# -*- coding: utf-8 -*-

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property


class Base(object):
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    count = Column(Integer, nullable=True)

    @hybrid_property
    def count_square(self):
        return self.count * self.count


Base = declarative_base(cls=Base)


class Foo(Base):

    __tablename__ = 'foo'

    bar_id = Column(Integer, ForeignKey('bar.id'), nullable=True)
    bar = relationship('Bar', back_populates='foos')


class Bar(Base):

    __tablename__ = 'bar'
    foos = relationship('Foo', back_populates='bar')


class Baz(Base):

    __tablename__ = 'baz'

    qux_id = Column(Integer, ForeignKey('qux.id'), nullable=True)


class Qux(Base):

    __tablename__ = 'qux'

    created_at = Column(Date)
    execution_time = Column(DateTime)
