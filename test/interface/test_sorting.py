# -*- coding: utf-8 -*-

import pytest

from sqlalchemy_filters.exceptions import (
    BadQuery, BadSortFormat, FieldNotFound
)
from sqlalchemy_filters.sorting import apply_sort
from test import error_value
from test.models import Bar, Qux


class TestProvidedModels(object):

    def test_query_with_no_models(self, session):
        query = session.query()
        order_by = [{'field': 'name', 'direction': 'asc'}]

        with pytest.raises(BadQuery) as err:
            apply_sort(query, order_by)

        assert 'The query does not contain any models.' == error_value(err)

    # TODO: replace this test once we support multiple models
    def test_multiple_models(self, session):
        query = session.query(Bar, Qux)
        order_by = [{'field': 'name', 'direction': 'asc'}]

        with pytest.raises(BadQuery) as err:
            apply_sort(query, order_by)

        expected_error = 'The query should contain only one model.'
        assert expected_error == error_value(err)


class TestSortNotApplied(object):

    def test_no_sort_provided(self, session):
        query = session.query(Bar)
        order_by = []

        filtered_query = apply_sort(query, order_by)

        assert query == filtered_query

    @pytest.mark.parametrize('sort', ['some text', 1, []])
    def test_wrong_sort_format(self, session, sort):
        query = session.query(Bar)
        order_by = [sort]

        with pytest.raises(BadSortFormat) as err:
            apply_sort(query, order_by)

        expected_error = 'Sort `{}` should be a dictionary.'.format(sort)
        assert expected_error == error_value(err)

    def test_field_not_provided(self, session):
        query = session.query(Bar)
        order_by = [{'direction': 'asc'}]

        with pytest.raises(BadSortFormat) as err:
            apply_sort(query, order_by)

        expected_error = '`field` and `direction` are mandatory attributes.'
        assert expected_error == error_value(err)

    def test_invalid_field(self, session):
        query = session.query(Bar)
        order_by = [{'field': 'invalid_field', 'direction': 'asc'}]

        with pytest.raises(FieldNotFound) as err:
            apply_sort(query, order_by)

        expected_error = (
            "Model <class 'test.models.Bar'> has no column `invalid_field`."
        )
        assert expected_error == error_value(err)

    def test_direction_not_provided(self, session):
        query = session.query(Bar)
        order_by = [{'field': 'name'}]

        with pytest.raises(BadSortFormat) as err:
            apply_sort(query, order_by)

        expected_error = '`field` and `direction` are mandatory attributes.'
        assert expected_error == error_value(err)

    def test_invalid_direction(self, session):
        query = session.query(Bar)
        order_by = [{'field': 'name', 'direction': 'invalid_direction'}]

        with pytest.raises(BadSortFormat) as err:
            apply_sort(query, order_by)

        expected_error = 'Direction `invalid_direction` not valid.'
        assert expected_error == error_value(err)


class TestSortApplied(object):

    @pytest.fixture
    def multiple_bars_inserted(self, session):
        bar_1 = Bar(id=1, name='name_1', count=5)
        bar_2 = Bar(id=2, name='name_2', count=10)
        bar_3 = Bar(id=3, name='name_1', count=None)
        bar_4 = Bar(id=4, name='name_4', count=12)
        bar_5 = Bar(id=5, name='name_1', count=2)
        bar_6 = Bar(id=6, name='name_4', count=15)
        bar_7 = Bar(id=7, name='name_1', count=2)
        bar_8 = Bar(id=8, name='name_5', count=1)
        session.add_all(
            [bar_1, bar_2, bar_3, bar_4, bar_5, bar_6, bar_7, bar_8]
        )
        session.commit()

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_single_sort_field_asc(self, session):
        query = session.query(Bar)
        order_by = [{'field': 'name', 'direction': 'asc'}]

        sorted_query = apply_sort(query, order_by)
        result = sorted_query.all()

        assert len(result) == 8
        assert result[0].id == 1
        assert result[1].id == 3
        assert result[2].id == 5
        assert result[3].id == 7
        assert result[4].id == 2
        assert result[5].id == 4
        assert result[6].id == 6
        assert result[7].id == 8

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_single_sort_field_desc(self, session):
        query = session.query(Bar)
        order_by = [{'field': 'name', 'direction': 'desc'}]

        sorted_query = apply_sort(query, order_by)
        result = sorted_query.all()

        assert len(result) == 8
        assert result[0].id == 8
        assert result[1].id == 4
        assert result[2].id == 6
        assert result[3].id == 2
        assert result[4].id == 1
        assert result[5].id == 3
        assert result[6].id == 5
        assert result[7].id == 7

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_multiple_sort_fields(self, session):
        query = session.query(Bar)
        order_by = [
            {'field': 'name', 'direction': 'asc'},
            {'field': 'count', 'direction': 'desc'},
            {'field': 'id', 'direction': 'desc'},
        ]

        sorted_query = apply_sort(query, order_by)
        result = sorted_query.all()

        assert len(result) == 8
        assert result[0].id == 1
        assert result[1].id == 7
        assert result[2].id == 5
        assert result[3].id == 3
        assert result[4].id == 2
        assert result[5].id == 6
        assert result[6].id == 4
        assert result[7].id == 8
