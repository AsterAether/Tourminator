from sqlalchemy import Integer, Column, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Guild(Base):
    __tablename__ = 'guild'

    id = Column(Integer, primary_key=True, autoincrement=False)


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=False)
    guild_id = Column(None, ForeignKey('guild.id'), nullable=False)
