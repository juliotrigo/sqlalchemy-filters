# -*- coding: utf-8 -*-

import datetime

import pytest
from six import string_types
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import select

from sqlalchemy_filters import apply_filters
from sqlalchemy_filters.exceptions import (
    BadFilterFormat, BadSpec, FieldNotFound
)
from sqlalchemy_filters.models import sqlalchemy_version_cmp

from test.models import Foo, Bar, Qux, Corge


ARRAY_NOT_SUPPORTED = (
    "ARRAY type and operators supported only by PostgreSQL"
)


STRING_DATE_TIME_NOT_SUPPORTED = (
    "TODO: String Time / DateTime values currently not working as filters by "
    "SQLite"
)


@pytest.fixture
def multiple_foos_inserted(session, multiple_bars_inserted):
    foo_1 = Foo(id=1, bar_id=1, name='name_1', count=50)
    foo_2 = Foo(id=2, bar_id=2, name='name_2', count=100)
    foo_3 = Foo(id=3, bar_id=3, name='name_1', count=None)
    foo_4 = Foo(id=4, bar_id=4, name='name_4', count=150)
    session.add_all([foo_1, foo_2, foo_3, foo_4])
    session.commit()


@pytest.fixture
def multiple_bars_inserted(session):
    bar_1 = Bar(id=1, name='name_1', count=5)
    bar_2 = Bar(id=2, name='name_2', count=10)
    bar_3 = Bar(id=3, name='name_1', count=None)
    bar_4 = Bar(id=4, name='name_4', count=15)
    session.add_all([bar_1, bar_2, bar_3, bar_4])
    session.commit()


@pytest.fixture
def multiple_quxs_inserted(session):
    qux_1 = Qux(
        id=1, name='name_1', count=5,
        created_at=datetime.date(2016, 7, 12),
        execution_time=datetime.datetime(2016, 7, 12, 1, 5, 9),
        expiration_time=datetime.time(1, 5, 9)
    )
    qux_2 = Qux(
        id=2, name='name_2', count=10,
        created_at=datetime.date(2016, 7, 13),
        execution_time=datetime.datetime(2016, 7, 13, 2, 5, 9),
        expiration_time=datetime.time(2, 5, 9)
    )
    qux_3 = Qux(
        id=3, name='name_1', count=None,
        created_at=None, execution_time=None, expiration_time=None
    )
    qux_4 = Qux(
        id=4, name='name_4', count=15,
        created_at=datetime.date(2016, 7, 14),
        execution_time=datetime.datetime(2016, 7, 14, 3, 5, 9),
        expiration_time=datetime.time(3, 5, 9)
    )
    session.add_all([qux_1, qux_2, qux_3, qux_4])
    session.commit()


@pytest.fixture
def multiple_corges_inserted(session, is_postgresql):
    if is_postgresql:
        corge_1 = Corge(id=1, name='name_1', tags=[])
        corge_2 = Corge(id=2, name='name_2', tags=['foo'])
        corge_3 = Corge(id=3, name='name_3', tags=['foo', 'bar'])
        corge_4 = Corge(id=4, name='name_4', tags=['bar', 'baz'])
        session.add_all([corge_1, corge_2, corge_3, corge_4])
        session.commit()


