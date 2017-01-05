# -*- coding: utf-8 -*-

from collections import namedtuple

import pytest

from sqlalchemy_filters import apply_pagination
from sqlalchemy_filters.exceptions import InvalidPage
from test import error_value
from test.models import Bar


Pagination = namedtuple(
    'Pagination', ['page_number', 'page_size', 'num_pages', 'total_results']
)


class TestPaginationFixtures(object):

    @pytest.fixture
    def multiple_bars_inserted(self, session):
        bar_1 = Bar(id=1, name='name_1', count=5)
        bar_2 = Bar(id=2, name='name_2', count=10)
        bar_3 = Bar(id=3, name='name_1', count=None)
        bar_4 = Bar(id=4, name='name_4', count=15)
        bar_5 = Bar(id=5, name='name_5', count=17)
        bar_6 = Bar(id=6, name='name_5', count=17)
        bar_7 = Bar(id=7, name='name_7', count=None)
        bar_8 = Bar(id=8, name='name_8', count=18)
        session.add_all(
            [bar_1, bar_2, bar_3, bar_4, bar_5, bar_6, bar_7, bar_8]
        )
        session.commit()


class TestWrongPagination(TestPaginationFixtures):

    @pytest.mark.parametrize(
        'page_number, page_size',
        [
            (-2, None), (-2, 0), (-2, 1), (-2, 2),
            (-1, None), (-1, 0), (-1, 1), (-1, 2),
            (0, None), (0, 0), (0, 1), (-0, 2),
        ]
    )
    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_wrong_page_number(self, session, page_number, page_size):
        query = session.query(Bar)

        with pytest.raises(InvalidPage) as err:
            apply_pagination(query, page_number, page_size)

        expected_error = 'Page number should be positive: {}'.format(
            page_number
        )
        assert error_value(err) == expected_error

    @pytest.mark.parametrize(
        'page_number, page_size',
        [
            (-2, None), (-2, 0), (-2, 1), (-2, 2),
            (-1, None), (-1, 0), (-1, 1), (-1, 2),
            (0, None), (0, 0), (0, 1), (-0, 2),
        ]
    )
    def test_wrong_page_number_with_no_results(
        self, session, page_number, page_size
    ):
        query = session.query(Bar)

        with pytest.raises(InvalidPage) as err:
            apply_pagination(query, page_number, page_size)

        expected_error = 'Page number should be positive: {}'.format(
            page_number
        )
        assert error_value(err) == expected_error

    @pytest.mark.parametrize(
        'page_number, page_size',
        [
            (None, -2), (-1, -2), (0, -2), (1, -2), (2, -2),
            (None, -1), (-1, -1), (0, -1), (1, -1), (2, -1),
        ]
    )
    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_wrong_page_size(self, session, page_number, page_size):
        query = session.query(Bar)

        with pytest.raises(InvalidPage) as err:
            apply_pagination(query, page_number, page_size)

        expected_error = 'Page size should not be negative: {}'.format(
            page_size
        )
        assert error_value(err) == expected_error


class TestNoPaginationProvided(TestPaginationFixtures):

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_no_pagination_info_provided(self, session):
        query = session.query(Bar)
        page_size = None
        page_number = None

        paginated_query, pagination = apply_pagination(
            query, page_number, page_size
        )

        assert query == paginated_query
        assert Pagination(
            page_number=1, page_size=8, num_pages=1, total_results=8
        ) == pagination

        result = paginated_query.all()

        assert len(result) == 8
        for i in range(8):
            assert result[i].id == i + 1


class TestNoPageNumberProvided(TestPaginationFixtures):

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_page_size_greater_than_total_records(self, session):
        query = session.query(Bar)
        page_size = 5000
        page_number = None

        paginated_query, pagination = apply_pagination(
            query, page_number, page_size
        )

        assert query != paginated_query
        assert Pagination(
            page_number=1, page_size=8, num_pages=1, total_results=8
        ) == pagination

        result = paginated_query.all()

        assert len(result) == 8
        for i in range(8):
            assert result[i].id == i + 1

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_page_size_provided(self, session):
        query = session.query(Bar)
        page_size = 2
        page_number = None

        paginated_query, pagination = apply_pagination(
            query, page_number, page_size
        )

        assert query != paginated_query
        assert Pagination(
            page_number=1, page_size=2, num_pages=4, total_results=8
        ) == pagination

        result = paginated_query.all()

        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2


