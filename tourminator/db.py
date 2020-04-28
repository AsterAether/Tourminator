from sqlalchemy.exc import SQLAlchemyError

from tourminator import models

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session

from tourminator.models import Guild, User


class DatabaseService:

    def __init__(self, db_file: str) -> None:
        self.db_engine = create_engine('sqlite:///' + db_file)
        self.SessionMaker = sessionmaker(bind=self.db_engine)

        self.__create_tables()

    def __create_tables(self):
        models.Base.metadata.create_all(self.db_engine)

    def __create_session(self) -> Session:
        return self.SessionMaker()

    def register_guild(self, guild_id):
        session = self.__create_session()
        guild = Guild(id=guild_id)
        session.add(guild)
        try:
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            return False
        finally:
            session.close()

    def register_user(self, user_id, guild_id):
        session = self.__create_session()
        user = User(id=user_id, guild_id=guild_id)
        session.add(user)
        try:
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            return False
        finally:
            session.close()

    def is_registered(self, user_id, guild_id):
        session = self.__create_session()
        count = session.query(models.User).filter(
            and_(models.User.guild_id == guild_id, models.User.id == user_id)
        ).count()
        session.close()
        return count == 1
