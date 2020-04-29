from sqlalchemy.exc import SQLAlchemyError

from tourminator import models

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session

from tourminator.models import Guild, User, Event, Participation


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
        count = session.query(User).filter(
            and_(User.guild_id == guild_id, User.id == user_id)
        ).count()
        session.close()
        return count == 1

    def create_event(self, name: str, guild_id: int):
        session = self.__create_session()
        event = Event(guild_id=guild_id, name=name)
        session.add(event)
        try:
            session.commit()
            session.refresh(event)
            return event
        except SQLAlchemyError as e:
            session.rollback()
            return None
        finally:
            session.close()

    def get_all_events(self, guild_id: int):
        session = self.__create_session()
        events = session.query(Event).filter(Event.guild_id == guild_id).all()
        session.close()
        return events

    def get_event_by_name(self, name: str, guild_id: int):
        session = self.__create_session()
        event = session.query(Event).filter(
            and_(Event.guild_id == guild_id, Event.name == name)
        ).first()
        session.close()
        return event

    def update_event(self, event_id: int, message_id: int):
        session = self.__create_session()
        event = session.query(Event).filter_by(id=event_id).first()
        event.message_id = message_id
        session.commit()
        session.close()

    def get_event_by_message_id(self, message_id):
        session = self.__create_session()
        event = session.query(Event).filter(Event.message_id == message_id).first()
        session.close()
        return event

    def join_event(self, event_id, user_id):
        session = self.__create_session()
        participation = Participation(user_id=user_id, event_id=event_id)
        session.add(participation)
        try:
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            return False
        finally:
            session.close()

    def leave_event(self, event_id, user_id):
        session = self.__create_session()
        amount = session.query(Participation).filter(
            and_(Participation.event_id == event_id, Participation.user_id == user_id)
        ).delete()
        session.commit()
        session.close()
        return amount == 1

    def get_participators_of_event(self, event_id):
        session = self.__create_session()
        event = session.query(Event).filter(Event.id == event_id).first()
        participants = event.participations
        session.close()

        return list(map(lambda p: p.user_id, participants))
