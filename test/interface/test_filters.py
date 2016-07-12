# -*- coding: utf-8 -*-

import pytest
from sqlalchemy_filters import apply_filters
from sqlalchemy_filters.exceptions import (
    BadFilterFormat,
    InvalidOperator,
    ModelNotFound,
)
from test.models import Bar


class TestNoModelsProvided(object):

    def test_query_with_no_models(self, session):
        query = session.query()
        filters = [{'field': 'name', 'op': '==', 'value': 'name_1'}]

        with pytest.raises(ModelNotFound) as err:
            apply_filters(query, filters)

        assert 'The query should contain some entities.' == err.value.args[0]


class TestProvidedFilters(object):

    def test_no_filters_provided(self, session):
        query = session.query(Bar)
        filters = []

        filtered_query = apply_filters(query, filters)

        assert query == filtered_query

    @pytest.mark.parametrize('filter_', ['some text', 1, []])
    def test_wrong_filters_format(self, session, filter_):
        query = session.query(Bar)
        filters = [filter_]

        with pytest.raises(BadFilterFormat) as err:
            apply_filters(query, filters)

        expected_query = 'Filter `{}` is not a dictionary.'.format(filter_)
        assert expected_query == err.value.args[0]

    def test_invalid_operator(self, session):
        query = session.query(Bar)
        filters = [{'field': 'name', 'op': 'op_not_valid', 'value': 'name_1'}]

        with pytest.raises(InvalidOperator) as err:
            apply_filters(query, filters)

        assert 'Operator `op_not_valid` not valid.' == err.value.args[0]

    def test_no_operator_provided(self, session):
        query = session.query(Bar)
        filters = [{'field': 'name', 'value': 'name_1'}]

        with pytest.raises(InvalidOperator) as err:
            apply_filters(query, filters)

        assert 'Operator not provided.' == err.value.args[0]

    def test_no_field_provided(self, session):
        query = session.query(Bar)
        filters = [{'op': '==', 'value': 'name_1'}]

        with pytest.raises(BadFilterFormat) as err:
            apply_filters(query, filters)

        assert '`field` is a mandatory filter attribute.' == err.value.args[0]

    def test_provide_both_value_and_other_field(self, session):
        query = session.query(Bar)
        filters = [{
            'field': 'name',
            'op': '==',
            'value': 'name_1',
            'other_field': 'count'
        }]

        with pytest.raises(BadFilterFormat) as err:
            apply_filters(query, filters)

        err_value = err.value.args[0]
        assert 'Both `value` and `other_field` were provided.' == err_value

    def test_provide_neither_value_nor_other_field(self, session):
        query = session.query(Bar)
        filters = [{
            'field': 'name',
            'op': '==',  # Binary operator
        }]

        with pytest.raises(BadFilterFormat) as err:
            apply_filters(query, filters)

        err_value = err.value.args[0]
        assert 'Either `value` or `other_field` must be provided.' == err_value


class TestFixtures(object):

    @pytest.fixture
    def multiple_bars_inserted(self, session):
        bar_1 = Bar(id=1, name='name_1', count=5)
        bar_2 = Bar(id=2, name='name_2', count=10)
        bar_3 = Bar(id=3, name='name_1', count=None)
        bar_4 = Bar(id=4, name='name_4', count=15)
        session.add(bar_1)
        session.add(bar_2)
        session.add(bar_3)
        session.add(bar_4)
        session.commit()


