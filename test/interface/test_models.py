import pytest
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from sqlalchemy_filters.exceptions import BadSpec, BadQuery
from sqlalchemy_filters.models import (
    auto_join, get_default_model, get_query_models, get_model_class_by_name,
    get_model_from_spec, sqlalchemy_version_lt
)
from test.models import Base, Bar, Foo, Qux


class TestGetQueryModels(object):

    def test_query_with_no_models(self, session):
        query = session.query()

        entities = get_query_models(query)

        assert {} == entities

    def test_query_with_one_model(self, session):
        query = session.query(Bar)

        entities = get_query_models(query)

        assert {'Bar': Bar} == entities

    def test_query_with_select_from_model(self, session):
        query = session.query().select_from(Bar)

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


class TestGetModelClassByName:

    @pytest.fixture
    def registry(self):
        return (
            Base._decl_class_registry
            if sqlalchemy_version_lt('1.4')
            else Base.registry._class_registry
        )

    def test_exists(self, registry):
        assert get_model_class_by_name(registry, 'Foo') == Foo

    def test_model_does_not_exist(self, registry):
        assert get_model_class_by_name(registry, 'Missing') is None


class TestGetDefaultModel:

    def test_single_model_query(self, session):
        query = session.query(Foo)
        assert get_default_model(query) == Foo

    def test_multi_model_query(self, session):
        query = session.query(Foo).join(Bar)
        assert get_default_model(query) is None

    def test_empty_query(self, session):
        query = session.query()
        assert get_default_model(query) is None


class TestAutoJoin:

    def test_model_not_present(self, session, db_uri):
        query = session.query(Foo)
        query = auto_join(query, 'Bar')

        join_type = "INNER JOIN" if "mysql" in db_uri else "JOIN"

        expected = (
            "SELECT "
            "foo.id AS foo_id, foo.name AS foo_name, "
            "foo.count AS foo_count, foo.bar_id AS foo_bar_id \n"
            "FROM foo {join} bar ON bar.id = foo.bar_id".format(join=join_type)
        )
        assert str(query) == expected

    def test_model_already_present(self, session):
        query = session.query(Foo, Bar)

        # no join applied
        expected = (
            "SELECT "
            "foo.id AS foo_id, foo.name AS foo_name, "
            "foo.count AS foo_count, foo.bar_id AS foo_bar_id, "
            "bar.id AS bar_id, bar.name AS bar_name, bar.count AS bar_count \n"
            "FROM foo, bar"
        )
        assert str(query) == expected

        query = auto_join(query, 'Bar')
        assert str(query) == expected   # no change

    def test_model_already_joined(self, session, db_uri):
        query = session.query(Foo).join(Bar)

        join_type = "INNER JOIN" if "mysql" in db_uri else "JOIN"

        expected = (
            "SELECT "
            "foo.id AS foo_id, foo.name AS foo_name, "
            "foo.count AS foo_count, foo.bar_id AS foo_bar_id \n"
            "FROM foo {join} bar ON bar.id = foo.bar_id".format(join=join_type)
        )
        assert str(query) == expected

        query = auto_join(query, 'Bar')
        assert str(query) == expected   # no change

    def test_model_eager_joined(self, session, db_uri):
        query = session.query(Foo).options(joinedload(Foo.bar))

        join_type = "INNER JOIN" if "mysql" in db_uri else "JOIN"

        expected_eager = (
            "SELECT "
            "foo.id AS foo_id, foo.name AS foo_name, "
            "foo.count AS foo_count, foo.bar_id AS foo_bar_id, "
            "bar_1.id AS bar_1_id, bar_1.name AS bar_1_name, "
            "bar_1.count AS bar_1_count \n"
            "FROM foo LEFT OUTER JOIN bar AS bar_1 ON bar_1.id = foo.bar_id"
        )
        assert str(query) == expected_eager

        expected_joined = (
            "SELECT "
            "foo.id AS foo_id, foo.name AS foo_name, "
            "foo.count AS foo_count, foo.bar_id AS foo_bar_id, "
            "bar_1.id AS bar_1_id, bar_1.name AS bar_1_name, "
            "bar_1.count AS bar_1_count \n"
            "FROM foo {join} bar ON bar.id = foo.bar_id "
            "LEFT OUTER JOIN bar AS bar_1 ON bar_1.id = foo.bar_id".format(
                join=join_type
            )
        )

        query = auto_join(query, 'Bar')
        assert str(query) == expected_joined

    def test_model_does_not_exist(self, session, db_uri):
        query = session.query(Foo)

        expected = (
            "SELECT "
            "foo.id AS foo_id, foo.name AS foo_name, "
            "foo.count AS foo_count, foo.bar_id AS foo_bar_id \n"
            "FROM foo"
        )
        assert str(query) == expected

        query = auto_join(query, 'Missing')
        assert str(query) == expected   # no change
