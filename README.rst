SQLAlchemy-filters
==================

.. pull-quote::

    Filter, sort and paginate SQLAlchemy query objects.
    Ideal for exposing these actions over a REST API.

Filtering
---------

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

Pagination
----------

.. code-block:: python

    from sqlalchemy_filters import apply_pagination

    # `query` should be a SQLAlchemy query object

    query, pagination = apply_pagination(query, page_number=1, page_size=10)

    page_size, page_number, num_pages, total_results = pagination

    assert 10 == len(query)
    assert 10 == page_size == pagination.page_size
    assert 1 == page_number == pagination.page_number
    assert 3 == num_pages == pagination.num_pages
    assert 22 == total_results == pagination.total_results

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

These are the default configuration values, that can be
overridden when executing the Makefile targets:

.. code-block:: shell

    DB_USER = root
    DB_PASS =
    DB_SERVER = localhost
    DB_PORT = 3306
    DB_NAME = test_sqlalchemy_filters
    SQLITE_DB_FILE = /test_sqlalchemy_filters.db
    DB_DIALECT = sqlite
    DB_DRIVER = pysqlite

Example of usage:

.. code-block:: shell

    $ # using default settings (sqlite)
    $ make test
    $ make coverage

    $ # or overridding the database parameters
    $ DB_SERVER=192.168.99.100 DB_PORT=3340 DB_DIALECT=mysql DB_DRIVER=mysqlconnector make test
    $ DB_SERVER=192.168.99.100 DB_PORT=3340 DB_DIALECT=mysql DB_DRIVER=mysqlconnector make coverage


License
-------

Apache 2.0. See LICENSE for details.