class TestApplyIsNullFilter(TestFixtures):

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_filter_field_with_null_values(self, session):
        query = session.query(Bar)
        filters = [{'field': 'count', 'op': 'is_null'}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 1
        assert result[0].id == 3

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_filter_field_with_no_null_values(self, session):
        query = session.query(Bar)
        filters = [{'field': 'name', 'op': 'is_null'}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 0


class TestApplyIsNotNullFilter(TestFixtures):

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_filter_field_with_null_values(self, session):
        query = session.query(Bar)
        filters = [{'field': 'count', 'op': 'is_not_null'}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 3
        assert result[0].id == 1
        assert result[1].id == 2
        assert result[2].id == 4

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_filter_field_with_no_null_values(self, session):
        query = session.query(Bar)
        filters = [{'field': 'name', 'op': 'is_not_null'}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 4
        assert result[0].id == 1
        assert result[1].id == 2
        assert result[2].id == 3
        assert result[3].id == 4


class TestApplyFiltersMultipleTimes(TestFixtures):

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_concatenate_queries(self, session):
        query = session.query(Bar)
        filters = [{'field': 'name', 'op': '==', 'value': 'name_1'}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].name == 'name_1'
        assert result[1].id == 3
        assert result[1].name == 'name_1'

        filters = [{'field': 'id', 'op': '==', 'value': 3}]

        filtered_query = apply_filters(filtered_query, filters)
        result = filtered_query.all()

        assert len(result) == 1
        assert result[0].id == 3
        assert result[0].name == 'name_1'


class TestApplyEqualToFilter(TestFixtures):

    @pytest.mark.parametrize('operator', ['==', 'eq'])
    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_one_filter_applied_to_a_single_model(self, session, operator):
        query = session.query(Bar)
        filters = [{'field': 'name', 'op': operator, 'value': 'name_1'}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].name == 'name_1'
        assert result[1].id == 3
        assert result[1].name == 'name_1'

    @pytest.mark.parametrize('operator', ['==', 'eq'])
    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_multiple_filters_applied_to_a_single_model(
        self, session, operator
    ):
        query = session.query(Bar)
        filters = [
            {'field': 'name', 'op': operator, 'value': 'name_1'},
            {'field': 'id', 'op': operator, 'value': 3}
        ]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 1
        assert result[0].id == 3
        assert result[0].name == 'name_1'


class TestApplyNotEqualToFilter(TestFixtures):

    @pytest.mark.parametrize('operator', ['!=', 'ne'])
    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_one_filter_applied_to_a_single_model(self, session, operator):
        query = session.query(Bar)
        filters = [{'field': 'name', 'op': operator, 'value': 'name_1'}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 2
        assert result[0].id == 2
        assert result[0].name == 'name_2'
        assert result[1].id == 4
        assert result[1].name == 'name_4'

    @pytest.mark.parametrize('operator', ['!=', 'ne'])
    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_multiple_filters_applied_to_a_single_model(
        self, session, operator
    ):
        query = session.query(Bar)
        filters = [
            {'field': 'name', 'op': operator, 'value': 'name_2'},
            {'field': 'id', 'op': operator, 'value': 3}
        ]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].name == 'name_1'
        assert result[1].id == 4
        assert result[1].name == 'name_4'


class TestApplyGreaterThanFilter(TestFixtures):

    @pytest.mark.parametrize('operator', ['>', 'gt'])
    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_one_filter_applied_to_a_single_model(self, session, operator):
        query = session.query(Bar)
        filters = [{'field': 'count', 'op': operator, 'value': '5'}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 2
        assert result[0].id == 2
        assert result[1].id == 4

    @pytest.mark.parametrize('operator', ['>', 'gt'])
    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_multiple_filters_applied_to_a_single_model(
        self, session, operator
    ):
        query = session.query(Bar)
        filters = [
            {'field': 'count', 'op': operator, 'value': '5'},
            {'field': 'id', 'op': operator, 'value': 2},
        ]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 1
        assert result[0].id == 4


class TestApplyLessThanFilter(TestFixtures):

    @pytest.mark.parametrize('operator', ['<', 'lt'])
    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_one_filter_applied_to_a_single_model(self, session, operator):
        query = session.query(Bar)
        filters = [{'field': 'count', 'op': operator, 'value': '7'}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 1
        assert result[0].id == 1

    @pytest.mark.parametrize('operator', ['<', 'lt'])
    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_multiple_filters_applied_to_a_single_model(
        self, session, operator
    ):
        query = session.query(Bar)
        filters = [
            {'field': 'count', 'op': operator, 'value': '7'},
            {'field': 'id', 'op': operator, 'value': 1},
        ]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 0


class TestApplyGreaterOrEqualThanFilter(TestFixtures):

    @pytest.mark.parametrize('operator', ['>=', 'ge'])
    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_one_filter_applied_to_a_single_model(self, session, operator):
        query = session.query(Bar)
        filters = [{'field': 'count', 'op': operator, 'value': '5'}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 3
        assert result[0].id == 1
        assert result[1].id == 2
        assert result[2].id == 4

    @pytest.mark.parametrize('operator', ['>=', 'ge'])
    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_multiple_filters_applied_to_a_single_model(
        self, session, operator
    ):
        query = session.query(Bar)
        filters = [
            {'field': 'count', 'op': operator, 'value': '5'},
            {'field': 'id', 'op': operator, 'value': 4},
        ]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 1
        assert result[0].id == 4


class TestApplyLessOrEqualThanFilter(TestFixtures):

    @pytest.mark.parametrize('operator', ['<=', 'le'])
    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_one_filter_applied_to_a_single_model(self, session, operator):
        query = session.query(Bar)
        filters = [{'field': 'count', 'op': operator, 'value': '15'}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 3
        assert result[0].id == 1
        assert result[1].id == 2
        assert result[2].id == 4

    @pytest.mark.parametrize('operator', ['<=', 'le'])
    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_multiple_filters_applied_to_a_single_model(
        self, session, operator
    ):
        query = session.query(Bar)
        filters = [
            {'field': 'count', 'op': operator, 'value': '15'},
            {'field': 'id', 'op': operator, 'value': 1},
        ]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 1
        assert result[0].id == 1


class TestApplyLikeFilter(TestFixtures):

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_one_filter_applied_to_a_single_model(self, session):
        query = session.query(Bar)
        filters = [{'field': 'name', 'op': 'like', 'value': '%me_1'}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 3


class TestApplyInFilter(TestFixtures):

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_field_not_in_value_list(self, session):
        query = session.query(Bar)
        filters = [{'field': 'count', 'op': 'in', 'value': [1, 2, 3]}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 0

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_field_in_value_list(self, session):
        query = session.query(Bar)
        filters = [{'field': 'count', 'op': 'in', 'value': [15, 2, 3]}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 1
        assert result[0].id == 4


class TestApplyNotInFilter(TestFixtures):

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_field_not_in_value_list(self, session):
        query = session.query(Bar)
        filters = [{'field': 'count', 'op': 'not_in', 'value': [1, 2, 3]}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 3
        assert result[0].id == 1
        assert result[1].id == 2
        assert result[2].id == 4

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_field_in_value_list(self, session):
        query = session.query(Bar)
        filters = [{'field': 'count', 'op': 'not_in', 'value': [15, 2, 3]}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2
