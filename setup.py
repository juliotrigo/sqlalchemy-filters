# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='sqlalchemy-filters',
    version='0.1.0',
    description='A library to filter SQLAlchemy queries.',
    author='Student.com',
    author_email='wearehiring@student.com',
    url='https://github.com/Overseas-Student-Living/sqlalchemy-filters',
    packages=find_packages(exclude=['test', 'test.*']),
    install_requires=[
        'sqlalchemy>=1.0.16',
    ],
    extras_require={
        'dev': [
            'pytest==3.0.5',
            'flake8==3.2.1',
            'coverage==4.2.0',
            'mysql-connector-python==2.1.5',
            'sqlalchemy-utils==0.32.12',
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
        "Operating System :: Linux",
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
