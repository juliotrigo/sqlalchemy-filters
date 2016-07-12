# -*- coding: utf-8 -*-

from collections import namedtuple

from .exceptions import (
    BadFilterFormat,
    InvalidOperator,
    ModelNotFound,
    ModelFieldNotFound,
)
from .query import get_query_entities


class Operator(object):

    OperatorFunction = namedtuple('OperatorFunction', ['arity', 'function'])

    OPERATORS = {
        'is_null': OperatorFunction(1, lambda f: f.is_(None)),
        'is_not_null': OperatorFunction(1, lambda f: f.isnot(None)),
        '==': OperatorFunction(2, lambda f, a: f == a),
        'eq': OperatorFunction(2, lambda f, a: f == a),
        '!=': OperatorFunction(2, lambda f, a: f != a),
        'ne': OperatorFunction(2, lambda f, a: f != a),
    }

    def __init__(self, operator):
        if not operator:
            raise InvalidOperator('Operator not provided.')

        try:
            op = self.OPERATORS[operator]
        except KeyError:
            raise InvalidOperator('Operator `{}` not valid.'.format(operator))

        self.operator = operator
        self.arity = op.arity
        self.function = op.function


class Filter(object):

    delimiter = '__'

    def __init__(self, filter_, models):
        if not isinstance(filter_, dict):
            raise BadFilterFormat(
                'Filter `{}` is not a dictionary.'.format(filter_)
            )

        self.operator = Operator(filter_.get('op'))
        self.value = filter_.get('value')
        field = filter_.get('field')
        other_field = filter_.get('other_field')  # TODO: finish implementation

        if not field:
            raise BadFilterFormat('`field` is a mandatory filter attribute.')

        # TODO: finish implementation
        if self.value and other_field:
            raise BadFilterFormat(
                'Both `value` and `other_field` were provided.'
            )

        self.field = self._get_model_field(field, models)
        self.other_field = (
            self._get_model_field(other_field, models) if other_field
            else None
        )  # TODO: finish implementation

    def create_sqlalchemy_filter(self):
        func = self.operator.function
        arity = self.operator.arity

        if arity == 1:
            return func(self.field)

        if arity == 2:
            # TODO: finish implementation
            if not self.value and not self.other_field:
                raise BadFilterFormat(
                    'Either `value` or `other_field` must be provided.'
                )
            if self.value:
                return func(self.field, self.value)
            elif self.other_field:
                return func(self.field, self.other_field)

        raise BadFilterFormat(
            'Incorrect number of filter arguments.'
        )

    @classmethod
    def _get_model_field(cls, field_name, models):
        if cls.delimiter in field_name:
            # TODO: finish implementation: model name as part of `field_name`
            raise NotImplemented()
        else:
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
                'Model {} has no attribute {}.'.format(model, field_name)
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
