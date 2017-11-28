import pytest
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from sqlalchemy_filters.exceptions import BadSpec, BadQuery
from sqlalchemy_filters.models import get_query_models, get_model_from_spec
from test.models import Bar, Foo, Qux


class TestGetQueryModels(object):

    def test_query_with_no_models(self, session):
        query = session.query()

        entities = get_query_models(query)

        assert {} == entities

    def test_query_with_one_model(self, session):
        query = session.query(Bar)

        entities = get_query_models(query)

        assert {'Bar': Bar} == entities

    def test_query_with_multiple_models(self, session):
        query = session.query(Bar, Qux)

        entities = get_query_models(query)

        assert {'Bar': Bar, 'Qux': Qux} == entities

    def test_query_with_duplicated_models(self, session):
        query = session.query(Bar, Qux, Bar)

        entities = get_query_models(query)

        assert {'Bar': Bar, 'Qux': Qux} == entities

    def test_query_with_one_field(self, session):
        query = session.query(Foo.id)

        entities = get_query_models(query)

        assert {'Foo': Foo} == entities

    def test_query_with_multiple_fields(self, session):
        query = session.query(Foo.id, Bar.id, Bar.name)

        entities = get_query_models(query)

        assert {'Foo': Foo, 'Bar': Bar} == entities

    def test_query_with_aggregate_func(self, session):
        query = session.query(func.count(Foo.id))

        entities = get_query_models(query)

        assert {'Foo': Foo} == entities

    def test_query_with_join(self, session):
        query = session.query(Foo).join(Bar)

        entities = get_query_models(query)

        assert {'Foo': Foo, 'Bar': Bar} == entities

    def test_query_with_multiple_joins(self, session):
        query = session.query(Foo).join(Bar).join(Qux, Bar.id == Qux.id)

        entities = get_query_models(query)

        assert {'Foo': Foo, 'Bar': Bar, 'Qux': Qux} == entities

    def test_query_with_joinedload(self, session):
        query = session.query(Foo).options(joinedload(Foo.bar))

        entities = get_query_models(query)

        # Bar is not added to the query since the joinedload is transparent
        assert {'Foo': Foo} == entities


class TestGetModelFromSpec:

    def test_query_with_no_models(self, session):
        query = session.query()
        spec = {'field': 'name', 'op': '==', 'value': 'name_1'}

        with pytest.raises(BadQuery) as err:
            get_model_from_spec(spec, query)

        assert 'The query does not contain any models.' == err.value.args[0]

    def test_query_with_named_model(self, session):
        query = session.query(Bar)
        spec = {'model': 'Bar'}

        model = get_model_from_spec(spec, query)
        assert model == Bar

    def test_query_with_missing_named_model(self, session):
        query = session.query(Bar)
        spec = {'model': 'Buz'}

        with pytest.raises(BadSpec) as err:
            get_model_from_spec(spec, query)

        assert 'The query does not contain model `Buz`.' == err.value.args[0]

    def test_multiple_models_ambiquous_spec(self, session):
        query = session.query(Bar, Qux)
        spec = {'field': 'name', 'op': '==', 'value': 'name_1'}

        with pytest.raises(BadSpec) as err:
            get_model_from_spec(spec, query)

        assert 'Ambiguous spec. Please specify a model.' == err.value.args[0]
