from setuptools import setup


setup(
    name='mkbucket',
    packages=['mkbucket'],
    description='Create S3 bucket and user easily',
    url='https://git.torchbox.com/tomasz.knapik/mkbucket',
    version='0.1',
    license='BSD-2',
    author='Tomasz Knapik',
    author_email='tomasz.knapik@torchbox.com',
    entry_points={
        'console_scripts': ['mkbucket=mkbucket.command_line:main'],
    },
    install_requires=[
        'boto3==1.7.11',
    ],
)
