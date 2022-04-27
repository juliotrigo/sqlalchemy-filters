import sqlalchemy
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.util import symbol
import types

from .exceptions import BadQuery, FieldNotFound, BadSpec


try:
    from sqlalchemy import Table
    from sqlalchemy.sql.selectable import Alias
except ImportError:
    pass


class Field(object):

    def __init__(self, model, field_name):
        self.model = model
        self.field_name = field_name

    def get_sqlalchemy_field(self):
        if self.field_name not in self._get_valid_field_names():
            raise FieldNotFound(
                'Model {} has no column `{}`.'.format(
                    self.model, self.field_name
                )
            )
        sqlalchemy_field = getattr(self.model, self.field_name)

        # If it's a hybrid method, then we call it so that we can work with
        # the result of the execution and not with the method object itself
        if isinstance(sqlalchemy_field, types.MethodType):
            sqlalchemy_field = sqlalchemy_field()

        return sqlalchemy_field

    def _get_valid_field_names(self):
        inspect_mapper = inspect(self.model)
        columns = inspect_mapper.columns
        orm_descriptors = inspect_mapper.all_orm_descriptors

        column_names = columns.keys()
        hybrid_names = [
            key for key, item in orm_descriptors.items()
            if _is_hybrid_property(item) or _is_hybrid_method(item)
        ]

        return set(column_names) | set(hybrid_names)


def _is_hybrid_property(orm_descriptor):
    return orm_descriptor.extension_type == symbol('HYBRID_PROPERTY')


def _is_hybrid_method(orm_descriptor):
    return orm_descriptor.extension_type == symbol('HYBRID_METHOD')


def _get_tables_from_join(orm_join):
    models = []
    if isinstance(orm_join.right, Table):
        models.append(orm_join.right)
    elif isinstance(orm_join.right, Alias):
        pass
    else:
        models.extend(_get_tables_from_join(orm_join.right))
    if isinstance(orm_join.left, Table):
        models.append(orm_join.left)
    elif isinstance(orm_join.right, Alias):
        pass
    else:
        models.extend(_get_tables_from_join(orm_join.left))
    return models


def _get_model_class_by_table_name(registry, tablename):
    """ Return the model class matching `tablename` in the given `registry`.
    """
    for cls in registry.values():
        if hasattr(cls, '__tablename__') and cls.__tablename__ == tablename:
            return cls


def _get_query_models_1_4(query):
    """Get models from query. Works for sqlalchemy 1.4

    :param query:
        A :class:`sqlalchemy.orm.Query` instance.

    :returns:
        A dictionary with all the models included in the query.
    """
    models = [col_desc['entity'] for col_desc in query.column_descriptions]
    if models:
        try:
            registry = models[-1].registry._class_registry
            joined = []
            for f in query.statement.get_final_froms():
                if not f._is_join:
                    continue
                if isinstance(f, Table):
                    joined.append(
                        _get_model_class_by_table_name(registry, f.name)
                    )
                else:
                    joined.extend(
                        _get_model_class_by_table_name(registry, m.name)
                        for m in _get_tables_from_join(f)
                    )

            models.extend([m for m in joined if m not in models])
        except InvalidRequestError:
            pass

    tables = query._from_obj
    select_from_models = [
        t._annotations['entity_namespace']._identity_class for t in tables
    ]
    models.extend([m for m in select_from_models if m not in models])

    tables = query._legacy_setup_joins
    joined = [
        t[0]._annotations['entity_namespace']._identity_class
        for t in tables
    ]
    models.extend([m for m in joined if m not in models])

    return {model.__name__: model for model in models if model}


def _get_query_models(query):
    """Get models from query. Works for sqlalchemy < 1.4

    :param query:
        A :class:`sqlalchemy.orm.Query` instance.

    :returns:
        A dictionary with all the models included in the query.
    """
    models = [col_desc['entity'] for col_desc in query.column_descriptions]
    models.extend(mapper.class_ for mapper in query._join_entities)

    # account also query.select_from entities
    if (
        hasattr(query, '_select_from_entity') and
        (query._select_from_entity is not None)
    ):
        model_class = (
            query._select_from_entity.class_
            if isinstance(query._select_from_entity, Mapper)  # sqlalchemy>=1.1
            else query._select_from_entity  # sqlalchemy==1.0
        )
        if model_class not in models:
            models.append(model_class)

    return {model.__name__: model for model in models}


def get_query_models(query):
    """Get models from query.

    :param query:
        A :class:`sqlalchemy.orm.Query` instance.

    :returns:
        A dictionary with all the models included in the query.
    """
    if sqlalchemy.__version__ > '1.3':
        return _get_query_models_1_4(query)
    return _get_query_models(query)


def get_model_from_spec(spec, query, default_model=None):
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
        elif default_model is not None:
            return default_model
        else:
            raise BadSpec("Ambiguous spec. Please specify a model.")

    return model


def get_model_class_by_name(registry, name):
    """ Return the model class matching `name` in the given `registry`.
    """
    for cls in registry.values():
        if getattr(cls, '__name__', None) == name:
            return cls


def get_default_model(query):
    """ Return the singular model from `query`, or `None` if `query` contains
    multiple models.
    """
    query_models = get_query_models(query).values()
    if len(query_models) == 1:
        default_model, = iter(query_models)
    else:
        default_model = None
    return default_model


def _auto_join(query, *model_names):
    """ Automatically join models to `query` if they're not already present
    and the join can be done implicitly. Works for sqlalchemy < 1.4
    """
    # every model has access to the registry, so we can use any from the query
    query_models = get_query_models(query).values()
    model_registry = list(query_models)[-1]._decl_class_registry

    for name in model_names:
        model = get_model_class_by_name(model_registry, name)
        if model not in get_query_models(query).values():
            try:
                query = query.join(model)
            except InvalidRequestError:
                pass  # can't be autojoined
    return query


def _auto_join_1_4(query, *model_names):
    """ Automatically join models to `query` if they're not already present
    and the join can be done implicitly. Works for sqlalchemy 1.4
    """
    # every model has access to the registry, so we can use any from the query
    query_models = get_query_models(query).values()
    model_registry = list(query_models)[-1].registry._class_registry

    for name in model_names:
        model = get_model_class_by_name(model_registry, name)
        if model and model not in get_query_models(query).values():
            try:
                tmp_query = query.join(model)
                tmp_query.statement.compile()
                query = tmp_query
            except InvalidRequestError:
                pass  # can't be autojoined
    return query


def auto_join(query, *model_names):
    """ Automatically join models to `query` if they're not already present
    and the join can be done implicitly.
    """
    if sqlalchemy.__version__ < '1.4':
        return _auto_join(query, *model_names)
    return _auto_join_1_4(query, *model_names)
