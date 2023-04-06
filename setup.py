# -*- coding: utf-8 -*-

import os
from codecs import open
from setuptools import setup, find_packages


here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.rst'), 'r', 'utf-8') as handle:
    readme = handle.read()

setup(
    name='sqlalchemy-filters',
    version='0.12.0',
    description='A library to filter SQLAlchemy queries.',
    long_description=readme,
    long_description_content_type='text/x-rst',
    author='Student.com',
    author_email='wearehiring@student.com',
    url='https://github.com/juliotrigo/sqlalchemy-filters',
    packages=find_packages(exclude=['test', 'test.*']),
    install_requires=['sqlalchemy>=1.0.16', 'six>=1.10.0'],
    extras_require={
        'dev': [
            'pytest>=4.6.9',
            'coverage~=5.0.4',
            # for sqlalchemy1.4 >= 0.37 is required
            'sqlalchemy-utils>=0.36.3',
            'flake8',
            'restructuredtext-lint',
            'Pygments',
        ],
        'mysql': ['mysql-connector-python-rf==2.2.2'],
        'postgresql': ['psycopg2==2.8.4'],
        'python2': ['funcsigs>=1.0.2'],
    },
    zip_safe=True,
    license='Apache License, Version 2.0',
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Database",
        "Topic :: Database :: Front-Ends",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]
)
