from sqlalchemy import __version__ as sqlalchemy_version
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import mapperlib
from sqlalchemy.inspection import inspect
from sqlalchemy.util import symbol
import types

from .exceptions import BadQuery, FieldNotFound, BadSpec


def sqlalchemy_version_lt(version):
    """compares sqla version < version"""

    return tuple(sqlalchemy_version.split('.')) < tuple(version.split('.'))


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


def get_model_from_table(table):  # pragma: no_cover_sqlalchemy_lt_1_4
    """Resolve model class from table object"""

    for registry in mapperlib._all_registries():
        for mapper in registry.mappers:
            if table in mapper.tables:
                return mapper.class_
    return None


def get_query_models(query):
    """Get models from query.

    :param query:
        A :class:`sqlalchemy.orm.Query` instance.

    :returns:
        A dictionary with all the models included in the query.
    """
    models = [col_desc['entity'] for col_desc in query.column_descriptions]

    # account joined entities
    if sqlalchemy_version_lt('1.4'):  # pragma: no_cover_sqlalchemy_gte_1_4
        models.extend(mapper.class_ for mapper in query._join_entities)
    else:  # pragma: no_cover_sqlalchemy_lt_1_4
        try:
            models.extend(
                mapper.class_
                for mapper
                in query._compile_state()._join_entities
            )
        except InvalidRequestError:
            # query might not contain columns yet, hence cannot be compiled
            # try to infer the models from various internals
            for table_tuple in query._setup_joins + query._legacy_setup_joins:
                model_class = get_model_from_table(table_tuple[0])
                if model_class:
                    models.append(model_class)

    # account also query.select_from entities
    model_class = None
    if sqlalchemy_version_lt('1.4'):  # pragma: no_cover_sqlalchemy_gte_1_4
        if query._select_from_entity:
            model_class = (
                query._select_from_entity
                if sqlalchemy_version_lt('1.1')
                else query._select_from_entity.class_
            )
    else:  # pragma: no_cover_sqlalchemy_lt_1_4
        if query._from_obj:
            model_class = get_model_from_table(query._from_obj[0])
    if model_class and (model_class not in models):
        models.append(model_class)

    return {model.__name__: model for model in models}


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


def auto_join(query, *model_names):
    """ Automatically join models to `query` if they're not already present
    and the join can be done implicitly.
    """
    # every model has access to the registry, so we can use any from the query
    query_models = get_query_models(query).values()
    last_model = list(query_models)[-1]
    model_registry = (
        last_model._decl_class_registry
        if sqlalchemy_version_lt('1.4')
        else last_model.registry._class_registry
    )

    for name in model_names:
        model = get_model_class_by_name(model_registry, name)
        if model and (model not in get_query_models(query).values()):
            try:
                if sqlalchemy_version_lt('1.4'):  # pragma: no_cover_sqlalchemy_gte_1_4
                    query = query.join(model)
                else:  # pragma: no_cover_sqlalchemy_lt_1_4
                    # https://docs.sqlalchemy.org/en/14/changelog/migration_14.html
                    # Many Core and ORM statement objects now perform much of
                    # their construction and validation in the compile phase
                    tmp = query.join(model)
                    tmp._compile_state()
                    query = tmp
            except InvalidRequestError:
                pass  # can't be autojoined
    return query
