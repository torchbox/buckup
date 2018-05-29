buckup
========

Create S3 bucket, policy and user with one command. Ready to use on your
project.

Features
--------

-  Create bucket
-  Enable versioning
-  Set CORS
-  Create user and generate access key pair.
-  Give that user permissions to the created bucket.

Installation
------------

Install with ``setup.py`` or just execute with ``run.py`` without
installing.

Usage
-----

To create a bucket with all the defaults, please just use.

.. code:: sh

   buckup [bucket-name]

E.g.

.. code:: sh

   buckup torchbox-production

CORS
~~~~

You can specify `CORS`_ origin so a web browser won’t block loading
static assets.

.. code:: sh

   buckup torchbox-production \
       --cors-origin https://torchbox.com \
       --cors-origin http://torchbox.com

Versioning
~~~~~~~~~~

You can also enable `versioning`_. Please consider switching it only for
the production site since it incurs additional costs.

.. code:: sh

   buckup torchbox-production --enable-versioning

Custom region
~~~~~~~~~~~~~

By default the script will use region from your session. You can specify
a custom one with the ``--region`` flag.

.. code:: sh

   buckup torchbox-production --region eu-west-2

Custom IAM user or policy name
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For whatever reason you may want to use custom policy or user name.

.. code:: sh

   buckup torchbox-production --policy-name custom-policy-name --user-name custom-user-name

Default ones are ``{bucket_name}-s3-owner`` and
``{bucket_name}-s3-owner-policy``.

.. _CORS: https://docs.aws.amazon.com/AmazonS3/latest/dev/cors.html
.. _versioning: https://docs.aws.amazon.com/AmazonS3/latest/dev/Versioning.html

