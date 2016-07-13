SQLAlchemy-filters
==================

.. pull-quote::

    Filter, sort and paginate SQLALquemy query objects.
    Ideal for exposing these actions over a REST API.

Usage
-----

Assuming that we have a `Foo` model and a `session` object.

.. code-block:: python

    from sqlalchemy import Column, Integer, String
    from sqlalchemy.ext.declarative import declarative_base


    class Base(object):
        id = Column(Integer, primary_key=True)
        name = Column(String(50), nullable=False)
        count = Column(Integer, nullable=True)


    Base = declarative_base(cls=Base)


    class Foo(Base):

        __tablename__ = 'foo'


Then we can create a SQLAlchemy `query` object:

.. code-block:: python

    from sqlalchemy_filters import create_query


    query = create_query(session, Foo)

And we can filter this or any other SQLAlchemy query object multiple
times:

.. code-block:: python

    from sqlalchemy_filters import apply_filters

    # `query` should be a SQLAlchemy query object

    filters = [{'field': 'name', 'op': '==', 'value': 'name_1'}]
    filtered_query = apply_filters(query, filters)

    more_filters = [{'field': 'id', 'op': '==', 'value': 3}]
    filtered_query = apply_filters(filtered_query, more_filters)

    result = filtered_query.all()

Filters format
--------------

Filters must be provided in a list and will be applied sequentially.
Each filter will be a dictionary element in that list, using the
following format:

.. code-block:: python

    filters = [
        {'field': 'field_name', 'op': '==', 'value': 'field_value'},
        {'field': 'field_2_name', 'op': '==', 'value': 'field_2_value'},
        # ...
    ]

Where ``field`` is the name of the field that will be filtered with
``value``, using the operator provided in ``op``.

This is the list of operators that can be used:

- ``is_null``
- ``is_not_null``
- ``==``, ``eq``
- ``!=``, ``ne``
- ``>``, ``gt``
- ``<``, ``lt``
- ``>=``, ``ge``
- ``<=``, ``le``
- ``like``
- ``in``
- ``not_in``

Running tests
-------------

There are some Makefile targets that can be used to run the tests. A
test database will be created, used during the tests and destroyed
afterwards.

These are the default configuration values, that can be
overridden when executing the Makefile targets:

.. code-block:: Makefile

    DB_USER ?= root
    DB_PASS ?=
    DB_SERVER ?= localhost
    DB_PORT ?= 3306
    DB_NAME ?= test_sqlalchemy_filters
    DB_DIALECT ?= mysql
    DB_DRIVER ?= mysqlconnector

Example of usage:

.. code-block:: shell

    $ # using default values
    $ make test
    $ make coverage

    $ # or overridding some parameters
    $ make test DB_SERVER=192.168.99.100 DB_PORT=3340
    $ make coverage DB_SERVER=192.168.99.100 DB_PORT=3340

