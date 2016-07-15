# -*- coding: utf-8 -*-


class SqlAlchemyFiltersError(Exception):
    pass


class InvalidOperator(SqlAlchemyFiltersError):
    pass


class ModelNotFound(SqlAlchemyFiltersError):
    pass


class ModelFieldNotFound(SqlAlchemyFiltersError):
    pass


class BadFilterFormat(SqlAlchemyFiltersError):
    pass
