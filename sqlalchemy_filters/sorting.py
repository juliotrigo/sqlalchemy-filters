# -*- coding: utf-8 -*-

from .exceptions import BadSortFormat
from .models import Field, get_model_from_spec


SORT_ASCENDING = 'asc'
SORT_DESCENDING = 'desc'


class Sort(object):

    def __init__(self, sort_spec, query):
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

        self.field = Field(model, field_name)
        self.direction = direction

    def format_for_sqlalchemy(self):
        field = self.field.get_sqlalchemy_field()

        if self.direction == SORT_ASCENDING:
            return field.asc()
        elif self.direction == SORT_DESCENDING:
            return field.desc()


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

    sqlalchemy_order_by = [
        Sort(item, query).format_for_sqlalchemy() for item in sort_spec
    ]
    if sqlalchemy_order_by:
        query = query.order_by(*sqlalchemy_order_by)

    return query
