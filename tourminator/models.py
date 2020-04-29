from functools import partial

from sqlalchemy import Integer, Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Guild(Base):
    __tablename__ = 'guild'

    id = Column(Integer, primary_key=True, autoincrement=False)


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=False)
    guild_id = Column(None, ForeignKey('guild.id'), primary_key=True, nullable=False)


class Event(Base):
    __tablename__ = 'event'
    __table_args__ = (UniqueConstraint('guild_id', 'name'),)

    id = Column(Integer, primary_key=True)
    guild_id = Column(None, ForeignKey('guild.id'), nullable=False)
    name = Column(String, nullable=False)
    message_id = Column(Integer)
    participations = relationship('Participation')


class Participation(Base):
    __tablename__ = 'participation'

    user_id = Column(None, ForeignKey('user.id'), primary_key=True, nullable=False)
    event_id = Column(None, ForeignKey('event.id'), primary_key=True, nullable=False)
