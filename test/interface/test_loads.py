# -*- coding: utf-8 -*-
import pytest
from sqlalchemy.orm import joinedload

from sqlalchemy_filters import apply_loads
from sqlalchemy_filters.exceptions import BadLoadFormat, BadSpec, FieldNotFound
from test.models import Foo, Bar
from test import error_value


@pytest.fixture
def multiple_bars_inserted(session):
    bar_1 = Bar(id=1, name='name_1', count=5)
    bar_2 = Bar(id=2, name='name_2', count=10)
    bar_3 = Bar(id=3, name='name_1', count=None)
    bar_4 = Bar(id=4, name='name_4', count=15)
    session.add_all([bar_1, bar_2, bar_3, bar_4])
    session.commit()


@pytest.fixture
def multiple_foos_inserted(multiple_bars_inserted, session):
    foo_1 = Foo(id=1, name='name_1', count=5, bar_id=1)
    foo_2 = Foo(id=2, name='name_2', count=10, bar_id=2)
    foo_3 = Foo(id=3, name='name_1', count=None, bar_id=3)
    foo_4 = Foo(id=4, name='name_4', count=15, bar_id=4)
    session.add_all([foo_1, foo_2, foo_3, foo_4])
    session.commit()


class TestLoadNotApplied(object):

    @pytest.mark.parametrize('spec', [1, []])
    def test_wrong_spec_format(self, session, spec):
        query = session.query(Bar)
        load_spec = [spec]

        with pytest.raises(BadLoadFormat) as err:
            apply_loads(query, load_spec)

        expected_error = 'Load spec `{}` should be a dictionary.'.format(spec)
        assert expected_error == error_value(err)

    def test_field_not_provided(self, session):
        query = session.query(Bar)
        load_spec = [{}]

        with pytest.raises(BadLoadFormat) as err:
            apply_loads(query, load_spec)

        expected_error = '`fields` is a mandatory attribute.'
        assert expected_error == error_value(err)

    def test_invalid_field(self, session):
        query = session.query(Bar)
        load_spec = [{'fields': ['invalid_field']}]

        with pytest.raises(FieldNotFound) as err:
            apply_loads(query, load_spec)

        expected_error = (
            "Model <class 'test.models.Bar'> has no column `invalid_field`."
        )
        assert expected_error == error_value(err)


class TestLoadsApplied(object):

    def test_no_load_provided(self, session):
        query = session.query(Bar)
        load_spec = []

        restricted_query = apply_loads(query, load_spec)

        # defers all fields
        expected = (
            "SELECT bar.id AS bar_id \n"
            "FROM bar"
        )
        assert str(restricted_query) == expected

    def test_single_value(self, session):

        query = session.query(Bar)
        loads = [
            {'fields': ['name']}
        ]

        restricted_query = apply_loads(query, loads)

        expected = (
            "SELECT bar.id AS bar_id, bar.name AS bar_name \n"
            "FROM bar"
        )
        assert str(restricted_query) == expected

    def test_multiple_values_single_model(self, session):

        query = session.query(Foo)
        loads = [
            {'fields': ['name', 'count']}
        ]

        restricted_query = apply_loads(query, loads)

        expected = (
            "SELECT foo.id AS foo_id, foo.name AS foo_name, "
            "foo.count AS foo_count \n"
            "FROM foo"
        )
        assert str(restricted_query) == expected

    def test_multiple_values_multiple_models(self, session):

        query = session.query(Foo, Bar)
        loads = [
            {'model': 'Foo', 'fields': ['count']},
            {'model': 'Bar', 'fields': ['count']},
        ]

        restricted_query = apply_loads(query, loads)

        expected = (
            "SELECT foo.id AS foo_id, foo.count AS foo_count, "
            "bar.id AS bar_id, bar.count AS bar_count \n"
            "FROM foo, bar"
        )
        assert str(restricted_query) == expected

    def test_multiple_values_multiple_models_joined(self, session, db_uri):

        query = session.query(Foo, Bar).join(Bar)
        loads = [
            {'model': 'Foo', 'fields': ['count']},
            {'model': 'Bar', 'fields': ['count']},
        ]

        restricted_query = apply_loads(query, loads)

        join_type = "INNER JOIN" if "mysql" in db_uri else "JOIN"

        expected = (
            "SELECT foo.id AS foo_id, foo.count AS foo_count, "
            "bar.id AS bar_id, bar.count AS bar_count \n"
            "FROM foo {join} bar ON bar.id = foo.bar_id".format(join=join_type)
        )
        assert str(restricted_query) == expected

    def test_multiple_values_multiple_models_lazy_load(self, session, db_uri):

        query = session.query(Foo).join(Bar)
        loads = [
            {'model': 'Foo', 'fields': ['count']},
            {'model': 'Bar', 'fields': ['count']},
        ]

        restricted_query = apply_loads(query, loads)

        join_type = "INNER JOIN" if "mysql" in db_uri else "JOIN"

        # Bar is lazily joined, so the second loads directive has no effect
        expected = (
            "SELECT foo.id AS foo_id, foo.count AS foo_count \n"
            "FROM foo {join} bar ON bar.id = foo.bar_id".format(join=join_type)
        )
        assert str(restricted_query) == expected

    def test_a_single_dict_can_be_supplied_as_load_spec(self, session):

        query = session.query(Foo)
        load_spec = {'fields': ['name', 'count']}

        restricted_query = apply_loads(query, load_spec)

        expected = (
            "SELECT foo.id AS foo_id, foo.name AS foo_name, "
            "foo.count AS foo_count \n"
            "FROM foo"
        )
        assert str(restricted_query) == expected

    def test_a_list_of_fields_can_be_supplied_as_load_spec(self, session):

        query = session.query(Foo)
        load_spec = ['name', 'count']

        restricted_query = apply_loads(query, load_spec)

        expected = (
            "SELECT foo.id AS foo_id, foo.name AS foo_name, "
            "foo.count AS foo_count \n"
            "FROM foo"
        )
        assert str(restricted_query) == expected

    def test_eager_load(self, session, db_uri):

        query = session.query(Foo).options(joinedload(Foo.bar))
        load_spec = [
            {'model': 'Foo', 'fields': ['name']},
            {'model': 'Bar', 'fields': ['count']}
        ]
        restricted_query = apply_loads(query, load_spec)

        join_type = "INNER JOIN" if "mysql" in db_uri else "JOIN"

        # autojoin has no effect
        expected = (
            "SELECT "
            "foo.id AS foo_id, foo.name AS foo_name, "
            "foo.bar_id AS foo_bar_id, "
            "bar_1.id AS bar_1_id, bar_1.name AS bar_1_name, "
            "bar_1.count AS bar_1_count \n"
            "FROM foo {join} bar ON bar.id = foo.bar_id "
            "LEFT OUTER JOIN bar AS bar_1 ON bar_1.id = foo.bar_id".format(
                join=join_type
            )
        )

        assert str(restricted_query) == expected


