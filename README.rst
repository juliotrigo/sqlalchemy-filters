SQLAlchemy filters
==================

.. pull-quote::

    Filter, sort and paginate SQLAlchemy query objects. Ideal for
    exposing these actions over a REST API.


.. image:: https://img.shields.io/pypi/v/sqlalchemy-filters.svg
    :target: https://pypi.org/project/sqlalchemy-filters/

.. image:: https://img.shields.io/pypi/pyversions/sqlalchemy-filters.svg
    :target: https://pypi.org/project/sqlalchemy-filters/

.. image:: https://img.shields.io/pypi/format/sqlalchemy-filters.svg
    :target: https://pypi.org/project/sqlalchemy-filters/

.. image:: https://travis-ci.org/juliotrigo/sqlalchemy-filters.svg?branch=master
    :target: https://travis-ci.org/juliotrigo/sqlalchemy-filters


Filtering
---------

Assuming that we have a SQLAlchemy_ ``query`` object:

.. code-block:: python

    from sqlalchemy import Column, Integer, String
    from sqlalchemy.ext.declarative import declarative_base


    class Base(object):
        id = Column(Integer, primary_key=True)
        name = Column(String(50), nullable=False)
        count = Column(Integer, nullable=True)

        @hybrid_property
        def count_square(self):
            return self.count * self.count

        @hybrid_method
        def three_times_count(self):
            return self.count * 3


    Base = declarative_base(cls=Base)


    class Foo(Base):

        __tablename__ = 'foo'

    # ...

    query = session.query(Foo)

Then we can apply filters to that ``query`` object (multiple times):

.. code-block:: python

    from sqlalchemy_filters import apply_filters


    # `query` should be a SQLAlchemy query object

    filter_spec = [{'field': 'name', 'op': '==', 'value': 'name_1'}]
    filtered_query = apply_filters(query, filter_spec)

    more_filters = [{'field': 'foo_id', 'op': 'is_not_null'}]
    filtered_query = apply_filters(filtered_query, more_filters)

    result = filtered_query.all()

It is also possible to filter queries that contain multiple models,
including joins:

.. code-block:: python

    class Bar(Base):

        __tablename__ = 'bar'

        foo_id = Column(Integer, ForeignKey('foo.id'))


