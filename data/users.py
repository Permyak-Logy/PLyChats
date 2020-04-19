import datetime
import sqlalchemy
from data.db_session import SqlAlchemyBase, create_session
from data.friends import Friends
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
    chats = orm.relation("Chat",
                         secondary="association_chats_users",
                         backref="user")

    def __repr__(self):
        return f"User(id={self.id} email='{self.email}' surname='{self.surname}' name='{self.name}')"

    def str(self):
        return repr(self)

    def set_password(self, password: str):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password: str):
        return check_password_hash(self.hashed_password, password)

    def get_obj_friends_with_user(self, user_id: int, session: sqlalchemy.orm.Session):
        session = create_session() if session is None else session
        friends = session.query(Friends).filter(
            (Friends.user_id_a == self.id) | (Friends.user_id_b == self.id)).filter(
            (Friends.user_id_a == user_id) | (Friends.user_id_b == user_id)).first()
        return friends

    def is_friend(self, user_id: int, session: sqlalchemy.orm.Session):
        return bool(self.get_obj_friends_with_user(user_id, session))

    def get_all_friends_users(self, session: sqlalchemy.orm.Session):
        session = create_session() if session is None else session
        friends = session.query(Friends).filter(
            (Friends.user_id_a == self.id) | (Friends.user_id_b == self.id)).all()
        friends_list = list(map(lambda x: x.user_id_a if x.user_id_a != self.id else x.user_id_b,
                                friends))
        return session.query(User).filter(User.id.in_(friends_list)).all()
