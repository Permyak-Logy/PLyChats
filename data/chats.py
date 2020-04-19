import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase
from .users import User


class Chat(SqlAlchemyBase):
    __tablename__ = 'chats'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    owner = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    is_public = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False)

    messages = orm.relation("Message", back_populates='chat')
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    association_table = sqlalchemy.Table('association_chats_users', SqlAlchemyBase.metadata,
                                         sqlalchemy.Column('user', sqlalchemy.Integer,
                                                           sqlalchemy.ForeignKey('users.id')),
                                         sqlalchemy.Column('chat', sqlalchemy.Integer,
                                                           sqlalchemy.ForeignKey('chats.id'))
                                         )

    def get_name(self, session: sqlalchemy.orm.Session, cur_user=None):
        if not self.is_public:
            for user in self.get_members(session):
                if user != cur_user:
                    return f'{user.surname} {user.name}'
        return self.name

    def get_members(self, session: sqlalchemy.orm.Session):
        result = []
        [[result.append(user) for chat in user.chats if chat.id == self.id] for user in session.query(User).all()]
        return result
