.. image:: https://raw.githubusercontent.com/torchbox/buckup/master/logo.png
   :alt: Buckup logo

buckup
========

Create S3 bucket, policy and user with one command. After creation it is ready
to use on your project.


Features
--------

-  Create bucket
-  Enable `versioning <https://docs.aws.amazon.com/AmazonS3/latest/dev/Versioning.html>`_
-  Set `CORS <https://docs.aws.amazon.com/AmazonS3/latest/dev/cors.html>`_
-  Create user and generate access key pair and give it permissions to the
   bucket.
-  Set policy to enable
   `s3:GetObject <https://docs.aws.amazon.com/AmazonS3/latest/API/RESTObjectGET.html>`_
   permission on every object in your bucket to the public.

Dependencies
------------

* Python 3
* `boto3 <https://pypi.org/project/boto3/>`_

Installation
------------

PyPI (pip)
~~~~~~~~~~

.. code:: sh

   python3 -m pip install buckup

Arch User Repository
~~~~~~~~~~~~~~~~~~~~

Buckup `can be found on AUR <https://aur.archlinux.org/packages/buckup>`_.

.. code:: sh

   cd /tmp
   git clone https://aur.archlinux.org/buckup.git
   cd buckup
   makepkg -si

Homebrew
~~~~~~~~

Buckup can be installed from Torchbox's `Homebrew tap <https://github.com/torchbox/homebrew-tap>`_.

.. code:: sh

   brew tap torchbox/tap
   brew install buckup

Development build
~~~~~~~~~~~~~~~~~

You can easily install buckup inside a virtual environment and work on it
there, e.g.

.. code:: sh

   git clone git@github.com:torchbox/buckup.git
   cd buckup
   python3 -m venv venv
   source venv/bin/activate
   pip install -e .
   buckup


Usage
-----

1. First you need an AWS account. You need programmatic access key to use it
   with buckup.

   * If you have `AWS CLI <https://aws.amazon.com/cli/>`_ installed,
     you can save your credentials with
     `aws configure <https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html>`_; or
   * you can set  ``AWS_ACCESS_KEY_ID`` and ``AWS_SECRET_ACCESS_KEY``
     environment variable containing your credentials.

   Read
   `boto3 documentation <https://boto3.readthedocs.io/en/latest/guide/configuration.html>`_
   for more detail.

   1. If you want to restrict your access only to essential credentials to use
      buckup, please set them to:

      * ``iam:ListAccountAliases`` (not required to use)
      * ``s3:PutBucketPolicy``
      * ``s3:CreateBucket``
      * ``iam:GetUser``
      * ``iam:CreateUser``
      * ``s3:PutBucketCORS``
      * ``s3:PutBucketVersioning``
      * ``iam:CreateAccessKey``

2. After you set that up, you can type ``buckup`` and that should open the
   prompt.

   1. If you want to specify other than the default region, please use ``--region``
      flag with ``buckup``, e.g. ``buckup --region eu-west-2``.

3. After you answer all the questions you should obtain your bucket details
   that are ready to use in your application.

.. image:: https://raw.githubusercontent.com/torchbox/buckup/master/screenshot.png
   :alt: Screenshot of buckup’s command line output, showing the creation of a test bucket
