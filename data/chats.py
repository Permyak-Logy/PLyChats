import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase
from data.messages import Message


class Chat(SqlAlchemyBase):
    __tablename__ = 'chats'
    id = sqlalchemy.Column(sqlalchemy.Integer, autoincrement=True, primary_key=True)
    user_a = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    user_b = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))

    messages = orm.relation("Message", back_populates='chat')
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return f'Chat(user_a={self.user_a} user_b={self.user_b} created_date={self.created_date})'

    def _get_all_messages(self, session: sqlalchemy.orm.Session) -> sqlalchemy.orm.Query:
        return session.query(Message).filter(Message.chat_id == self.id)

    def get_all_messages(self, session: sqlalchemy.orm.Session) -> list:
        return self._get_all_messages(session).all()

    def get_opponent_id(self, session: sqlalchemy.orm.Session, user_id: int) -> int:
        opponent_id = self.user_a if self.user_a != user_id else self.user_b
        return opponent_id
