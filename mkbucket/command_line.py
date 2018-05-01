import argparse
import json
import sys

import boto3


USER_NAME_FORMAT = '{bucket_name}-s3-owner'
POLICY_NAME_FORMAT = '{bucket_name}-s3-owner-policy'


class BucketCreator:
    def __init__(self, profile_name=None):
        self.s3 = boto3.resource('s3')
        self.iam = boto3.resource('iam')
        self.user_session = boto3.session.Session(profile_name=profile_name)

    def get_bucket(self, name, dont_check=False):
        bucket = self.s3.Bucket(name)
        if not dont_check:
            # This should raise "botocore.exceptions.ClientError" if
            # bucket does not exist.
            self.s3.meta.client.head_bucket(Bucket=name)
        return bucket

    def create_bucket(self, name, region=None):
        if region is None:
            region = self.user_session.region_name
        if region is None:
            print()
            sys.exit('You need to specify your region.')
        input_msg = 'Do you want to create bucket "{name}" in region ' \
                    '"{region}"? (Ctrl+C to cancel)\nType your bucket name ' \
                    'again to proceed:\n>>> '.format(name=name, region=region)
        if input(input_msg) != name:
            print()
            sys.exit('Incorrect.')
        response = self.s3.Bucket(name).create(
            CreateBucketConfiguration={
                'LocationConstraint': region
            },
        )
        msg = 'Created bucket "{bucket_name}" at "{bucket_location}" in ' \
              'region "{region}".'
        print(msg.format(
            bucket_name=name,
            bucket_location=response['Location'],
            region=region,
        ))
        print()
        print('\tAWS_S3_BUCKET_NAME', name)
        print()
        return self.get_bucket(name)

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
        user = self.iam.User(user_name).create()
        print('Created IAM user "{user_name}".'.format(user_name=user_name))
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
    parser.add_argument('--policy-name', type=str,
                        help='Will use "{}" if not '
                             'specified'.format(POLICY_NAME_FORMAT))
    parser.add_argument('--user-name', type=str,
                        help='Will use "{}" if not '
                             'specified'.format(USER_NAME_FORMAT))
    parser.add_argument(
        '--cors-origin', type=str, action='append',
        help='Domain you want to set CORS for. You can specify multiple '
             'domains, e.g. "--cors-origin http://domain.com '
             '--cors-origin http://domain2.com".'
    )
    args = parser.parse_args()
    creator = BucketCreator()
    bucket = creator.create_bucket(args.bucket_name, region=args.region)
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
        sys.exit('Aborted by user.')
