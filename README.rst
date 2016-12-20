SQLAlchemy-filters
==================

.. pull-quote::

    Filter, sort and paginate SQLAlchemy query objects.
    Ideal for exposing these actions over a REST API.

Usage
-----

Assuming that we have a SQLAlchemy `query` that only contains a single
model:

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

    # ...

    query = self.session.query(Foo)

Then we can apply filters to that ``query`` object (multiple times):

.. code-block:: python

    from sqlalchemy_filters import apply_filters

    # `query` should be a SQLAlchemy query object

    filters = [{'field': 'name', 'op': '==', 'value': 'name_1'}]
    filtered_query = apply_filters(query, filters)

    more_filters = [{'field': 'foo_id', 'op': 'is_not_null'}]
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
        {'field': 'field_2_name', 'op': '!=', 'value': 'field_2_value'},
        # ...
    ]

Where ``field`` is the name of the field that will be filtered using the
operator provided in ``op`` and (optionally, depending on the operator)
the provided ``value``.

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

The default configuration uses SQLite with the following test URI:

.. code-block:: shell

    sqlite+pysqlite:///test_sqlalchemy_filters.db

Example of usage:

.. code-block:: shell

    $ # using default settings
    $ make test
    $ make coverage

    $ # overriding DB parameters
    $ ARGS='--test-db-uri mysql+mysqlconnector://root:@192.168.99.100:3340/test_sqlalchemy_filters' make test
    $ ARGS='--test-db-uri mysql+mysqlconnector://root:@192.168.99.100:3340/test_sqlalchemy_filters' make coverage


License
-------

Apache 2.0. See LICENSE for details.