.. code-block:: python

    query = session.query(Foo).join(Bar)

    filter_spec = [
        {'model': 'Foo', field': 'name', 'op': '==', 'value': 'name_1'},
        {'model': 'Bar', field': 'count', 'op': '>=', 'value': 5},
    ]
    filtered_query = apply_filters(query, filter_spec)

    result = filtered_query.all()


``apply_filters`` will attempt to automatically join models to ``query``
if they're not already present and a model-specific filter is supplied.
For example, the value of ``filtered_query`` in the following two code
blocks is identical:

.. code-block:: python

    query = session.query(Foo).join(Bar)  # join pre-applied to query

    filter_spec = [
        {'model': 'Foo', field': 'name', 'op': '==', 'value': 'name_1'},
        {'model': 'Bar', field': 'count', 'op': '>=', 'value': 5},
    ]
    filtered_query = apply_filters(query, filter_spec)

.. code-block:: python

    query = session.query(Foo)  # join to Bar will be automatically applied

    filter_spec = [
        {field': 'name', 'op': '==', 'value': 'name_1'},
        {'model': 'Bar', field': 'count', 'op': '>=', 'value': 5},
    ]
    filtered_query = apply_filters(query, filter_spec)

The automatic join is only possible if SQLAlchemy_ can implictly
determine the condition for the join, for example because of a foreign
key relationship.

Automatic joins allow flexibility for clients to filter and sort by related
objects without specifying all possible joins on the server beforehand. Feature
can be explicitly disabled by passing ``do_auto_join=False`` argument to the
``apply_filters`` call.

Note that first filter of the second block does not specify a model.
It is implictly applied to the ``Foo`` model because that is the only
model in the original query passed to ``apply_filters``.

It is also possible to apply filters to queries defined by fields, functions or
``select_from`` clause:

.. code-block:: python

    query_alt_1 = session.query(Foo.id, Foo.name)
    query_alt_2 = session.query(func.count(Foo.id))
    query_alt_3 = session.query().select_from(Foo).add_column(Foo.id)

Hybrid attributes
^^^^^^^^^^^^^^^^^

You can filter by a `hybrid attribute`_: a `hybrid property`_ or a `hybrid method`_.

.. code-block:: python

    query = session.query(Foo)

    filter_spec = [{'field': 'count_square', 'op': '>=', 'value': 25}]
    filter_spec = [{'field': 'three_times_count', 'op': '>=', 'value': 15}]

    filtered_query = apply_filters(query, filter_spec)
    result = filtered_query.all()


Restricted Loads
----------------

You can restrict the fields that SQLAlchemy_ loads from the database by
using the ``apply_loads`` function:

.. code-block:: python

    query = session.query(Foo, Bar).join(Bar)
    load_spec = [
        {'model': 'Foo', 'fields': ['name']},
        {'model': 'Bar', 'fields': ['count']}
    ]
    query = apply_loads(query, load_spec)  # will load only Foo.name and Bar.count


The effect of the ``apply_loads`` function is to ``_defer_`` the load
of any other fields to when/if they're accessed, rather than loading
them when the query is executed. It only applies to fields that would be
loaded during normal query execution.


Effect on joined queries
^^^^^^^^^^^^^^^^^^^^^^^^

The default SQLAlchemy_ join is lazy, meaning that columns from the
joined table are loaded only when required. Therefore ``apply_loads``
has limited effect in the following scenario:

.. code-block:: python

    query = session.query(Foo).join(Bar)
    load_spec = [
        {'model': 'Foo', 'fields': ['name']}
        {'model': 'Bar', 'fields': ['count']}  # ignored
    ]
    query = apply_loads(query, load_spec)  # will load only Foo.name


``apply_loads`` cannot be applied to columns that are loaded as
`joined eager loads <http://docs.sqlalchemy.org/en/latest/orm/loading_relationships.html#joined-eager-loading>`_.
This is because a joined eager load does not add the joined model to the
original query, as explained
`here <http://docs.sqlalchemy.org/en/latest/orm/loading_relationships.html#the-zen-of-joined-eager-loading>`_

The following would not prevent all columns from ``Bar`` being eagerly
loaded:

.. code-block:: python

    query = session.query(Foo).options(joinedload(Foo.bar))
    load_spec = [
        {'model': 'Foo', 'fields': ['name']}
        {'model': 'Bar', 'fields': ['count']}
    ]
    query = apply_loads(query, load_spec)

.. sidebar:: Automatic Join

    In fact, what happens here is that ``Bar`` is automatically joined
    to ``query``, because it is determined that ``Bar`` is not part of
    the original query. The ``load_spec`` therefore has no effect
    because the automatic join results in lazy evaluation.

If you wish to perform a joined load with restricted columns, you must
specify the columns as part of the joined load, rather than with
``apply_loads``:

.. code-block:: python

    query = session.query(Foo).options(joinedload(Bar).load_only('count'))
    load_spec = [
        {'model': 'Foo', 'fields': ['name']}
    ]
    query = apply_loads(query. load_spec)  # will load ony Foo.name and Bar.count


Sort
----

.. code-block:: python

    from sqlalchemy_filters import apply_sort


    # `query` should be a SQLAlchemy query object

    sort_spec = [
        {'model': 'Foo', field': 'name', 'direction': 'asc'},
        {'model': 'Bar', field': 'id', 'direction': 'desc'},
    ]
    sorted_query = apply_sort(query, sort_spec)

    result = sorted_query.all()


``apply_sort`` will attempt to automatically join models to ``query`` if
they're not already present and a model-specific sort is supplied.
The behaviour is the same as in ``apply_filters``.

This allows flexibility for clients to sort by fields on related objects
without specifying all possible joins on the server beforehand.

Hybrid attributes
^^^^^^^^^^^^^^^^^

You can sort by a `hybrid attribute`_: a `hybrid property`_ or a `hybrid method`_.


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

    filter_spec = [
        {'model': 'model_name', 'field': 'field_name', 'op': '==', 'value': 'field_value'},
        {'model': 'model_name', 'field': 'field_2_name', 'op': '!=', 'value': 'field_2_value'},
        # ...
    ]

The ``model`` key is optional if the original query being filtered only
applies to one model.

If there is only one filter, the containing list may be omitted:

.. code-block:: python

    filter_spec = {'field': 'field_name', 'op': '==', 'value': 'field_value'}

Where ``field`` is the name of the field that will be filtered using the
operator provided in ``op`` (optional, defaults to ``==``) and the
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
- ``ilike``
- ``not_ilike``
- ``in``
- ``not_in``
- ``any``
- ``not_any``

any / not_any
^^^^^^^^^^^^^

PostgreSQL specific operators allow to filter queries on columns of type ``ARRAY``.
Use ``any`` to filter if a value is present in an array and ``not_any`` if it's not.

Boolean Functions
^^^^^^^^^^^^^^^^^
``and``, ``or``, and ``not`` functions can be used and nested within the
filter specification:

.. code-block:: python

    filter_spec = [
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


Note: ``or`` and ``and`` must reference a list of at least one element.
``not`` must reference a list of exactly one element.

Sort format
-----------

Sort elements must be provided as dictionaries in a list and will be
applied sequentially:

.. code-block:: python

    sort_spec = [
        {'model': 'Foo', 'field': 'name', 'direction': 'asc'},
        {'model': 'Bar', 'field': 'id', 'direction': 'desc'},
        # ...
    ]

Where ``field`` is the name of the field that will be sorted using the
provided ``direction``.

The ``model`` key is optional if the original query being sorted only
applies to one model.

nullsfirst / nullslast
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    sort_spec = [
        {'model': 'Baz', 'field': 'count', 'direction': 'asc', 'nullsfirst': True},
        {'model': 'Qux', 'field': 'city', 'direction': 'desc', 'nullslast': True},
        # ...
    ]

``nullsfirst`` is an optional attribute that will place ``NULL`` values first
if set to ``True``, according to the `SQLAlchemy documentation <https://docs.sqlalchemy.org/en/latest/core/sqlelement.html#sqlalchemy.sql.expression.nullsfirst>`__.

``nullslast`` is an optional attribute that will place ``NULL`` values last
if set to ``True``, according to the `SQLAlchemy documentation <https://docs.sqlalchemy.org/en/latest/core/sqlelement.html#sqlalchemy.sql.expression.nullslast>`__.

If none of them are provided, then ``NULL`` values will be sorted according
to the RDBMS being used. SQL defines that ``NULL`` values should be placed
together when sorting, but it does not specify whether they should be placed
first or last.

Even though both ``nullsfirst`` and ``nullslast`` are part of SQLAlchemy_,
they will raise an unexpected exception if the RDBMS that is being used does
not support them.

At the moment they are
`supported by PostgreSQL <https://www.postgresql.org/docs/current/queries-order.html>`_,
but they are **not** supported by SQLite and MySQL.



Running tests
-------------

The default configuration uses **SQLite**, **MySQL** (if the driver is
installed, which is the case when ``tox`` is used) and **PostgreSQL**
(if the driver is installed, which is the case when ``tox`` is used) to
run the tests, with the following URIs:

.. code-block:: shell

    sqlite+pysqlite:///test_sqlalchemy_filters.db
    mysql+mysqlconnector://root:@localhost:3306/test_sqlalchemy_filters
    postgresql+psycopg2://postgres:@localhost:5432/test_sqlalchemy_filters?client_encoding=utf8'

A test database will be created, used during the tests and destroyed
afterwards for each RDBMS configured.

There are Makefile targets to run docker containers locally for both
**MySQL** and **PostgreSQL**, using the default ports and configuration:

.. code-block:: shell

    $ make mysql-container
    $ make postgres-container

To run the tests locally:

.. code-block:: shell

    $ # Create/activate a virtual environment
    $ pip install tox
    $ tox

There are some other Makefile targets that can be used to run the tests:

There are other Makefile targets to run the tests, but extra
dependencies will have to be installed:

.. code-block:: shell

    $ pip install -U --editable ".[dev,mysql,postgresql]"
    $ # using default settings
    $ make test
    $ make coverage

    $ # overriding DB parameters
    $ ARGS='--mysql-test-db-uri mysql+mysqlconnector://root:@192.168.99.100:3340/test_sqlalchemy_filters' make test
    $ ARGS='--sqlite-test-db-uri sqlite+pysqlite:///test_sqlalchemy_filters.db' make test

    $ ARGS='--mysql-test-db-uri mysql+mysqlconnector://root:@192.168.99.100:3340/test_sqlalchemy_filters' make coverage
    $ ARGS='--sqlite-test-db-uri sqlite+pysqlite:///test_sqlalchemy_filters.db' make coverage



Database management systems
---------------------------

The following RDBMS are supported (tested):

- SQLite
- MySQL
- PostgreSQL


Python 2
--------

There is no active support for Python 2. However, it is compatible as of
February 2019, if you install ``funcsigs``, included in the ``python2``
extra requirements.


SQLAlchemy support
------------------

The following SQLAlchemy_ versions are supported: ``1.0``, ``1.1``,
``1.2``, ``1.3``.


Changelog
---------

Consult the `CHANGELOG <https://github.com/juliotrigo/sqlalchemy-filters/blob/master/CHANGELOG.rst>`_
document for fixes and enhancements of each version.


License
-------

Apache 2.0. See `LICENSE <https://github.com/juliotrigo/sqlalchemy-filters/blob/master/LICENSE>`_
for details.


.. _SQLAlchemy: https://www.sqlalchemy.org/
.. _hybrid attribute: https://docs.sqlalchemy.org/en/13/orm/extensions/hybrid.html
.. _hybrid property: https://docs.sqlalchemy.org/en/13/orm/extensions/hybrid.html#sqlalchemy.ext.hybrid.hybrid_property
.. _hybrid method: https://docs.sqlalchemy.org/en/13/orm/extensions/hybrid.html#sqlalchemy.ext.hybrid.hybrid_method