# -*- coding: utf-8 -*-

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base


class Base(object):
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    count = Column(Integer, nullable=True)


Base = declarative_base(cls=Base)


class Foo(Base):

    __tablename__ = 'foo'

    bar_id = Column(Integer, ForeignKey('bar.id'), nullable=True)


class Bar(Base):

    __tablename__ = 'bar'


class Baz(Base):

    __tablename__ = 'baz'

    qux_id = Column(Integer, ForeignKey('qux.id'), nullable=True)


class Qux(Base):

    __tablename__ = 'qux'
