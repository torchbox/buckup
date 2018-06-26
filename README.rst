.. image:: logo.png
   :alt: Buckup logo

buckup
========

Create S3 bucket, policy and user with one command. After creation it is ready
to use on your project.

Features
--------

-  Create bucket
-  Enable versioning
-  Set CORS
-  Create user and generate access key pair and give it permissions to the
   bucket.
-  Set policy to enable
   `s3:GetObject <https://docs.aws.amazon.com/AmazonS3/latest/API/RESTObjectGET.html>`_
   permission on every object in your bucket to the public.

Installation
------------

.. code:: sh

   pip install buckup

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

To create a bucket just type ``buckup`` in the command line.

If you want to use other AWS CLI profile use ``--profile`` flag. You can always
pass your credentials using ``AWS_ACCESS_KEY_ID`` and ``AWS_ACCESS_SECRET_KEY``
environment variables or other methods described in the
`boto3 documentation <https://boto3.readthedocs.io/en/latest/guide/configuration.html>`_.

If you want to specify another region use ``--region`` flag.
