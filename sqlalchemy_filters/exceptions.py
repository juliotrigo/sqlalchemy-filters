# -*- coding: utf-8 -*-


class SqlAlquemyFiltersError(Exception):
    pass


class InvalidOperator(SqlAlquemyFiltersError):
    pass


class ModelNotFound(SqlAlquemyFiltersError):
    pass


class ModelFieldNotFound(SqlAlquemyFiltersError):
    pass


class BadFilterFormat(SqlAlquemyFiltersError):
    pass
