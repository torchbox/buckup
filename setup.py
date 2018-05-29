from setuptools import setup


setup(
    entry_points={
        'console_scripts': ['buckup=buckup.command_line:main'],
    },
)
