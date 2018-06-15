import argparse
import sys

from .bucket_creator import BucketCreator
from .exceptions import (
    BucketNameAlreadyInUse, CredentialsNotFound, InvalidBucketName,
    InvalidUserName, UserNameTaken,
)

from .utils import CommandLineInterface


USER_NAME_FORMAT = '{bucket_name}-s3-owner'


class BuckupCommandLineInterface(CommandLineInterface):
    def __init__(self, boto3_profile=None, boto3_region=None):
        self.bucket_creator = BucketCreator(profile_name=boto3_profile,
                                            region_name=boto3_region)
        self.data = {}
        self.data['region'] = self.bucket_creator.session.region_name

    def print_welcome_information(self):
        print(
            ' _                _\n'
            '| |              | |\n'
            '| |__  _   _  ___| | ___   _ _ __\n'
            '| \'_ \| | | |/ __| |/ / | | | \'_ \\\n'
            '| |_) | |_| | (__|   <| |_| | |_) |\n'
            '|_.__/ \__,_|\___|_|\_\\__,_| .__/\n'
            '                            | |\n'
            '                            |_|\n'
        )
        print('Queries: http://github.com/torchbox/buckup\n')
        print('We are going to create an S3 bucket with a user that is ready '
              'to use. In the end\nyou will have a bucket name, access key '
              'and secret key.')

    def print_account_information(self):
        try:
            current_user = self.bucket_creator.get_current_user()
            account_alias = self.bucket_creator.get_current_account_alias()
        except CredentialsNotFound:
            print('Credentials not set. Please make sure you set your AWS '
                  'credentials.')
            print('You can use "aws configure" command or set them in '
                  'environment variables \n"AWS_ACCESS_KEY_ID" or '
                  '"AWS_SECRET_ACCESS_KEY".')
            print('If you already set AWS CLI credentials for another '
                  'profile, you can use\n"--profile" flag.')
            print('Read more: https://boto3.readthedocs.io/en/latest/guide/'
                  'configuration.html')
            print('Aborted due to error.')
            sys.exit(1)
        print('Signed in as {user_name}.'.format(
            user_name=current_user.arn,
        ))
        print('You account alias is "{}".'.format(account_alias))
        region = self.data['region']
        print('Use "--profile" flag to use different profile.')
        print('Region used is {region}. '
              'Use "--region" to specify different '
              'region.'.format(region=region))

    def ask_bucket_name(self):
        bucket_name = self.ask('Bucket name?')
        try:
            self.bucket_creator.validate_bucket_name(bucket_name)
        except BucketNameAlreadyInUse:
            print('Bucket name already in use...')
            return self.ask_bucket_name()
        except InvalidBucketName as e:
            print(e)
            return self.ask_bucket_name()
        else:
            self.data['bucket_name'] = bucket_name

    def ask_user_name(self):
        default_user_name = USER_NAME_FORMAT.format(
            bucket_name=self.data['bucket_name']
        )
        question = 'Username? [{}]'.format(default_user_name)
        user_name = self.ask(question)
        if not user_name:
            user_name = default_user_name

        try:
            self.bucket_creator.validate_user_name(user_name)
        except UserNameTaken:
            print('The username is already taken. Try a different one.')
            return self.ask_user_name()
        except InvalidUserName as e:
            print(str(e))
            return self.ask_user_name()
        else:
            self.data['user_name'] = user_name

    def ask_enable_versioning(self):
        versioning = self.ask_yes_no('Do you want to enable versioning?')
        self.data['enable_versioning'] = versioning

    def ask_summary(self):
        print('SUMMARY:')
        for key, value in self.data.items():
            print('\t{key}: {value}'.format(key=key, value=value))
        print()
        answer = self.ask_yes_no('Do you want to create a bucket with the '
                                 'above details?')
        if not answer:
            print('Cancelled.')
            sys.exit(130)
        return answer

    def ask_public_get_object(self):
        public_get_object = self.ask_yes_no(
            'Do you want to enable public s3:getObject on the whole bucket?\n'
            'That will enable everyone with the link to access the object. '
            'This is recommended\napproach if you do not want to set'
            'indidual objects as public in your\napplication.'
        )
        self.data['public_get_object'] = public_get_object

    def ask_cors(self):
        cors_origins = self.ask(
            'Specify a comma separated list of origins whitelisted for the '
            'CORS,\ne.g. "https://example.com" (not required)'
        ).strip().split(',')
        self.data['cors_origins'] = []
        for origin in cors_origins:
            origin = origin.strip()
            if origin:
                self.data['cors_origins'].append(origin)

    def create_bucket(self):
        self.bucket_creator.commit(self.data)
        print('\nBucket created. Please keep the above credentials secret as '
              'they grant owner\naccess to your bucket and files within it.')

    def print_separator(self):
        print()
        print('=' * 80)
        print()

    def execute(self):
        self.print_welcome_information()
        self.print_separator()
        self.print_account_information()
        self.print_separator()
        self.ask_bucket_name()
        self.ask_user_name()
        self.ask_enable_versioning()
        self.ask_public_get_object()
        self.ask_cors()
        self.print_separator()
        if self.ask_summary():
            self.print_separator()
            self.create_bucket()


def parse_args():
    parser = argparse.ArgumentParser(
        description='Create S3 bucket with user ready to use on your website.'
    )
    parser.add_argument('--profile', type=str,
                        help='AWS CLI profile you want to use')
    parser.add_argument('--region', type=str,
                        help='In which region you want to host. It will use '
                             'your default region from the local session if '
                             'not specified.')
    return parser.parse_args()


def main():
    try:
        args = parse_args()
        cli = BuckupCommandLineInterface(boto3_profile=args.profile,
                                         boto3_region=args.region)
        cli.execute()
    except KeyboardInterrupt:
        print()
        print('Aborted by user.')
        sys.exit(130)
