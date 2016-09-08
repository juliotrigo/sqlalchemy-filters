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
        'sqlalchemy>=1.0.14',
    ],
    extras_require={
        'dev': [
            'pytest==2.9.2',
            'flake8==3.0.1',
            'coverage==4.2.0',
            'mysql-connector-python==2.0.4',
            'sqlalchemy-utils==0.32.9',
        ]
    },
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