class TestFiltersNotApplied:

    def test_no_filters_provided(self, session):
        query = session.query(Bar)
        filters = []

        filtered_query = apply_filters(query, filters)

        assert query == filtered_query

    @pytest.mark.parametrize('filter_', ['some text', 1, ''])
    def test_wrong_filters_format(self, session, filter_):
        query = session.query(Bar)
        filters = [filter_]

        with pytest.raises(BadFilterFormat) as err:
            apply_filters(query, filters)

        expected_error = 'Filter spec `{}` should be a dictionary.'.format(
            filter_
        )
        assert expected_error == err.value.args[0]

    def test_invalid_operator(self, session):
        query = session.query(Bar)
        filters = [{'field': 'name', 'op': 'op_not_valid', 'value': 'name_1'}]

        with pytest.raises(BadFilterFormat) as err:
            apply_filters(query, filters)

        assert 'Operator `op_not_valid` not valid.' == err.value.args[0]

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_no_operator_provided(self, session):
        query = session.query(Bar)
        filters = [{'field': 'name', 'value': 'name_1'}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 3

    def test_no_field_provided(self, session):
        query = session.query(Bar)
        filters = [{'op': '==', 'value': 'name_1'}]

        with pytest.raises(BadFilterFormat) as err:
            apply_filters(query, filters)

        expected_error = '`field` is a mandatory filter attribute.'
        assert expected_error == err.value.args[0]

    # TODO: replace this test once we add the option to compare against
    # another field
    def test_no_value_provided(self, session):
        query = session.query(Bar)
        filters = [{'field': 'name', 'op': '==', }]

        with pytest.raises(BadFilterFormat) as err:
            apply_filters(query, filters)

        assert '`value` must be provided.' == err.value.args[0]

    def test_invalid_field(self, session):
        query = session.query(Bar)
        filters = [{'field': 'invalid_field', 'op': '==', 'value': 'name_1'}]

        with pytest.raises(FieldNotFound) as err:
            apply_filters(query, filters)

        expected_error = (
            "Model <class 'test.models.Bar'> has no column `invalid_field`."
        )
        assert expected_error == err.value.args[0]

    @pytest.mark.parametrize('attr_name', [
        'metadata',  # model attribute
        'foos',  # model relationship
    ])
    def test_invalid_field_but_valid_model_attribute(self, session, attr_name):
        query = session.query(Bar)
        filters = [{'field': attr_name, 'op': '==', 'value': 'name_1'}]

        with pytest.raises(FieldNotFound) as err:
            apply_filters(query, filters)

        expected_error = (
            "Model <class 'test.models.Bar'> has no column `{}`.".format(
                attr_name
            )
        )
        assert expected_error == err.value.args[0]


class TestMultipleModels:

    # TODO: multi-model should be tested for each filter type
    @pytest.mark.usefixtures('multiple_bars_inserted')
    @pytest.mark.usefixtures('multiple_quxs_inserted')
    def test_multiple_models(self, session):
        query = session.query(Bar, Qux)
        filters = [
            {'model': 'Bar', 'field': 'name', 'op': '==', 'value': 'name_1'},
            {'model': 'Qux', 'field': 'name', 'op': '==', 'value': 'name_1'},
        ]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 4
        bars, quxs = zip(*result)
        assert set(map(type, bars)) == {Bar}
        assert {bar.id for bar in bars} == {1, 3}
        assert {bar.name for bar in bars} == {"name_1"}
        assert set(map(type, quxs)) == {Qux}
        assert {qux.id for qux in quxs} == {1, 3}
        assert {qux.name for qux in quxs} == {"name_1"}


class TestAutoJoin:

    @pytest.mark.usefixtures('multiple_foos_inserted')
    def test_auto_join(self, session):

        query = session.query(Foo)
        filters = [
            {'field': 'name', 'op': '==', 'value': 'name_1'},
            {'model': 'Bar', 'field': 'count', 'op': 'is_null'},
        ]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 1
        assert result[0].id == 3
        assert result[0].bar_id == 3
        assert result[0].bar.count is None

    @pytest.mark.usefixtures('multiple_foos_inserted')
    def test_do_not_auto_join(self, session):

        query = session.query(Foo)
        filters = [
            {'field': 'name', 'op': '==', 'value': 'name_1'},
            {'model': 'Bar', 'field': 'count', 'op': 'is_null'},
        ]

        with pytest.raises(BadSpec) as exc:
            apply_filters(query, filters, do_auto_join=False)

        assert 'The query does not contain model `Bar`' in str(exc)

    @pytest.mark.usefixtures('multiple_foos_inserted')
    def test_noop_if_query_contains_named_models(self, session):

        query = session.query(Foo).join(Bar)
        filters = [
            {'model': 'Foo', 'field': 'name', 'op': '==', 'value': 'name_1'},
            {'model': 'Bar', 'field': 'count', 'op': 'is_null'},
        ]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 1
        assert result[0].id == 3
        assert result[0].bar_id == 3
        assert result[0].bar.count is None

    @pytest.mark.usefixtures('multiple_foos_inserted')
    def test_auto_join_to_invalid_model(self, session):

        query = session.query(Foo)
        filters = [
            {'field': 'name', 'op': '==', 'value': 'name_1'},
            {'model': 'Bar', 'field': 'count', 'op': 'is_null'},
            {'model': 'Qux', 'field': 'created_at', 'op': 'is_not_null'}
        ]
        with pytest.raises(BadSpec) as err:
            apply_filters(query, filters)

        assert 'The query does not contain model `Qux`.' == err.value.args[0]

    @pytest.mark.usefixtures('multiple_foos_inserted')
    def test_ambiguous_query(self, session):

        query = session.query(Foo).join(Bar)
        filters = [
            {'field': 'name', 'op': '==', 'value': 'name_1'},  # ambiguous
            {'model': 'Bar', 'field': 'count', 'op': 'is_null'},
        ]
        with pytest.raises(BadSpec) as err:
            apply_filters(query, filters)

        assert 'Ambiguous spec. Please specify a model.' == err.value.args[0]

    @pytest.mark.usefixtures('multiple_foos_inserted')
    def test_eager_load(self, session):

        # behaves as if the joinedload wasn't present
        query = session.query(Foo).options(joinedload(Foo.bar))
        filters = [
            {'field': 'name', 'op': '==', 'value': 'name_1'},
            {'model': 'Bar', 'field': 'count', 'op': 'is_null'},
        ]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 1
        assert result[0].id == 3
        assert result[0].bar_id == 3
        assert result[0].bar.count is None


class TestApplyIsNullFilter:

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


class TestApplyIsNotNullFilter:

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


class TestApplyFiltersMultipleTimes:

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


class TestApplyFilterWithoutList:

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_a_single_dict_can_be_supplied_as_filters(self, session):
        query = session.query(Bar)
        filters = {'field': 'name', 'op': '==', 'value': 'name_1'}

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].name == 'name_1'
        assert result[1].id == 3
        assert result[1].name == 'name_1'