class TestAutoJoin:

    @pytest.mark.usefixtures('multiple_foos_inserted')
    def test_auto_join(self, session, db_uri):

        query = session.query(Foo)
        loads = [
            {'fields': ['count']},
            {'model': 'Bar', 'fields': ['count']},
        ]

        restricted_query = apply_loads(query, loads)

        join_type = "INNER JOIN" if "mysql" in db_uri else "JOIN"

        # Bar is lazily joined, so the second loads directive has no effect
        expected = (
            "SELECT foo.id AS foo_id, foo.count AS foo_count \n"
            "FROM foo {join} bar ON bar.id = foo.bar_id".format(join=join_type)
        )
        assert str(restricted_query) == expected

    @pytest.mark.usefixtures('multiple_foos_inserted')
    def test_noop_if_query_contains_named_models(self, session, db_uri):

        query = session.query(Foo, Bar).join(Bar)
        loads = [
            {'model': 'Foo', 'fields': ['count']},
            {'model': 'Bar', 'fields': ['count']},
        ]

        restricted_query = apply_loads(query, loads)

        join_type = "INNER JOIN" if "mysql" in db_uri else "JOIN"

        expected = (
            "SELECT foo.id AS foo_id, foo.count AS foo_count, "
            "bar.id AS bar_id, bar.count AS bar_count \n"
            "FROM foo {join} bar ON bar.id = foo.bar_id".format(join=join_type)
        )
        assert str(restricted_query) == expected

    @pytest.mark.usefixtures('multiple_foos_inserted')
    def test_auto_join_to_invalid_model(self, session):

        query = session.query(Foo, Bar)
        loads = [
            {'model': 'Foo', 'fields': ['count']},
            {'model': 'Bar', 'fields': ['count']},
            {'model': 'Qux', 'fields': ['count']},
        ]

        with pytest.raises(BadSpec) as err:
            apply_loads(query, loads)

        assert 'The query does not contain model `Qux`.' == err.value.args[0]

    @pytest.mark.usefixtures('multiple_foos_inserted')
    def test_ambiguous_query(self, session):

        query = session.query(Foo, Bar)
        loads = [
            {'fields': ['count']},  # ambiguous
            {'model': 'Bar', 'fields': ['count']},
            {'model': 'Qux', 'fields': ['count']},
        ]

        with pytest.raises(BadSpec) as err:
            apply_loads(query, loads)

        assert 'Ambiguous spec. Please specify a model.' == err.value.args[0]
