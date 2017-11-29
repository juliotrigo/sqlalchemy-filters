# -*- coding: utf-8 -*-
from collections import Iterable, namedtuple
from inspect import signature
from itertools import chain

from six import string_types
from sqlalchemy import and_, or_, not_

from .exceptions import BadFilterFormat
from .models import Field, get_model_from_spec


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

    def __init__(self, filter_spec, query):
        try:
            field_name = filter_spec['field']
        except KeyError:
            raise BadFilterFormat('`field` is a mandatory filter attribute.')
        except TypeError:
            raise BadFilterFormat(
                'Filter spec `{}` should be a dictionary.'.format(filter_spec)
            )

        model = get_model_from_spec(filter_spec, query)

        self.field = Field(model, field_name)
        self.operator = Operator(filter_spec.get('op'))
        self.value = filter_spec.get('value')
        self.value_present = True if 'value' in filter_spec else False

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


def _is_iterable_filter(filter_spec):
    """ `filter_spec` may be a list of nested filter specs, or a dict.
    """
    return (
        isinstance(filter_spec, Iterable) and
        not isinstance(filter_spec, (string_types, dict))
    )


def _build_sqlalchemy_filters(filter_spec, query):
    """ Recursively process `filter_spec` """

    if _is_iterable_filter(filter_spec):
        return list(chain.from_iterable(
            _build_sqlalchemy_filters(item, query) for item in filter_spec
        ))

    if isinstance(filter_spec, dict):
        # Check if filter spec defines a boolean function.
        for boolean_function in BOOLEAN_FUNCTIONS:
            if boolean_function.key in filter_spec:
                # The filter spec is for a boolean-function
                # Get the function argument definitions and validate
                fn_args = filter_spec[boolean_function.key]

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
                        *_build_sqlalchemy_filters(fn_args, query)
                    )
                ]

    return [Filter(filter_spec, query).format_for_sqlalchemy()]


def apply_filters(query, filter_spec):
    """Apply filters to a SQLAlchemy query.

    :param query:
        A :class:`sqlalchemy.orm.Query` instance.

    :param filter_spec:
        A dict or an iterable of dicts, where each one includes
        the necesary information to create a filter to be applied to the
        query.

        Example::

            filter_spec = [
                {'model': 'Foo', 'field': 'name', 'op': '==', 'value': 'foo'},
            ]

        If the query being modified refers to a single model, the `model` key
        may be omitted from the filter spec.

        Filters may be combined using boolean functions.

        Example:

            filter_spec = {
                'or': [
                    {'model': 'Foo', 'field': 'id', 'op': '==', 'value': '1'},
                    {'model': 'Bar', 'field': 'id', 'op': '==', 'value': '2'},
                ]
            }

    :returns:
        The :class:`sqlalchemy.orm.Query` instance after all the filters
        have been applied.
    """
    sqlalchemy_filters = _build_sqlalchemy_filters(filter_spec, query)

    if sqlalchemy_filters:
        query = query.filter(*sqlalchemy_filters)

    return query
