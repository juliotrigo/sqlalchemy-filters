SQLAlchemy-filters
==================

.. pull-quote::

    Filter, sort and paginate SQLALquemy query objects.

Usage
-----

.. code-block:: python

    from sqlalchemy_filters import apply_filters, create_query

    # a SQLAlchemy `session` alrady exists

    # `Foo` model:
    # class Foo(Base):
    #     __tablename__ = 'foo'
    #     id = Column(Integer, primary_key=True)
    #     name = Column(String(50), nullable=False)
    #     count = Column(Integer, nullable=True)

    query = create_query(session, Foo)

    filters = [{'field': 'name', 'op': '==', 'value': 'name_1'}]
    filtered_query = apply_filters(query, filters)

    more_filters = [{'field': 'id', 'op': '==', 'value': 3}]
    filtered_query = apply_filters(filtered_query, more_filters)

    result = filtered_query.all()


Running tests
-------------

There are some Makefile targets that can be used to run the tests. A
test database will be created, used during the tests and destroyed
afterwards.

These are the default configuration values, that can be
overridden when executing the Makefile targets:

.. code-block:: Makefile

    DB_USER ?= root
    DB_PASS ?= password
    DB_SERVER ?= localhost
    DB_PORT ?= 3306
    DB_NAME ?= test_sqlalchemy_filters
    DB_DIALECT ?= 'mysql'
    DB_DRIVER ?= 'mysqlconnector'

Example of usage:

.. code-block:: shell

    $ make test DB_SERVER=192.168.99.100 DB_PORT=3340

    $ make coverage DB_SERVER=192.168.99.100 DB_PORT=3340
