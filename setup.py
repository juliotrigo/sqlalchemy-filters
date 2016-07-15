# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='sqlalchemy-filters',
    version='0.1.0',
    description='A library to filter SQLAlchemy queries.',
    packages=find_packages(exclude=['test', 'test.*']),
    install_requires=[],
    extras_require={
        'dev': [
            'pytest==2.9.2',
            'flake8==2.6.0',
            'coverage==4.1.0',
            'mysql-connector-python==2.0.4',
            'sqlalchemy-utils==0.32.8',
        ]
    },
    zip_safe=True,
)
