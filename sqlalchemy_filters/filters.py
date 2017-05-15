# -*- coding: utf-8 -*-

from inspect import signature
from sqlalchemy import and_, or_, not_

from .exceptions import BadFilterFormat, BadQuery
from .models import Field, get_query_models


BOOLEAN_FUNCTIONS = [
    ('or', or_, False),
    ('and', and_, False),
    ('not', not_, True),
]
"""
Sqlalchemy boolean functions that can be parsed from the filter definition.

Each entry is a tuple of (`key`, `sqlalchemy-function`, `only_one_argument`)
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

    def __init__(self, operator):
        if operator not in self.OPERATORS:
            raise BadFilterFormat('Operator `{}` not valid.'.format(operator))

        self.operator = operator
        self.function = self.OPERATORS[operator]
        self.arity = len(signature(self.function).parameters)


class Filter(object):

    def __init__(self, filter_, models):
        try:
            field_name = filter_['field']
            op = filter_['op']
        except KeyError:
            raise BadFilterFormat(
                '`field` and `op` are mandatory filter attributes.'
            )
        except TypeError:
            raise BadFilterFormat(
                'Filter `{}` should be a dictionary.'.format(filter_)
            )

        self.field = Field(models, field_name)
        self.operator = Operator(op)
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


def build_sqlalchemy_filters(filterdef, models):
    """ Recursively parse the `filterdef` into sqlalchemy filter arguments """

    if isinstance(filterdef, (list, tuple)):
        return [build_sqlalchemy_filters(item, models) for item in filterdef]

    if isinstance(filterdef, dict):
        # Check if filterdef defines a boolean function.
        for key, boolean_fn, only_one_arg in BOOLEAN_FUNCTIONS:
            if key in filterdef:
                # The filterdef is for a boolean-function
                # Get the function argument definitions.
                fn_args = filterdef[key]
                # validate the arguments
                if not isinstance(fn_args, (list, tuple)):
                    raise BadFilterFormat(
                        '`{}` value must be a list or tuple'.format(key)
                    )
                if only_one_arg and len(fn_args) != 1:
                    raise BadFilterFormat(
                        '`{}` value must be a list or tuple of '
                        'length 1'.format(key)
                    )
                if not only_one_arg and len(fn_args) <= 1:
                    raise BadFilterFormat(
                        '`{}` value must be a list or tuple with '
                        'length > 1'.format(key)
                    )

                return boolean_fn(*build_sqlalchemy_filters(fn_args, models))

    return Filter(filterdef, models).format_for_sqlalchemy()


def apply_filters(query, filters):
    """Apply filters to a SQLAlchemy query.

    :param query:
        A :class:`sqlalchemy.orm.Query` instance.

    :param filters:
        A list (or tuple) of dictionaries, where each one of them includes
        the necesary information to create a filter to be applied to the
        query.

    :returns:
        The :class:`sqlalchemy.orm.Query` instance after all the filters
        have been applied.
    """
    models = get_query_models(query)
    if not models:
        raise BadQuery('The query does not contain any models.')

    if not isinstance(filters, (list, tuple)):
        raise BadFilterFormat('`filters` must be a list or tuple')

    sqlalchemy_filters = build_sqlalchemy_filters(filters, models)

    if sqlalchemy_filters:
        query = query.filter(*sqlalchemy_filters)

    return query
