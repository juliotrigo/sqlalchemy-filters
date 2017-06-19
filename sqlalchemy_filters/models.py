from sqlalchemy.inspection import inspect

from .exceptions import FieldNotFound, BadQuery


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
    return {
        col_desc['entity'].__name__: col_desc['entity']
        for col_desc in query.column_descriptions
    }
