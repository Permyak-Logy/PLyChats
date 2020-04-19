import sqlalchemy
from .db_session import SqlAlchemyBase


class Friends(SqlAlchemyBase):
    __tablename__ = 'friends'
    user_id_a = sqlalchemy.Column(sqlalchemy.Integer,
                                  sqlalchemy.ForeignKey('users.id'), nullable=False, primary_key=True)
    user_id_b = sqlalchemy.Column(sqlalchemy.Integer,
                                  sqlalchemy.ForeignKey('users.id'), nullable=False, primary_key=True)
