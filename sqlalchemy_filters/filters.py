# -*- coding: utf-8 -*-

from inspect import signature

from sqlalchemy.inspection import inspect

from .exceptions import BadFilterFormat, BadQuery


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
        if self.field_name not in inspect(self.model).columns.keys():
            raise BadFilterFormat(
                'Model {} has no column `{}`.'.format(
                    self.model, self.field_name
                )
            )
        return getattr(self.model, self.field_name)


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


def apply_filters(query, filters):
    """Apply filters to a SQLAlchemy query.

    :param query:
        A :class:`sqlalchemy.orm.Query` instance.

    :param filters:
        A list of dictionaries, where each one of them includes
        the necesary information to create a filter to be applied to the
        query.

    :returns:
        The :class:`sqlalchemy.orm.Query` instance after all the filters
        have been applied.
    """
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
    """Get models from query.

    :param query:
        A :class:`sqlalchemy.orm.Query` instance.

    :returns:
        A dictionary with all the models included in the query.
    """
    return {
        entity['type'].__name__: entity['type']
        for entity in query.column_descriptions
    }
