# -*- coding: utf-8 -*-


def create_query(session, models):
    try:
        iter(models)
    except TypeError:
        return session.query(models)  # Single model provided

    return session.query(*models)


def get_query_entities(query):
    return {
        entity['type'].__name__: entity['type']
        for entity in query.column_descriptions
    }
