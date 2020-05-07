from typing import Tuple

from sqlalchemy.exc import SQLAlchemyError

from tourminator import models

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session

from tourminator.models import Event, Participation


class DatabaseService:

    def __init__(self, db_file: str) -> None:
        self.db_engine = create_engine('sqlite:///' + db_file)
        self.SessionMaker = sessionmaker(bind=self.db_engine)

        self.__create_tables()

    def __create_tables(self):
        models.Base.metadata.create_all(self.db_engine)

    def __create_session(self) -> Session:
        return self.SessionMaker()

    def create_event(self, name: str, description: str, guild_id: int):
        session = self.__create_session()
        event = Event(guild_id=guild_id, description=description, name=name)
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

    def delete_event(self, event_id: int):
        session = self.__create_session()
        session.query(Participation).filter_by(event_id=event_id).delete()
        session.flush()
        session.query(Event).filter_by(id=event_id).delete()
        session.commit()
        session.close()

    def get_all_events(self, guild_id: int):
        session = self.__create_session()
        events = session.query(Event).filter(Event.guild_id == guild_id).all()
        session.close()
        return events

    def get_event_by(self, name: Tuple[str, int] = None, message_id: Tuple[int, int] = None,
                     event_channel_id: int = None):
        session = self.__create_session()
        if name is not None:
            criteria = and_(Event.guild_id == name[1], Event.name == name[0])
        elif message_id is not None:
            criteria = and_(Event.message_id == message_id[0], Event.message_channel_id == message_id[1])
        else:
            criteria = Event.event_channel_id == event_channel_id

        event = session.query(Event).filter(
            criteria
        ).first()
        session.close()
        return event

    def update_event(self, event_id: int, message_id: int = None, message_channel_id: int = None,
                     event_channel_id: int = None, event_role_id: int = None, description: str = None):
        session = self.__create_session()
        event = session.query(Event).filter_by(id=event_id).first()
        if message_id is not None:
            event.message_id = message_id
        if message_channel_id is not None:
            event.message_channel_id = message_channel_id
        if event_channel_id is not None:
            event.event_channel_id = event_channel_id
        if event_role_id is not None:
            event.event_role_id = event_role_id
        if description is not None:
            event.description = description
        session.commit()
        session.close()

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

    def get_participants_of_event(self, event_id):
        session = self.__create_session()
        event = session.query(Event).filter(Event.id == event_id).first()
        participants = event.participations
        session.close()

        return list(map(lambda p: p.user_id, participants))
