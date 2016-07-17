# -*- coding: utf-8 -*-

from collections import namedtuple

from .exceptions import BadFilterFormat, BadQuery


class Operator(object):

    OperatorFunction = namedtuple('OperatorFunction', ['arity', 'function'])

    OPERATORS = {
        'is_null': OperatorFunction(1, lambda f: f.is_(None)),
        'is_not_null': OperatorFunction(1, lambda f: f.isnot(None)),
        '==': OperatorFunction(2, lambda f, a: f == a),
        'eq': OperatorFunction(2, lambda f, a: f == a),
        '!=': OperatorFunction(2, lambda f, a: f != a),
        'ne': OperatorFunction(2, lambda f, a: f != a),
        '>': OperatorFunction(2, lambda f, a: f > a),
        'gt': OperatorFunction(2, lambda f, a: f > a),
        '<': OperatorFunction(2, lambda f, a: f < a),
        'lt': OperatorFunction(2, lambda f, a: f < a),
        '>=': OperatorFunction(2, lambda f, a: f >= a),
        'ge': OperatorFunction(2, lambda f, a: f >= a),
        '<=': OperatorFunction(2, lambda f, a: f <= a),
        'le': OperatorFunction(2, lambda f, a: f <= a),
        'like': OperatorFunction(2, lambda f, a: f.like(a)),
        'in': OperatorFunction(2, lambda f, a: f.in_(a)),
        'not_in': OperatorFunction(2, lambda f, a: ~f.in_(a)),
    }

    def __init__(self, operator):
        if operator not in self.OPERATORS:
            raise BadFilterFormat('Operator `{}` not valid.'.format(operator))

        op = self.OPERATORS[operator]
        self.operator = operator
        self.arity = op.arity
        self.function = op.function


class Field(object):

    def __init__(self, models, field_name):
        # TODO: remove this check once we start supporing multiple models
        if len(models) > 1:
            raise BadQuery('The query should contain only one model.')

        self.model = self._get_model(models)
        self.field_name = field_name

    def _get_model(self, models):
        # TODO: add model_name argument once we start supporing multiple models
        return [v for (k, v) in models.items()][0]  # first (and only) model

    def get_sqlalchemy_field(self):
        try:
            return getattr(self.model, self.field_name)
        except AttributeError:
            raise BadFilterFormat(
                'Model {} has no attribute `{}`.'.format(
                    self.model, self.field_name
                )
            )


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

    def format_for_sqlalchemy(self):
        function = self.operator.function
        arity = self.operator.arity
        field = self.field.get_sqlalchemy_field()

        if arity == 1:
            return function(field)

        if arity == 2:
            if not self.value_present:
                raise BadFilterFormat('`value` must be provided.')

            return function(field, self.value)


def apply_filters(query, filters):
    models = get_query_models(query)
    if not models:
        raise BadQuery('The query does not contain any models.')

    sqlalchemy_filters = [
        Filter(filter_, models).format_for_sqlalchemy() for filter_ in filters
    ]
    if sqlalchemy_filters:
        query = query.filter(*sqlalchemy_filters)

    return query


def get_query_models(query):
    return {
        entity['type'].__name__: entity['type']
        for entity in query.column_descriptions
    }
