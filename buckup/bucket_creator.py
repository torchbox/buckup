import json

import boto3
from botocore.exceptions import (
    ClientError, NoCredentialsError, ParamValidationError
)

from .exceptions import (
    BucketNameAlreadyInUse, CredentialsNotFound, InvalidBucketName,
    InvalidUserName, UserNameTaken
)


POLICY_NAME_FORMAT = '{bucket_name}-owner-policy'


class BucketCreator:
    def __init__(self, profile_name=None, region_name=None):
        self.session = boto3.session.Session(profile_name=profile_name,
                                             region_name=region_name)
        self.s3 = self.session.resource('s3')
        self.iam = self.session.resource('iam')

    def commit(self, data):
        bucket = self.create_bucket(data['bucket_name'], data['region'])
        self.create_user(bucket, data['user_name'])
        if data.get('public_get_object_paths'):
            self.set_public_get_object_policy_on_paths(
                bucket,
                data['public_get_object_paths']
            )
        if data.get('cors_origins'):
            self.set_cors(bucket, data['cors_origins'])
        if data.get('enable_versioning'):
            self.enable_versioning(bucket)

    def set_public_get_object_policy_on_paths(self, bucket, paths):
        """
        Allow everyone to s3:GetObject on any file in the bucket.

        I.e. Anyone with the link to the file can open it without permission.
        """
        def format_path(path):
            if path.startswith('/'):
                path = path[1:]
            return "arn:aws:s3:::{bucket_name}/{path}".format(
                bucket_name=bucket.name,
                path=path,
            )

        resources = []
        for path in paths:
            resources.append(format_path(path))

        policy = json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Sid": "PublicGetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": ["s3:GetObject"],
                "Resource": resources,
            }],
        })
        bucket.Policy().put(Policy=policy)
        print('Allowed public to perform s3:GetObject on any object inside '
              'the bucket on resources:\n\t{}'.format(resources))

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
        print('Created IAM user "{user_name}".'.format(
            user_name=user_name
        ))
        self.iam.meta.client.get_waiter('user_exists').wait(UserName=user_name)
        self.attach_bucket_user_policy(bucket, user)
        self.create_user_access_key_pair(user)
        return user

    def create_user_access_key_pair(self, user):
        access_key_pair = user.create_access_key_pair()
        print('Created access key pair for user "{user_name}".'.format(
            user_name=user.user_name,
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

    def attach_bucket_user_policy(self, bucket, user):
        policy_name = POLICY_NAME_FORMAT.format(bucket_name=bucket.name)
        user.create_policy(
            PolicyName=policy_name,
            PolicyDocument=json.dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "AllowFullBucketAccess",
                        "Effect": "Allow",
                        "Action": ["s3:*"],
                        "Resource": [
                            "arn:aws:s3:::{bucket_name}".format(
                                bucket_name=bucket.name
                            ),
                            "arn:aws:s3:::{bucket_name}/*".format(
                                bucket_name=bucket.name
                            ),
                        ]
                    }
                ]
            }),
        )
        msg = 'Attached policy "{policy_name}" to user "{user_name}".'
        print(msg.format(policy_name=policy_name, user_name=user.user_name))

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
        return self.iam.CurrentUser()

    def get_current_account_alias(self):
        try:
            response = self.iam.meta.client.list_account_aliases()
        except NoCredentialsError as e:
            raise CredentialsNotFound from e
        try:
            return response['AccountAliases'][0]
        except IndexError:
            return
