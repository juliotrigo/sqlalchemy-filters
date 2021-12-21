# -*- coding: utf-8 -*-

from sqlalchemy import (
    Column, Date, DateTime, ForeignKey, Integer, String, Time
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.orm import relationship


class Base(object):
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    count = Column(Integer, nullable=True)

    @hybrid_property
    def count_square(self):
        return self.count * self.count

    @hybrid_method
    def three_times_count(self):
        return self.count * 3


Base = declarative_base(cls=Base)
BasePostgresqlSpecific = declarative_base(cls=Base)


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
    expiration_time = Column(Time)


class Corge(BasePostgresqlSpecific):

    __tablename__ = 'corge'

    tags = Column(ARRAY(String, dimensions=1))
