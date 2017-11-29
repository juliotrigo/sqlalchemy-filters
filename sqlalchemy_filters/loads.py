from sqlalchemy.orm import Load

from .exceptions import BadLoadFormat
from .models import Field, get_model_from_spec


class LoadOnly(object):

    def __init__(self, load_spec, query):
        try:
            field_names = load_spec['fields']
        except KeyError:
            raise BadLoadFormat(
                '`fields` is a mandatory attribute.'
            )
        except TypeError:
            raise BadLoadFormat(
                'Load spec `{}` should be a dictionary.'.format(load_spec)
            )

        self.model = get_model_from_spec(load_spec, query)
        self.fields = [
            Field(self.model, field_name) for field_name in field_names
        ]

    def format_for_sqlalchemy(self):
        return Load(self.model).load_only(
            *[field.get_sqlalchemy_field() for field in self.fields]
        )


def apply_loads(query, load_spec):
    """Apply load restrictions to a :class:`sqlalchemy.orm.Query` instance.

    :param load_spec:
        A list of dictionaries, where each item contains the fields to load
        for each model.

        Example::

            load_spec = [
                {'model': 'Foo', fields': ['id', 'name']},
                {'model': 'Bar', 'fields': ['name']},
            ]

        If the query being modified refers to a single model, the `model` key
        may be omitted from the load spec. The following shorthand form is
        also accepted when the model can be inferred::

            load_spec = ['id', 'name']

    :returns:
        The :class:`sqlalchemy.orm.Query` instance after the load restrictions
        have been applied.
    """
    if (
        isinstance(load_spec, list) and
        all(map(lambda item: isinstance(item, str), load_spec))
    ):
        load_spec = {'fields': load_spec}

    if isinstance(load_spec, dict):
        load_spec = [load_spec]

    sqlalchemy_loads = [
        LoadOnly(item, query).format_for_sqlalchemy() for item in load_spec
    ]
    if sqlalchemy_loads:
        query = query.options(*sqlalchemy_loads)

    return query
