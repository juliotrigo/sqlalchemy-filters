# -*- coding: utf-8 -*-

from .exceptions import BadQuery, BadSortFormat
from .models import Field, get_query_models


SORT_ASCENDING = 'asc'
SORT_DESCENDING = 'desc'


class Sort(object):

    def __init__(self, sort, models):
        try:
            field_name = sort['field']
            direction = sort['direction']
        except KeyError:
            raise BadSortFormat(
                '`field` and `direction` are mandatory attributes.'
            )
        except TypeError:
            raise BadSortFormat(
                'Sort `{}` should be a dictionary.'.format(sort)
            )

        if direction not in [SORT_ASCENDING, SORT_DESCENDING]:
            raise BadSortFormat('Direction `{}` not valid.'.format(direction))

        self.field = Field(models, field_name)
        self.direction = direction

    def format_for_sqlalchemy(self):
        field = self.field.get_sqlalchemy_field()

        if self.direction == SORT_ASCENDING:
            return field.asc()
        elif self.direction == SORT_DESCENDING:
            return field.desc()


def apply_sort(query, order_by):
    """Apply sorting to a :class:`sqlalchemy.orm.Query` instance.

    :param order_by:
        A list of dictionaries, where each one of them includes
        the necesary information to order the elements of the query.

        Example::

            order_by = [
                {'field': 'name', 'direction': 'asc'},
                {'field': 'id', 'direction': 'desc'},
            ]

    :returns:
        The :class:`sqlalchemy.orm.Query` instance after the provided
        sorting has been applied.
    """
    models = get_query_models(query)
    if not models:
        raise BadQuery('The query does not contain any models.')

    sqlalchemy_order_by = [
        Sort(sort, models).format_for_sqlalchemy() for sort in order_by
    ]
    if sqlalchemy_order_by:
        query = query.order_by(*sqlalchemy_order_by)

    return query
