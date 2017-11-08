from sqlalchemy.inspection import inspect

from .exceptions import FieldNotFound


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
