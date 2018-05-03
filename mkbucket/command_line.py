import argparse
import json
import sys

import boto3
from botocore.exceptions import ClientError


USER_NAME_FORMAT = '{bucket_name}-s3-owner'
POLICY_NAME_FORMAT = '{bucket_name}-s3-owner-policy'


class BucketCreator:
    def __init__(self, profile_name=None, region_name=None):
        self.session = boto3.session.Session(profile_name=profile_name,
                                             region_name=region_name)
        self.s3 = self.session.resource('s3')
        self.iam = self.session.resource('iam')

    def get_current_user(self):
        return self.iam.CurrentUser()

    def get_current_account_alias(self):
        response = self.iam.meta.client.list_account_aliases()
        try:
            return response['AccountAliases'][0]
        except IndexError:
            return

    def create_bucket(self, name, acl=None):
        current_user = self.get_current_user()
        account_alias = self.get_current_account_alias()
        alias_msg = ''
        if account_alias:
            alias_msg = ' You account alias is "{}".'.format(account_alias)
        print('Signed in as {user_name}.{alias_info}'.format(user_name=current_user.arn, alias_info=alias_msg))
        region = self.session.region_name
        input_msg = 'Do you want to create bucket "{name}" in region ' \
                    '"{region}"? (Ctrl+C to cancel)\nType your bucket name ' \
                    'again to proceed:\n>>> '.format(name=name, region=region)
        if input(input_msg) != name:
            print()
            print('Incorrect')
            sys.exit(1)
        create_bucket_kwargs = {}
        create_bucket_config = {}
        # us-east-1 does not need to have location constraint
        # specified'
        if region != 'us-east-1':
            create_bucket_config['LocationConstraint'] = region
        if acl:
            create_bucket_kwargs['ACL'] = acl
        if create_bucket_config:
            create_bucket_kwargs['CreateBucketConfiguration'] = (
                create_bucket_config
            )
        bucket = self.s3.Bucket(name)
        # Because creating an existing bucket in US-East-1 won't
        # fail, we need to check whether it exists beforehand.
        try:
            self.s3.meta.client.head_bucket(Bucket=name)
        except ClientError as e:
            # Bucket does not exist, proceed with creation.
            if not e.response['Error']['Code'] == '404':
                sys.exit('Bucket seems to already exist... Aborting.')
        else:
            proceed = input(
                'This bucket seems to already exist on your account... '
                'Do you want to proceed with creating credentials for it? '
                '[y/N]: ')
            if proceed.lower() == 'y':
                return bucket
            print('Aborted by user.')
            sys.exit(1)
        if acl:
            print('Bucket\'s ACL is set to "{}".'.format(acl))
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

    def create_bucket_user(self, bucket, user_name=None):
        if user_name is None:
            user_name = USER_NAME_FORMAT.format(bucket_name=bucket.name)
        i = 0
        while True:
            tmp_user_name = user_name
            if i:
                tmp_user_name += str(i)
            try:
                user = self.iam.User(tmp_user_name).create()
                print('Created IAM user "{user_name}".'.format(
                    user_name=tmp_user_name
                ))
            except ClientError as e:
                if e.response['Error']['Code'] == 'EntityAlreadyExists':
                    i += 1
                    continue
            break
        self.iam.meta.client.get_waiter('user_exists').wait(UserName=user_name)
        return user

    def create_bucket_user_policy(self, bucket, user, policy_name=None):
        if policy_name is None:
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

    def enable_versioning(self, bucket):
        bucket.Versioning().enable()
        print('Enabled versioning for "{}".'.format(bucket.name))


def mkbucket():
    parser = argparse.ArgumentParser(description='Create S3 bucket with user.')
    parser.add_argument('bucket_name', type=str, metavar='bucket-name',
                        help='Name of the bucket you want to create.')
    parser.add_argument('--region', type=str,
                        help='In which region you want to host. It will use '
                             'your default region from the local session if '
                             'not specified.')
    parser.add_argument('--enable-versioning', action='store_true',
                        help='Enable file versioning. Please consider '
                             'using on production only.')
    parser.add_argument('--profile', type=str,
                        help='AWS CLI profile you want to use')
    parser.add_argument('--policy-name', type=str,
                        help='Will use "{}" if not '
                             'specified'.format(POLICY_NAME_FORMAT))
    parser.add_argument('--user-name', type=str,
                        help='Will use "{}" if not '
                             'specified'.format(USER_NAME_FORMAT))
    parser.add_argument('--bucket-acl', type=str)
    parser.add_argument(
        '--cors-origin', type=str, action='append',
        help='Domain you want to set CORS for. You can specify multiple '
             'domains, e.g. "--cors-origin http://domain.com '
             '--cors-origin http://domain2.com".'
    )
    args = parser.parse_args()
    creator = BucketCreator(profile_name=args.profile,
                            region_name=args.region)
    bucket = creator.create_bucket(args.bucket_name, acl=args.bucket_acl)
    if args.enable_versioning:
        creator.enable_versioning(bucket)
    user = creator.create_bucket_user(bucket, user_name=args.user_name)
    creator.create_user_access_key_pair(user)
    creator.create_bucket_user_policy(bucket, user,
                                      policy_name=args.policy_name)
    if args.cors_origin:
        creator.set_cors(bucket, args.cors_origin)


def main():
    try:
        mkbucket()
    except KeyboardInterrupt:
        print()
        print('Aborted by user.')
        sys.exit(130)
