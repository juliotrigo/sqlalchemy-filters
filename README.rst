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

Note that we can also apply filters to queries defined by fields or functions:

.. code-block:: python

    query_alt_1 = self.session.query(Foo.id, Foo.name)
    query_alt_2 = self.session.query(func.count(Foo.id))


Sort
----

.. code-block:: python

    from sqlalchemy_filters import apply_sort

    # `query` should be a SQLAlchemy query object

    order_by = [
        {'field': 'name', 'direction': 'asc'},
        {'field': 'id', 'direction': 'desc'},
    ]
    sorted_query = apply_sort(query, order_by)

    result = sorted_query.all()


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

Optionally, if there is only one filter, the containing list may be omitted:

.. code-block:: python

    filters = {'field': 'field_name', 'op': '==', 'value': 'field_value'}

Where ``field`` is the name of the field that will be filtered using the
operator provided in ``op`` (optional, defaults to `==`) and the
provided ``value`` (optional, depending on the operator).

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

Boolean Functions
*****************
``and``, ``or``, and ``not`` functions can be used and nested within the filter definition:

.. code-block:: python

    filters = [
        {
            'or': [
                {
                    'and': [
                        {'field': 'field_name', 'op': '==', 'value': 'field_value'},
                        {'field': 'field_2_name', 'op': '!=', 'value': 'field_2_value'},
                    ]
                },
                {
                    'not': [
                        {'field': 'field_3_name', 'op': '==', 'value': 'field_3_value'}
                    ]
                },
            ],
        }
    ]


Note: ``or`` and ``and`` must reference a list of at least one element. ``not`` must reference a list of exactly one element.

Sort format
-----------

Sort elements must be provided as dictionaries in a list and will be
applied sequentially:

.. code-block:: python

    order_by = [
        {'field': 'name', 'direction': 'asc'},
        {'field': 'id', 'direction': 'desc'},
        # ...
    ]

Where ``field`` is the name of the field that will be sorted using the
provided ``direction``.

Running tests
-------------

There are some Makefile targets that can be used to run the tests. A
test database will be created, used during the tests and destroyed
afterwards.

The default configuration uses both SQLite and MySQL (if the driver is
installed) to run the tests, with the following URIs:

.. code-block:: shell

    sqlite+pysqlite:///test_sqlalchemy_filters.db
    mysql+mysqlconnector://root:@localhost:3306/test_sqlalchemy_filters

Example of usage:

.. code-block:: shell

    $ # using default settings
    $ make test
    $ make coverage

    $ # overriding DB parameters
    $ ARGS='--mysql-test-db-uri mysql+mysqlconnector://root:@192.168.99.100:3340/test_sqlalchemy_filters' make test
    $ ARGS='--sqlite-test-db-uri sqlite+pysqlite:///test_sqlalchemy_filters.db' make test

    $ ARGS='--mysql-test-db-uri mysql+mysqlconnector://root:@192.168.99.100:3340/test_sqlalchemy_filters' make coverage
    $ ARGS='--sqlite-test-db-uri sqlite+pysqlite:///test_sqlalchemy_filters.db' make coverage


License
-------

Apache 2.0. See LICENSE for details.
