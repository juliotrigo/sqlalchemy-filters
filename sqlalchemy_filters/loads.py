from sqlalchemy.orm import Load

from .exceptions import BadSpec, BadLoadFormat
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

        try:
            model = get_model_from_spec(load_spec, query)
        except BadSpec as exc:
            raise BadLoadFormat(str(exc)) from exc

        self.model = model
        self.fields = [Field(model, field_name) for field_name in field_names]

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

    :returns:
        The :class:`sqlalchemy.orm.Query` instance after the load restrictions
        have been applied.
    """
    sqlalchemy_loads = [
        LoadOnly(item, query).format_for_sqlalchemy() for item in load_spec
    ]
    if sqlalchemy_loads:
        query = query.options(*sqlalchemy_loads)

    return query
