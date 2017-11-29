from sqlalchemy.inspection import inspect

from .exceptions import BadQuery, FieldNotFound, BadSpec


class Field(object):

    def __init__(self, model, field_name):
        self.model = model
        self.field_name = field_name

    def get_sqlalchemy_field(self):
        if self.field_name not in inspect(self.model).columns.keys():
            raise FieldNotFound(
                'Model {} has no column `{}`.'.format(
                    self.model, self.field_name
                )
            )
        return getattr(self.model, self.field_name)


def get_query_models(query):
    """Get models from query.

    :param query:
        A :class:`sqlalchemy.orm.Query` instance.

    :returns:
        A dictionary with all the models included in the query.
    """
    models = [col_desc['entity'] for col_desc in query.column_descriptions]
    models.extend(mapper.class_ for mapper in query._join_entities)
    return {
        model.__name__: model for model in models
    }


def get_model_from_spec(spec, query):
    """ Determine the model to which a spec applies on a given query.

    A spec that does not specify a model may be applied to a query that
    contains a single model. Otherwise the spec must specify the model to
    which it applies, and that model must be present in the query.

    :param query:
        A :class:`sqlalchemy.orm.Query` instance.

    :param spec:
        A dictionary that may or may not contain a model name to resolve
        against the query.

    :returns:
        A model instance.

    :raise BadSpec:
        If the spec is ambiguous or refers to a model not in the query.

    :raise BadQuery:
        If the query contains no models.

    """
    models = get_query_models(query)
    if not models:
        raise BadQuery('The query does not contain any models.')

    model_name = spec.get('model')
    if model_name is not None:
        models = [v for (k, v) in models.items() if k == model_name]
        if not models:
            raise BadSpec(
                'The query does not contain model `{}`.'.format(model_name)
            )
        model = models[0]
    else:
        if len(models) == 1:
            model = list(models.values())[0]
        else:
            raise BadSpec(
                "Ambiguous spec. Please specify a model."
            )

    return model
