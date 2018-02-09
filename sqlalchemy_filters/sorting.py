# -*- coding: utf-8 -*-

from .exceptions import BadSortFormat
from .models import Field, get_model_from_spec


SORT_ASCENDING = 'asc'
SORT_DESCENDING = 'desc'


class Sort(object):

    def __init__(self, sort_spec):
        self.sort_spec = sort_spec

    def format_for_sqlalchemy(self, query):
        sort_spec = self.sort_spec

        try:
            field_name = sort_spec['field']
            direction = sort_spec['direction']
        except KeyError:
            raise BadSortFormat(
                '`field` and `direction` are mandatory attributes.'
            )
        except TypeError:
            raise BadSortFormat(
                'Sort spec `{}` should be a dictionary.'.format(sort_spec)
            )

        if direction not in [SORT_ASCENDING, SORT_DESCENDING]:
            raise BadSortFormat('Direction `{}` not valid.'.format(direction))

        model = get_model_from_spec(sort_spec, query)

        field = Field(model, field_name)
        sqlalchemy_field = field.get_sqlalchemy_field()

        if direction == SORT_ASCENDING:
            return sqlalchemy_field.asc()
        elif direction == SORT_DESCENDING:
            return sqlalchemy_field.desc()


def apply_sort(query, sort_spec):
    """Apply sorting to a :class:`sqlalchemy.orm.Query` instance.

    :param sort_spec:
        A list of dictionaries, where each one of them includes
        the necesary information to order the elements of the query.

        Example::

            sort_spec = [
                {'model': 'Foo', 'field': 'name', 'direction': 'asc'},
                {'model': 'Bar', 'field': 'id', 'direction': 'desc'},
            ]

        If the query being modified refers to a single model, the `model` key
        may be omitted from the sort spec.

    :returns:
        The :class:`sqlalchemy.orm.Query` instance after the provided
        sorting has been applied.
    """
    if isinstance(sort_spec, dict):
        sort_spec = [sort_spec]

    sorts = [Sort(item) for item in sort_spec]
    sqlalchemy_sorts = [
        sort.format_for_sqlalchemy(query) for sort in sorts
    ]

    if sqlalchemy_sorts:
        query = query.order_by(*sqlalchemy_sorts)

    return query
