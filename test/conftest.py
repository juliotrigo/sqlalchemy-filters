# -*- coding: utf-8 -*-

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, drop_database, database_exists

from test.models import Base, BasePostgresqlSpecific


SQLITE_TEST_DB_URI = 'SQLITE_TEST_DB_URI'
MYSQL_TEST_DB_URI = 'MYSQL_TEST_DB_URI'
POSTGRESQL_TEST_DB_URI = 'POSTGRESQL_TEST_DB_URI'


def pytest_addoption(parser):
    parser.addoption(
        '--sqlite-test-db-uri',
        action='store',
        dest=SQLITE_TEST_DB_URI,
        default='sqlite+pysqlite:///test_sqlalchemy_filters.db',
        help=(
            'DB uri for testing (e.g. '
            '"sqlite+pysqlite:///test_sqlalchemy_filters.db")'
        )
    )

    parser.addoption(
        '--mysql-test-db-uri',
        action='store',
        dest=MYSQL_TEST_DB_URI,
        default=(
            'mysql+mysqlconnector://root:@localhost:3306'
            '/test_sqlalchemy_filters'
        ),
        help=(
            'DB uri for testing (e.g. '
            '"mysql+mysqlconnector://username:password@localhost:3306'
            '/test_sqlalchemy_filters")'
        )
    )

    parser.addoption(
        '--postgresql-test-db-uri',
        action='store',
        dest=POSTGRESQL_TEST_DB_URI,
        default=(
            'postgresql+psycopg2://postgres:@localhost:5432'
            '/test_sqlalchemy_filters?client_encoding=utf8'
        ),
        help=(
            'DB uri for testing (e.g. '
            '"postgresql+psycopg2://username:password@localhost:5432'
            '/test_sqlalchemy_filters?client_encoding=utf8")'
        )
    )


@pytest.fixture(scope='session')
def config(request):
    return {
        SQLITE_TEST_DB_URI: request.config.getoption(SQLITE_TEST_DB_URI),
        MYSQL_TEST_DB_URI: request.config.getoption(MYSQL_TEST_DB_URI),
        POSTGRESQL_TEST_DB_URI: request.config.getoption(
            POSTGRESQL_TEST_DB_URI
        ),
    }


def test_db_keys():
    """Decide what DB backends to use to run the tests."""
    test_db_uris = []
    test_db_uris.append(SQLITE_TEST_DB_URI)

    try:
        import mysql  # noqa: F401
    except ImportError:
        pass
    else:
        test_db_uris.append(MYSQL_TEST_DB_URI)

    try:
        import psycopg2  # noqa: F401
    except ImportError:
        pass
    else:
        test_db_uris.append(POSTGRESQL_TEST_DB_URI)

    return test_db_uris


@pytest.fixture(scope='session', params=test_db_keys())
def db_uri(request, config):
    return config[request.param]


@pytest.fixture(scope='session')
def is_postgresql(db_uri):
    if 'postgresql' in db_uri:
        return True
    return False


@pytest.fixture(scope='session')
def is_sqlite(db_uri):
    if 'sqlite' in db_uri:
        return True
    return False


@pytest.fixture(scope='session')
def db_engine_options(db_uri, is_postgresql):
    if is_postgresql:
        return dict(
            client_encoding='utf8',
            connect_args={'client_encoding': 'utf8'}
        )
    return {}


@pytest.fixture(scope='session')
def connection(db_uri, db_engine_options, is_postgresql):
    create_db(db_uri)
    engine = create_engine(db_uri, **db_engine_options)
    Base.metadata.create_all(engine)
    connection = engine.connect()
    Base.metadata.bind = engine
    if is_postgresql:
        BasePostgresqlSpecific.metadata.create_all(engine)
        BasePostgresqlSpecific.metadata.bind = engine

    yield connection

    Base.metadata.drop_all()
    destroy_database(db_uri)


@pytest.fixture()
def session(connection, is_postgresql):
    Session = sessionmaker(bind=connection)
    db_session = Session()

    yield db_session

    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    if is_postgresql:
        for table in reversed(BasePostgresqlSpecific.metadata.sorted_tables):
            db_session.execute(table.delete())

    db_session.commit()
    db_session.close()


def create_db(uri):
    """Drop the database at ``uri`` and create a brand new one. """
    destroy_database(uri)
    create_database(uri)


def destroy_database(uri):
    """Destroy the database at ``uri``, if it exists. """
    if database_exists(uri):
        drop_database(uri)
