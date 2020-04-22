import datetime
import sqlalchemy
from .chats import Chat
from .db_session import SqlAlchemyBase
from .friends import Friends
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import orm


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    surname = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    patronymic = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    about = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String,
                              index=True, unique=True, nullable=False)
    phone = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=True)
    address = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)
    modified_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    news = orm.relation("News", back_populates='user')

    def __repr__(self):
        return f"User(id={self.id} " \
               f"email='{self.email}' " \
               f"surname='{self.surname}'  " \
               f"name='{self.name}' " \
               f"patronymic='{self.patronymic}')"

    def __str__(self):
        return f'{self.surname} {self.name} {self.patronymic if self.patronymic else ""}'

    def set_password(self, password: str):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password: str):
        return check_password_hash(self.hashed_password, password)

    def get_obj_friends_with_user(self, session: sqlalchemy.orm.Session, user_id: int):
        friends = session.query(Friends).filter(
            (Friends.user_id_a == self.id) | (Friends.user_id_b == self.id)).filter(
            (Friends.user_id_a == user_id) | (Friends.user_id_b == user_id)).first()
        return friends

    def is_friend(self, session: sqlalchemy.orm.Session, user_id: int):
        return bool(self.get_obj_friends_with_user(session, user_id))

    def get_all_friends_users(self, session: sqlalchemy.orm.Session):
        friends = session.query(Friends).filter(
            (Friends.user_id_a == self.id) | (Friends.user_id_b == self.id)).all()
        friends_list = list(map(lambda x: x.user_id_a if x.user_id_a != self.id else x.user_id_b,
                                friends))
        return session.query(User).filter(User.id.in_(friends_list)).all()

    def _get_all_chats(self, session: sqlalchemy.orm.Session) -> sqlalchemy.orm.Query:
        return session.query(Chat).filter((Chat.user_a == self.id) | (Chat.user_b == self.id))

    def get_all_chats(self, session: sqlalchemy.orm.Session) -> list:
        return self._get_all_chats(session).all()

    def get_chat_with_user(self, session: sqlalchemy.orm.Session, user_id: int) -> Chat:
        all_chats = self._get_all_chats(session)
        return all_chats.filter((Chat.user_a == user_id) | (Chat.user_b == user_id)).first()

    def get_chat(self, session: sqlalchemy.orm.Session, chat_id) -> Chat:
        return self._get_all_chats(session).filter(Chat.id == chat_id).first()
