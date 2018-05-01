# mkbucket
Create S3 bucket, policy and user with one command. Ready to use on your
project.

## Features
- Create bucket
- Enable versioning
- Set CORS
- Create user and generate access key pair.
- Give that user permissions to the created bucket.

## Installation
Install with `setup.py` or just execute with `run.py` without installing.

## Usage
To create a bucket with all the defaults, please just use.
```bash
mkbucket [bucket-name]
```
E.g.
```bash
mkbucket torchbox-production
```
### CORS
You can specify [CORS](https://docs.aws.amazon.com/AmazonS3/latest/dev/cors.html)
origin so a web browser won't block loading static assets.
```bash
mkbucket torchbox-production \
    --cors-origin https://torchbox.com \
    --cors-origin http://torchbox.com
```
### Versioning
You can also enable [versioning](https://docs.aws.amazon.com/AmazonS3/latest/dev/Versioning.html).
Please consider switching it only for the production site since it incurs
additional costs.
```bash
mkbucket torchbox-production --enable-versioning
```

### Custom region
By default the script will use region from your session. You can specify a
custom one with the `--region` flag.
```bash
mkbucket torchbox-production --region eu-west-2
```

### Custom IAM user or policy name
For whatever reason you may want to use custom policy or user name.
```bash
mkbucket torchbox-production --policy-name custom-policy-name --user-name custom-user-name
```
Default ones are `{bucket_name}-s3-owner` and `{bucket_name}-s3-owner-policy`.

