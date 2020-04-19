import sqlalchemy
from .db_session import SqlAlchemyBase


class FriendRequest(SqlAlchemyBase):
    __tablename__ = 'friend_requests'
    id = sqlalchemy.Column(sqlalchemy.Integer, autoincrement=True, primary_key=True)
    sender = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    recipient = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
