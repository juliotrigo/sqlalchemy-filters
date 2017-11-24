from sqlalchemy.orm import Load

from .exceptions import BadQuery, BadLoadFormat
from .models import get_query_models


class LoadOnly(object):

    def __init__(self, value, models):
        try:
            self.field_names = value['fields']
        except KeyError:
            raise BadLoadFormat(
                '`fields` is a mandatory attribute.'
            )
        except TypeError:
            raise BadLoadFormat(
                'Value `{}` should be a dictionary.'.format(value)
            )

        model_name = value.get('model')
        if model_name is not None:
            models = [v for (k, v) in models.items() if k == model_name]
            if not models:
                raise BadLoadFormat(
                    'The query does not contain model `{}`.'.format(model_name)
                )
            model = models[0]
        else:
            if len(models) == 1:
                model = list(models.values())[0]
            else:
                raise BadLoadFormat(
                    "Ambiguous field. Please specify a model."
                )

        self.model = model

    def format_for_sqlalchemy(self):
        return Load(self.model).load_only(*self.field_names)


def apply_loads(query, spec):
    """Apply load restrictions to a :class:`sqlalchemy.orm.Query` instance.

    :param spec:
        A list of dictionaries, where each item contains the fields to load
        for each model.

        Example::

            spec = [
                {'model': 'Foo', fields': ['id', 'name']},
                {'model': 'Bar', 'fields': ['name']},
            ]

    :returns:
        The :class:`sqlalchemy.orm.Query` instance after the load restrictions
        have been applied.
    """
    models = get_query_models(query)
    if not models:
        raise BadQuery('The query does not contain any models.')

    sqlalchemy_loads = [
        LoadOnly(value, models).format_for_sqlalchemy() for value in spec
    ]
    if sqlalchemy_loads:
        query = query.options(*sqlalchemy_loads)

    return query
