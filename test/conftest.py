# -*- coding: utf-8 -*-

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, drop_database, database_exists

from test.models import Base


def pytest_addoption(parser):
    parser.addoption(
        '--test-db-uri',
        action='store',
        dest='TEST_DB_URI',
        default='sqlite+pysqlite:///test_sqlalchemy_filters.db',
        help=(
            'DB uri for testing (e.g. '
            '"mysql+mysqlconnector:username:password@localhost:3306'
            '/test_sqlalchemy_filters")'
        )
    )


@pytest.fixture(scope='session')
def config(request):
    return {
        'TEST_DB_URI': request.config.getoption('TEST_DB_URI')
    }


@pytest.fixture(scope='session')
def db_uri(config):
    return config['TEST_DB_URI']


@pytest.yield_fixture(scope='session')
def connection(db_uri):
    create_db(db_uri)
    engine = create_engine(db_uri)
    Base.metadata.create_all(engine)
    connection = engine.connect()
    Base.metadata.bind = engine

    yield connection

    Base.metadata.drop_all()
    destroy_database(db_uri)


@pytest.yield_fixture()
def session(connection):
    Session = sessionmaker(bind=connection)
    db_session = Session()

    yield db_session

    for table in reversed(Base.metadata.sorted_tables):
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
