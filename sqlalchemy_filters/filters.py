# -*- coding: utf-8 -*-
from collections import Iterable, namedtuple
from inspect import signature
from itertools import chain

from six import string_types
from sqlalchemy import and_, or_, not_

from .exceptions import BadFilterFormat, BadQuery
from .models import Field, get_query_models


BooleanFunction = namedtuple(
    'BooleanFunction', ('key', 'sqlalchemy_fn', 'only_one_arg')
)
BOOLEAN_FUNCTIONS = [
    BooleanFunction('or', or_, False),
    BooleanFunction('and', and_, False),
    BooleanFunction('not', not_, True),
]
"""
Sqlalchemy boolean functions that can be parsed from the filter definition.
"""


class Operator(object):

    OPERATORS = {
        'is_null': lambda f: f.is_(None),
        'is_not_null': lambda f: f.isnot(None),
        '==': lambda f, a: f == a,
        'eq': lambda f, a: f == a,
        '!=': lambda f, a: f != a,
        'ne': lambda f, a: f != a,
        '>': lambda f, a: f > a,
        'gt': lambda f, a: f > a,
        '<': lambda f, a: f < a,
        'lt': lambda f, a: f < a,
        '>=': lambda f, a: f >= a,
        'ge': lambda f, a: f >= a,
        '<=': lambda f, a: f <= a,
        'le': lambda f, a: f <= a,
        'like': lambda f, a: f.like(a),
        'in': lambda f, a: f.in_(a),
        'not_in': lambda f, a: ~f.in_(a),
    }

    def __init__(self, operator=None):
        if not operator:
            operator = '=='

        if operator not in self.OPERATORS:
            raise BadFilterFormat('Operator `{}` not valid.'.format(operator))

        self.operator = operator
        self.function = self.OPERATORS[operator]
        self.arity = len(signature(self.function).parameters)


class Filter(object):

    def __init__(self, filter_, models):
        try:
            field_name = filter_['field']
        except KeyError:
            raise BadFilterFormat('`field` is a mandatory filter attribute.')
        except TypeError:
            raise BadFilterFormat(
                'Filter `{}` should be a dictionary.'.format(filter_)
            )

        self.field = Field(models, field_name)
        self.operator = Operator(filter_.get('op'))
        self.value = filter_.get('value')
        self.value_present = True if 'value' in filter_ else False

        if not self.value_present and self.operator.arity == 2:
            raise BadFilterFormat('`value` must be provided.')

    def format_for_sqlalchemy(self):
        function = self.operator.function
        arity = self.operator.arity
        field = self.field.get_sqlalchemy_field()

        if arity == 1:
            return function(field)

        if arity == 2:
            return function(field, self.value)


def _build_sqlalchemy_filters(filterdef, models):
    """ Recursively parse the `filterdef` into sqlalchemy filter arguments """

    if _is_iterable_filter(filterdef):
        return list(chain.from_iterable(
            _build_sqlalchemy_filters(item, models) for item in filterdef
        ))

    if isinstance(filterdef, dict):
        # Check if filterdef defines a boolean function.
        for boolean_function in BOOLEAN_FUNCTIONS:
            if boolean_function.key in filterdef:
                # The filterdef is for a boolean-function
                # Get the function argument definitions and validate
                fn_args = filterdef[boolean_function.key]

                if not _is_iterable_filter(fn_args):
                    raise BadFilterFormat(
                        '`{}` value must be an iterable across the function '
                        'arguments'.format(boolean_function.key)
                    )
                if boolean_function.only_one_arg and len(fn_args) != 1:
                    raise BadFilterFormat(
                        '`{}` must have one argument'.format(
                            boolean_function.key
                        )
                    )
                if not boolean_function.only_one_arg and len(fn_args) < 1:
                    raise BadFilterFormat(
                        '`{}` must have one or more arguments'.format(
                            boolean_function.key
                        )
                    )
                return [
                    boolean_function.sqlalchemy_fn(
                        *_build_sqlalchemy_filters(fn_args, models)
                    )
                ]

    return [Filter(filterdef, models).format_for_sqlalchemy()]


def _is_iterable_filter(filterdef):
    return (
        isinstance(filterdef, Iterable) and
        not isinstance(filterdef, (string_types, dict))
    )


def apply_filters(query, filters):
    """Apply filters to a SQLAlchemy query.

    :param query:
        A :class:`sqlalchemy.orm.Query` instance.

    :param filters:
        A dict or an iterable of dicts, where each one includes
        the necesary information to create a filter to be applied to the
        query.

    :returns:
        The :class:`sqlalchemy.orm.Query` instance after all the filters
        have been applied.
    """
    models = get_query_models(query)
    if not models:
        raise BadQuery('The query does not contain any models.')

    sqlalchemy_filters = _build_sqlalchemy_filters(filters, models)

    if sqlalchemy_filters:
        query = query.filter(*sqlalchemy_filters)

    return query
