# -*- coding: utf-8 -*-

import os
from codecs import open
from setuptools import setup, find_packages


here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.rst'), 'r', 'utf-8') as handle:
    readme = handle.read()

setup(
    name='sqlalchemy-filters',
    version='0.4.0',
    description='A library to filter SQLAlchemy queries.',
    long_description=readme,
    author='Student.com',
    author_email='wearehiring@student.com',
    url='https://github.com/Overseas-Student-Living/sqlalchemy-filters',
    packages=find_packages(exclude=['test', 'test.*']),
    install_requires=[
        'sqlalchemy>=1.0.16',
        'six>=1.10.0',
    ],
    extras_require={
        'dev': [
            'pytest==3.0.5',
            'flake8==3.2.1',
            'coverage==4.3.1',
            'sqlalchemy-utils==0.32.12',
        ],
        'mysql': [
            'mysql-connector-python==2.1.5',
        ]
    },
    dependency_links=[
        'https://cdn.mysql.com/Downloads/Connector-Python'
        '/mysql-connector-python-2.1.5.zip'
    ],
    zip_safe=True,
    license='Apache License, Version 2.0',
    classifiers=[
        "Programming Language :: Python",
        "Operating System :: POSIX",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
    ]
)
