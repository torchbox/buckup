import json
import time

import boto3
from botocore.exceptions import (
    ClientError, NoCredentialsError, ParamValidationError
)

from .exceptions import (
    BucketNameAlreadyInUse, CannotGetCurrentUser, CannotListAccountAliases,
    CredentialsNotFound, InvalidBucketName, InvalidUserName, UserNameTaken
)


POLICY_NAME_FORMAT = '{bucket_name}-owner-policy'


class BucketCreator:
    def __init__(self, profile_name=None, region_name=None):
        self.session = boto3.session.Session(profile_name=profile_name,
                                             region_name=region_name)
        self.s3 = self.session.resource('s3')
        self.s3_client = self.session.client('s3')
        self.iam = self.session.resource('iam')

    def commit(self, data):
        bucket = self.create_bucket(data['bucket_name'], data['region'])
        user = self.create_user(bucket, data['user_name'])
        self.set_bucket_policy(
            bucket,
            user,
            allow_public_acls=data["allow_public_acls"],
            public_get_object_paths=data.get('public_get_object_paths')
        )
        if data.get('cors_origins'):
            self.set_cors(bucket, data['cors_origins'])
        if data.get('enable_versioning'):
            self.enable_versioning(bucket)

    def get_bucket_policy_statement_for_get_object(self, bucket,
                                                   public_get_object_paths):
        """
        Create policy statement to enable the public to perform s3:getObject
        on specified paths.
        """
        if public_get_object_paths:
            def format_path(path):
                if path.startswith('/'):
                    path = path[1:]
                return "arn:aws:s3:::{bucket_name}/{path}".format(
                    bucket_name=bucket.name,
                    path=path,
                )
            paths_resources = []
            for path in public_get_object_paths:
                paths_resources.append(format_path(path))
            return {
                "Sid": "PublicGetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": ["s3:GetObject"],
                "Resource": paths_resources,
            }

    def get_bucket_policy_statements_for_user_access(self, bucket, user):
        # Create policy statement giving the created user access to
        # non-destructive actions on the bucket.
        yield {
            "Sid": "AllowUserManageBucket",
            "Effect": "Allow",
            "Principal": {
                "AWS": user.arn
            },
            "Action": [
                "s3:ListBucket",
                "s3:GetBucketLocation",
                "s3:ListBucketMultipartUploads",
                "s3:ListBucketVersions"
            ],
            "Resource": "arn:aws:s3:::{bucket_name}".format(
                bucket_name=bucket.name
            )
        }
        # Create policy statement giving the created user full access over the
        # objects.
        yield {
            "Sid": "AllowUserManageBucketObjects",
            "Effect": "Allow",
            "Principal": {
                "AWS": user.arn
            },
            "Action": "s3:*",
            "Resource": "arn:aws:s3:::{bucket_name}/*".format(
                bucket_name=bucket.name
            )
        }

    def set_bucket_policy(self, bucket, user, allow_public_acls, public_get_object_paths=None):
        policy_statement = []
        public_access = bool(public_get_object_paths)

        if public_access:
            policy_statement.append(
                self.get_bucket_policy_statement_for_get_object(
                    bucket, public_get_object_paths
                )
            )
        policy_statement.extend(list(
            self.get_bucket_policy_statements_for_user_access(bucket, user)
        ))
        policy = json.dumps({
            "Version": "2012-10-17",
            "Statement": policy_statement,
        })
        while True:
            try:
                bucket.Policy().put(Policy=policy)
            except ClientError as e:
                if e.response['Error']['Code'] == 'MalformedPolicy':
                    print('Waiting for the user to be available to be '
                          'attached to the policy (wait 5s).')
                    time.sleep(5)
                    continue
                raise e
            else:
                break
        print('Bucket policy set.')

        # NB: This API doesn't exist on a `Bucket`
        self.s3_client.put_public_access_block(
            Bucket=bucket.name,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": not allow_public_acls,
                "IgnorePublicAcls": not allow_public_acls,
                "BlockPublicPolicy": not public_access,
                "RestrictPublicBuckets": not public_access
            }
        )

        if public_access or allow_public_acls:
            print('Configured public access to bucket.')

    def create_bucket(self, name, region):
        """
        Create bucket of name in the given region.
        """
        create_bucket_kwargs = {}
        create_bucket_config = {}
        # us-east-1 does not work with location specified.
        if region != 'us-east-1':
            create_bucket_config['LocationConstraint'] = region
        if create_bucket_config:
            create_bucket_kwargs['CreateBucketConfiguration'] = (
                create_bucket_config
            )
        bucket = self.s3.Bucket(name)
        response = bucket.create(**create_bucket_kwargs)
        msg = 'Created bucket "{bucket_name}" at "{bucket_location}" in ' \
              'region "{region}".'
        print(msg.format(
            bucket_name=name,
            bucket_location=response['Location'],
            region=region,
        ))
        print()
        print('\tAWS_STORAGE_BUCKET_NAME', name)
        print()
        bucket.wait_until_exists()
        return bucket

    def enable_versioning(self, bucket):
        bucket.Versioning().enable()
        print('Enabled versioning for "{}".'.format(bucket.name))

    def create_user(self, bucket, user_name):
        user = self.iam.User(user_name).create()
        self.iam.meta.client.get_waiter('user_exists').wait(UserName=user_name)
        user.load()
        print('Created IAM user "{user_name}".'.format(
            user_name=user.arn
        ))
        self.create_user_access_key_pair(user)
        return user

    def create_user_access_key_pair(self, user):
        access_key_pair = user.create_access_key_pair()
        print('Created access key pair for user "{user}".'.format(
            user=user.arn,
        ))
        print()
        print('\tAWS_ACCESS_KEY_ID', access_key_pair.access_key_id)
        print('\tAWS_SECRET_ACCESS_KEY', access_key_pair.secret_access_key)
        print()
        return access_key_pair

    def set_cors(self, bucket, origins):
        try:
            # Validates that the origins is an iterable and is
            # not empty.
            next(iter(origins))
        except StopIteration:
            raise ValueError("'origins' cannot be empty.")
        config = {
            'CORSRules': [
                {
                    'AllowedMethods': ['GET'],
                    'AllowedOrigins': origins,
                    'MaxAgeSeconds': 3000,
                    'AllowedHeaders': ['Authorization'],
                }
            ]
        }
        msg = "Set CORS for domains {domains} to bucket \"{bucket_name}\"."
        print(msg.format(domains=', '.join(origins), bucket_name=bucket.name))
        bucket.Cors().put(CORSConfiguration=config)

    def validate_bucket_name(self, bucket_name):
        try:
            self.s3.meta.client.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            # Bucket does not exist, proceed with creation.
            if e.response['Error']['Code'] == '404':
                return
            # No access to the bucket means that it already exists but we
            # cannot run head request on it.
            elif e.response['Error']['Code'] == '403':
                raise BucketNameAlreadyInUse
            else:
                raise e
        except ParamValidationError as e:
            raise InvalidBucketName(str(e)) from e
        else:
            raise BucketNameAlreadyInUse

    def validate_user_name(self, user_name):
        try:
            self.iam.User(user_name).load()
        except ClientError as e:
            if e.response['Error']['Code'] == 'ValidationError':
                raise InvalidUserName(str(e)) from e
            if not e.response['Error']['Code'] == 'EntityAlreadyExists':
                return
            raise e
        else:
            raise UserNameTaken

    def get_current_user(self):
        try:
            user = self.iam.CurrentUser()
            user.load()
            return user
        except NoCredentialsError as e:
            raise CredentialsNotFound from e
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                raise CannotGetCurrentUser from e
            raise e

    def get_current_account_alias(self):
        try:
            response = self.iam.meta.client.list_account_aliases()
        except NoCredentialsError as e:
            raise CredentialsNotFound from e
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                raise CannotListAccountAliases from e
            raise e
        try:
            return response['AccountAliases'][0]
        except IndexError:
            return