class TestApplyFilterOnFieldBasedQuery:

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_apply_filter_on_single_field_query(self, session):
        query = session.query(Bar.id)
        filters = [{'field': 'name', 'op': '==', 'value': 'name_1'}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 2
        assert result[0] == (1,)
        assert result[1] == (3,)

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_apply_filter_on_aggregate_query(self, session):
        query = session.query(func.count(Bar.id))
        filters = [{'field': 'name', 'op': '==', 'value': 'name_1'}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 1
        assert result[0] == (2,)


class TestApplyEqualToFilter:

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

    @pytest.mark.parametrize(
        'filters', [
            [  # filters using `==` in a list
                {'field': 'name', 'op': '==', 'value': 'name_1'},
                {'field': 'id', 'op': '==', 'value': 3}
            ],
            (  # filters using `eq` in a tuple
                {'field': 'name', 'op': 'eq', 'value': 'name_1'},
                {'field': 'id', 'op': 'eq', 'value': 3}
            )
        ]
    )
    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_multiple_filters_applied_to_a_single_model(
        self, session, filters
    ):
        query = session.query(Bar)

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 1
        assert result[0].id == 3
        assert result[0].name == 'name_1'


class TestApplyNotEqualToFilter:

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


class TestApplyGreaterThanFilter:

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


class TestApplyLessThanFilter:

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


class TestApplyGreaterOrEqualThanFilter:

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


class TestApplyLessOrEqualThanFilter:

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


class TestApplyLikeFilter:

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_one_filter_applied_to_a_single_model(self, session):
        query = session.query(Bar)
        filters = [{'field': 'name', 'op': 'like', 'value': '%me_1'}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 3


class TestApplyILikeFilter:

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_one_filter_applied_to_a_single_model(self, session):
        query = session.query(Bar)
        filters = [{'field': 'name', 'op': 'ilike', 'value': '%ME_1'}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 3


class TestApplyNotILikeFilter:

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_one_filter_applied_to_a_single_model(self, session):
        query = session.query(Bar)
        filters = [{'field': 'name', 'op': 'not_ilike', 'value': '%ME_1'}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 2
        assert result[0].id == 2
        assert result[1].id == 4


class TestApplyInFilter:

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


class TestApplyNotInFilter:

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


class TestDateFields:

    @pytest.mark.parametrize(
        'value',
        [
            datetime.date(2016, 7, 14),
            datetime.date(2016, 7, 14).isoformat()
        ]
    )
    @pytest.mark.usefixtures('multiple_quxs_inserted')
    def test_filter_date_equality(self, session, value):
        query = session.query(Qux)
        filters = [{
            'field': 'created_at',
            'op': '==',
            'value': value
        }]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 1
        assert result[0].created_at == datetime.date(2016, 7, 14)

    @pytest.mark.parametrize(
        'value',
        [
            datetime.date(2016, 7, 13),
            datetime.date(2016, 7, 13).isoformat()
        ]
    )
    @pytest.mark.usefixtures('multiple_quxs_inserted')
    def test_filter_multiple_dates(self, session, value):
        query = session.query(Qux)
        filters = [{
            'field': 'created_at',
            'op': '>=',
            'value': value
        }]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 2
        assert result[0].created_at == datetime.date(2016, 7, 13)
        assert result[1].created_at == datetime.date(2016, 7, 14)

    @pytest.mark.usefixtures('multiple_quxs_inserted')
    def test_null_date(self, session):
        query = session.query(Qux)
        filters = [{'field': 'created_at', 'op': 'is_null'}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 1
        assert result[0].created_at is None


class TestTimeFields:

    @pytest.mark.parametrize(
        'value',
        [
            datetime.time(3, 5, 9),
            datetime.time(3, 5, 9).isoformat()  # '03:05:09'
        ]
    )
    @pytest.mark.usefixtures('multiple_quxs_inserted')
    def test_filter_time_equality(self, session, is_sqlite, value):
        if isinstance(value, string_types) and is_sqlite:
            pytest.skip(STRING_DATE_TIME_NOT_SUPPORTED)

        query = session.query(Qux)
        filters = [{'field': 'expiration_time', 'op': '==', 'value': value}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 1
        assert result[0].expiration_time == datetime.time(3, 5, 9)

    @pytest.mark.parametrize(
        'value',
        [
            datetime.time(2, 5, 9),
            datetime.time(2, 5, 9).isoformat()  # '02:05:09'
        ]
    )
    @pytest.mark.usefixtures('multiple_quxs_inserted')
    def test_filter_multiple_times(self, session, is_sqlite, value):
        if isinstance(value, string_types) and is_sqlite:
            pytest.skip(STRING_DATE_TIME_NOT_SUPPORTED)

        query = session.query(Qux)
        filters = [{
            'field': 'expiration_time',
            'op': '>=',
            'value': value
        }]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 2
        assert result[0].expiration_time == datetime.time(2, 5, 9)
        assert result[1].expiration_time == datetime.time(3, 5, 9)

    @pytest.mark.usefixtures('multiple_quxs_inserted')
    def test_null_time(self, session):
        query = session.query(Qux)
        filters = [{'field': 'expiration_time', 'op': 'is_null'}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 1
        assert result[0].expiration_time is None


class TestDateTimeFields:

    @pytest.mark.parametrize(
        'value',
        [
            datetime.datetime(2016, 7, 14, 3, 5, 9),
            # '2016-07-14T03:05:09'
            datetime.datetime(2016, 7, 14, 3, 5, 9).isoformat()
        ]
    )
    @pytest.mark.usefixtures('multiple_quxs_inserted')
    def test_filter_datetime_equality(self, session, is_sqlite, value):
        if isinstance(value, string_types) and is_sqlite:
            pytest.skip(STRING_DATE_TIME_NOT_SUPPORTED)

        query = session.query(Qux)
        filters = [{
            'field': 'execution_time',
            'op': '==',
            'value': value
        }]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 1
        assert result[0].execution_time == datetime.datetime(
            2016, 7, 14, 3, 5, 9
        )

    @pytest.mark.parametrize(
        'value',
        [
            datetime.datetime(2016, 7, 13, 2, 5, 9),
            # '2016-07-13T02:05:09'
            datetime.datetime(2016, 7, 13, 2, 5, 9).isoformat()
        ]
    )
    @pytest.mark.usefixtures('multiple_quxs_inserted')
    def test_filter_multiple_datetimes(self, session, is_sqlite, value):
        if isinstance(value, string_types) and is_sqlite:
            pytest.skip(STRING_DATE_TIME_NOT_SUPPORTED)

        query = session.query(Qux)
        filters = [{
            'field': 'execution_time',
            'op': '>=',
            'value': value
        }]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 2
        assert result[0].execution_time == datetime.datetime(
            2016, 7, 13, 2, 5, 9
        )
        assert result[1].execution_time == datetime.datetime(
            2016, 7, 14, 3, 5, 9
        )

    @pytest.mark.usefixtures('multiple_quxs_inserted')
    def test_null_datetime(self, session):
        query = session.query(Qux)
        filters = [{'field': 'execution_time', 'op': 'is_null'}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 1
        assert result[0].execution_time is None


class TestApplyBooleanFunctions:

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_or(self, session):
        query = session.query(Bar)
        filters = [
            {'or': [
                {'field': 'id', 'op': '==', 'value': 1},
                {'field': 'id', 'op': '==', 'value': 3},
            ]},
        ]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 3

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_or_with_one_arg(self, session):
        query = session.query(Bar)
        filters = [
            {'or': [
                {'field': 'id', 'op': '==', 'value': 1},
            ]},
        ]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 1
        assert result[0].id == 1

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_or_with_three_args(self, session):
        query = session.query(Bar)
        filters = [
            {'or': [
                {'field': 'id', 'op': '==', 'value': 1},
                {'field': 'id', 'op': '==', 'value': 3},
                {'field': 'id', 'op': '==', 'value': 4},
            ]},
        ]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 3
        assert result[0].id == 1
        assert result[1].id == 3
        assert result[2].id == 4

    @pytest.mark.parametrize(
        ('or_args', 'expected_error'), [
            (
                [],
                '`or` must have one or more arguments'
            ),
            (
                {},
                '`or` value must be an iterable across the function arguments'
            ),
            (
                'hello',
                '`or` value must be an iterable across the function arguments'
            ),
        ]
    )
    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_or_with_bad_format(self, session, or_args, expected_error):
        query = session.query(Bar)
        filters = [{'or': or_args}]

        with pytest.raises(BadFilterFormat) as exc:
            apply_filters(query, filters)

        assert expected_error in str(exc)

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_and(self, session):
        query = session.query(Bar)
        filters = [
            {'and': [
                {'field': 'id', 'op': '<=', 'value': 2},
                {'field': 'count', 'op': '>=', 'value': 6},
            ]},
        ]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 1
        assert result[0].id == 2

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_and_with_one_arg(self, session):
        query = session.query(Bar)
        filters = [
            {'and': [
                {'field': 'id', 'op': '==', 'value': 3},
            ]},
        ]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 1
        assert result[0].id == 3

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_and_with_three_args(self, session):
        query = session.query(Bar)
        filters = [
            {'and': [
                {'field': 'id', 'op': '<=', 'value': 3},
                {'field': 'name', 'op': '==', 'value': 'name_1'},
                {'field': 'count', 'op': 'is_not_null'},
            ]},
        ]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 1
        assert result[0].id == 1

    @pytest.mark.parametrize(
        ('and_args', 'expected_error'), [
            (
                [],
                '`and` must have one or more arguments'
            ),
            (
                {},
                '`and` value must be an iterable across the function arguments'
            ),
            (
                'hello',
                '`and` value must be an iterable across the function arguments'
            ),
        ]
    )
    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_and_with_bad_format(self, session, and_args, expected_error):
        query = session.query(Bar)
        filters = [{'and': and_args}]

        with pytest.raises(BadFilterFormat) as exc:
            apply_filters(query, filters)

        assert expected_error in str(exc)

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_not(self, session):
        query = session.query(Bar)
        filters = [
            {'not': [
                {'field': 'id', 'op': '==', 'value': 3},
            ]},
        ]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 3
        assert result[0].id == 1
        assert result[1].id == 2
        assert result[2].id == 4

    @pytest.mark.parametrize(
        ('not_args', 'expected_error'), [
            (
                [{'field': 'id', 'op': '==', 'value': 1},
                    {'field': 'id', 'op': '==', 'value': 2}],
                '`not` must have one argument'
            ),
            (
                [],
                '`not` must have one argument'
            ),
            (
                {},
                '`not` value must be an iterable across the function arguments'
            ),
            (
                'hello',
                '`not` value must be an iterable across the function arguments'
            ),
        ]
    )
    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_not_with_bad_format(self, session, not_args, expected_error):
        query = session.query(Bar)
        filters = [{'not': not_args}]

        with pytest.raises(BadFilterFormat) as exc:
            apply_filters(query, filters)

        assert expected_error in str(exc)

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_complex(self, session):
        query = session.query(Bar)
        filters = [
            {
                'and': [
                    {
                        'or': [
                            {'field': 'id', 'op': '==', 'value': 2},
                            {'field': 'id', 'op': '==', 'value': 3},
                        ]
                    },
                    {
                        'not': [
                            {'field': 'name', 'op': '==', 'value': 'name_2'}
                        ]
                    },
                ],
            }
        ]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 1
        assert result[0].id == 3

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_complex_using_tuples(self, session):
        query = session.query(Bar)
        filters = (
            {
                'and': (
                    {
                        'or': (
                            {'field': 'id', 'op': '==', 'value': 2},
                            {'field': 'id', 'op': '==', 'value': 3},
                        )
                    },
                    {
                        'not': (
                            {'field': 'name', 'op': '==', 'value': 'name_2'},
                        )
                    },
                ),
            },
        )

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 1
        assert result[0].id == 3


class TestApplyArrayFilters:

    @pytest.mark.usefixtures('multiple_corges_inserted')
    def test_any_value_in_array(self, session, is_postgresql):
        if not is_postgresql:
            pytest.skip(ARRAY_NOT_SUPPORTED)

        query = session.query(Corge)
        filters = [{'field': 'tags', 'op': 'any', 'value': 'foo'}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 2
        assert result[0].id == 2
        assert result[1].id == 3

    @pytest.mark.usefixtures('multiple_corges_inserted')
    def test_not_any_values_in_array(self, session, is_postgresql):
        if not is_postgresql:
            pytest.skip(ARRAY_NOT_SUPPORTED)

        query = session.query(Corge)
        filters = [{'field': 'tags', 'op': 'not_any', 'value': 'foo'}]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 4


class TestHybridAttributes:

    @pytest.mark.usefixtures('multiple_bars_inserted')
    @pytest.mark.parametrize(
        ('field, expected_error'),
        [
            ('foos', "Model <class 'test.models.Bar'> has no column `foos`."),
            (
                '__mapper__',
                "Model <class 'test.models.Bar'> has no column `__mapper__`.",
            ),
            (
                'not_valid',
                "Model <class 'test.models.Bar'> has no column `not_valid`.",
            ),
        ]
    )
    def test_orm_descriptors_not_valid_hybrid_attributes(
        self, session, field, expected_error
    ):
        query = session.query(Bar)
        filters = [
            {
                'model': 'Bar',
                'field': field,
                'op': '==',
                'value': 100
            }
        ]
        with pytest.raises(FieldNotFound) as exc:
            apply_filters(query, filters)

        assert expected_error in str(exc)

    @pytest.mark.usefixtures('multiple_bars_inserted')
    @pytest.mark.usefixtures('multiple_quxs_inserted')
    def test_filter_by_hybrid_properties(self, session):
        query = session.query(Bar, Qux)
        filters = [
            {
                'model': 'Bar',
                'field': 'count_square',
                'op': '==',
                'value': 100
            },
            {
                'model': 'Qux',
                'field': 'count_square',
                'op': '>=',
                'value': 26
            },
        ]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 2
        bars, quxs = zip(*result)

        assert set(map(type, bars)) == {Bar}
        assert {bar.id for bar in bars} == {2}
        assert {bar.count_square for bar in bars} == {100}

        assert set(map(type, quxs)) == {Qux}
        assert {qux.id for qux in quxs} == {2, 4}
        assert {qux.count_square for qux in quxs} == {100, 225}

    @pytest.mark.usefixtures('multiple_bars_inserted')
    @pytest.mark.usefixtures('multiple_quxs_inserted')
    def test_filter_by_hybrid_methods(self, session):
        query = session.query(Bar, Qux)
        filters = [
            {
                'model': 'Bar',
                'field': 'three_times_count',
                'op': '==',
                'value': 30
            },
            {
                'model': 'Qux',
                'field': 'three_times_count',
                'op': '>=',
                'value': 31
            },
        ]

        filtered_query = apply_filters(query, filters)
        result = filtered_query.all()

        assert len(result) == 1
        bars, quxs = zip(*result)

        assert set(map(type, bars)) == {Bar}
        assert {bar.id for bar in bars} == {2}
        assert {bar.three_times_count() for bar in bars} == {30}

        assert set(map(type, quxs)) == {Qux}
        assert {qux.id for qux in quxs} == {4}
        assert {qux.three_times_count() for qux in quxs} == {45}


class TestSelectObject:

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_filter_on_select(self, session):
        if sqlalchemy_version_cmp('<', '1.4'):
            pytest.skip("Sqlalchemy select style 2.0 not supported")

        query = select(Bar)
        filters = {'field': 'name', 'op': '==', 'value': 'name_2'}

        query = apply_filters(query, filters)
        result = session.execute(query).fetchall()

        assert len(result) == 1
