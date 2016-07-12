# -*- coding: utf-8 -*-

from .exceptions import (
    BadFilterFormat,
    InvalidOperator,
    ModelNotFound,
    ModelFieldNotFound,
)
from .query import get_query_entities


class Operator(object):

    # (arity, function)
    OPERATORS = {
        'is_null': (1, lambda f: f.is_(None)),
        'is_not_null': (1, lambda f: f.isnot(None)),
        '==': (2, lambda f, a: f == a),
        'eq': (2, lambda f, a: f == a),
        '!=': (2, lambda f, a: f != a),
        'ne': (2, lambda f, a: f != a),
        '>': (2, lambda f, a: f > a),
        'gt': (2, lambda f, a: f > a),
        '<': (2, lambda f, a: f < a),
        'lt': (2, lambda f, a: f < a),
        '>=': (2, lambda f, a: f >= a),
        'ge': (2, lambda f, a: f >= a),
        '<=': (2, lambda f, a: f <= a),
        'le': (2, lambda f, a: f <= a),
        'like': (2, lambda f, a: f.like(a)),
        'in': (2, lambda f, a: f.in_(a)),
        'not_in': (2, lambda f, a: ~f.in_(a)),
    }

    def __init__(self, operator):
        if not operator:
            raise InvalidOperator('Operator not provided.')

        try:
            op = self.OPERATORS[operator]
        except KeyError:
            raise InvalidOperator(
                'Operator `{}` not valid.'.format(operator)
            )

        self.operator = operator
        self.arity = op[0]
        self.function = op[1]


class Filter(object):

    def __init__(self, filter_, models):
        if not isinstance(filter_, dict):
            raise BadFilterFormat(
                'Filter `{}` is not a dictionary.'.format(filter_)
            )

        field = filter_.get('field')
        if not field:
            raise BadFilterFormat('`field` is a mandatory filter attribute.')

        self.field = self.get_model_field(field, models)
        self.operator = Operator(filter_.get('op'))
        self.value = filter_.get('value')

    def create_sqlalchemy_filter(self):
        func = self.operator.function
        arity = self.operator.arity

        if arity == 1:
            return func(self.field)

        if arity == 2:
            if not self.value:
                raise BadFilterFormat('`value` must be provided.')
            return func(self.field, self.value)

    @staticmethod
    def get_model_field(field_name, models):
        if len(models) > 1:
            raise ModelNotFound(
                'The query has multiple models and `{}` is ambiguous. '
                'Please also provide the model.'.format(field_name)
            )
        model = [v for (k, v) in models.items()][0]  # The only entity

        try:
            return getattr(model, field_name)
        except AttributeError:
            raise ModelFieldNotFound(
                'Model {} has no attribute `{}`.'.format(model, field_name)
            )


def apply_filters(query, filters):
    models = get_query_entities(query)
    if not models:
        raise ModelNotFound('The query should contain some entities.')

    filters = _create_sqlalchemy_filters(models, filters)
    if filters:
        query = query.filter(*filters)

    return query


def _create_sqlalchemy_filters(models, filters):
    return [
        Filter(_filter, models).create_sqlalchemy_filter()
        for _filter in filters
    ]
