# -*- coding: utf-8 -*-

import pytest
from sqlalchemy_filters import create_query, get_query_entities
from test.models import Bar, Qux


class TestCreateQuery(object):

    def test_no_models_provided(self, session):
        query = create_query(session, ())

        assert [] == query.column_descriptions

    @pytest.mark.parametrize('models', [(Bar, ), Bar])
    def test_one_model_provided(self, session, models):
        # Single models can be provided directly, without adding them to
        # a sequence
        query = create_query(session, models)

        column_desc = query.column_descriptions

        assert 1 == len(column_desc)
        assert Bar == column_desc[0]['type']

    def test_multiple_models_provided(self, session):
        query = create_query(session, (Bar, Qux))

        column_desc = query.column_descriptions
        entities = [entity['type'] for entity in query.column_descriptions]

        assert 2 == len(column_desc)
        assert Bar in entities
        assert Qux in entities


class TestGetQueryEntities(object):

    def test_query_with_no_models(self, session):
        query = session.query()

        entities = get_query_entities(query)

        assert {} == entities

    def test_query_with_one_model(self, session):
        query = session.query(Bar)

        entities = get_query_entities(query)

        assert {'Bar': Bar} == entities

    def test_query_with_multiple_models(self, session):
        query = session.query(Bar, Qux)

        entities = get_query_entities(query)

        assert {'Bar': Bar, 'Qux': Qux} == entities

    def test_query_with_duplicated_models(self, session):
        query = session.query(Bar, Qux, Bar)

        entities = get_query_entities(query)

        assert {'Bar': Bar, 'Qux': Qux} == entities
