# -*- coding: utf-8 -*-
import pytest

from sqlalchemy_filters import apply_loads
from test.models import Foo, Bar


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


class TestFieldsApplied(object):

    @pytest.mark.usefixtures('multiple_bars_inserted')
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

    @pytest.mark.usefixtures('multiple_foos_inserted')
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

    @pytest.mark.usefixtures('multiple_foos_inserted')
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

    @pytest.mark.usefixtures('multiple_foos_inserted')
    def test_multiple_values_multiple_models_joined(self, session):

        query = session.query(Foo, Bar).join(Bar)
        loads = [
            {'model': 'Foo', 'fields': ['count']},
            {'model': 'Bar', 'fields': ['count']},
        ]

        restricted_query = apply_loads(query, loads)

        expected = (
            "SELECT foo.id AS foo_id, foo.count AS foo_count, "
            "bar.id AS bar_id, bar.count AS bar_count \n"
            "FROM foo INNER JOIN bar ON bar.id = foo.bar_id"
        )
        assert str(restricted_query) == expected

    @pytest.mark.usefixtures('multiple_foos_inserted')
    def test_multiple_values_multiple_models_lazy_load(self, session):

        query = session.query(Foo).join(Bar)
        loads = [
            {'model': 'Foo', 'fields': ['count']},
            {'model': 'Bar', 'fields': ['count']},
        ]

        restricted_query = apply_loads(query, loads)

        # Bar is lazily joined, so the second loads directive has no effect
        expected = (
            "SELECT foo.id AS foo_id, foo.count AS foo_count \n"
            "FROM foo INNER JOIN bar ON bar.id = foo.bar_id"
        )
        assert str(restricted_query) == expected