class TestNoPageSizeProvided(TestPaginationFixtures):

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_first_page(self, session):
        query = session.query(Bar)
        page_size = None
        page_number = 1

        paginated_query, pagination = apply_pagination(
            query, page_number, page_size
        )

        assert query != paginated_query
        assert Pagination(
            page_number=1, page_size=8, num_pages=1, total_results=8
        ) == pagination

        result = paginated_query.all()

        assert len(result) == 8
        for i in range(8):
            assert result[i].id == i + 1

    @pytest.mark.parametrize('page_number', [2, 3, 4])
    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_page_number_greater_than_one(self, session, page_number):
        query = session.query(Bar)
        page_size = None

        paginated_query, pagination = apply_pagination(
            query, page_number, page_size
        )

        assert query != paginated_query
        assert Pagination(
            page_number=page_number, page_size=8, num_pages=1, total_results=8
        ) == pagination

        result = paginated_query.all()

        assert len(result) == 0


class TestApplyPagination(TestPaginationFixtures):

    @pytest.mark.parametrize('page_number', [1, 2, 3])
    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_page_size_zero(self, session, page_number):
        query = session.query(Bar)
        page_size = 0

        paginated_query, pagination = apply_pagination(
            query, page_number, page_size
        )

        assert query != paginated_query
        assert Pagination(
            page_number=page_number, page_size=0, num_pages=0, total_results=8
        ) == pagination

        result = paginated_query.all()

        assert len(result) == 0

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_page_size_zero_and_no_page_number_provided(self, session):
        query = session.query(Bar)
        page_size = 0
        page_number = None

        paginated_query, pagination = apply_pagination(
            query, page_number, page_size
        )

        assert query != paginated_query
        assert Pagination(
            page_number=1, page_size=0, num_pages=0, total_results=8
        ) == pagination

        result = paginated_query.all()

        assert len(result) == 0

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_page_number_and_page_size_provided(self, session):
        query = session.query(Bar)
        page_size = 2
        page_number = 3

        paginated_query, pagination = apply_pagination(
            query, page_number, page_size
        )
        assert query != paginated_query
        assert Pagination(
            page_number=3, page_size=2, num_pages=4, total_results=8
        ) == pagination

        result = paginated_query.all()

        assert len(result) == 2
        assert result[0].id == 5
        assert result[1].id == 6

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_get_individual_record(self, session):
        query = session.query(Bar)
        page_size = 1
        page_number = 5

        paginated_query, pagination = apply_pagination(
            query, page_number, page_size
        )

        assert query != paginated_query
        assert Pagination(
            page_number=5, page_size=1, num_pages=8, total_results=8
        ) == pagination

        result = paginated_query.all()

        assert len(result) == 1
        assert result[0].id == 5

    @pytest.mark.parametrize('page_number', [5, 6, 7])
    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_page_number_greater_than_number_of_pages(
        self, session, page_number
    ):
        query = session.query(Bar)
        page_size = 2

        paginated_query, pagination = apply_pagination(
            query, page_number, page_size
        )

        assert query != paginated_query
        assert Pagination(
            page_number=page_number, page_size=2, num_pages=4, total_results=8
        ) == pagination

        result = paginated_query.all()

        assert len(result) == 0

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_last_complete_page(self, session):
        query = session.query(Bar)
        page_size = 2
        page_number = 4

        paginated_query, pagination = apply_pagination(
            query, page_number, page_size
        )

        assert query != paginated_query
        assert Pagination(
            page_number=4, page_size=2, num_pages=4, total_results=8
        ) == pagination

        result = paginated_query.all()

        assert len(result) == 2
        assert result[0].id == 7
        assert result[1].id == 8

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_last_incomplete_page(self, session):
        query = session.query(Bar)
        page_size = 5
        page_number = 2

        paginated_query, pagination = apply_pagination(
            query, page_number, page_size
        )

        assert query != paginated_query
        assert Pagination(
            page_number=2, page_size=5, num_pages=2, total_results=8
        ) == pagination

        result = paginated_query.all()

        assert len(result) == 3
        assert result[0].id == 6
        assert result[1].id == 7
        assert result[2].id == 8

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_get_first_page(self, session):
        query = session.query(Bar)
        page_size = 2
        page_number = 1

        paginated_query, pagination = apply_pagination(
            query, page_number, page_size
        )

        assert query != paginated_query
        assert Pagination(
            page_number=1, page_size=2, num_pages=4, total_results=8
        ) == pagination

        result = paginated_query.all()

        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2


class TestQueryWithNoResults:

    def test_page_size_and_page_number_provided(self, session):
        query = session.query(Bar)
        page_size = 2
        page_number = 1

        paginated_query, pagination = apply_pagination(
            query, page_number, page_size
        )

        assert query != paginated_query
        assert Pagination(
            page_number=1, page_size=2, num_pages=0, total_results=0
        ) == pagination

        result = paginated_query.all()

        assert len(result) == 0
