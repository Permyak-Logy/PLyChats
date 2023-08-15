import os

import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec

SqlAlchemyBase = dec.declarative_base()

__factory = None


def __enter__(self: Session) -> Session:
    return self


def __exit__(self: Session, *_, **__):
    self.close()


Session.__enter__ = __enter__
Session.__exit__ = __exit__


def global_init(*, conn_str: str):
    global __factory

    if __factory:
        return

    if not conn_str:
        raise FileNotFoundError("Необходимо указать подключение к базе данных.")

    print(f"Подключение к базе данных по адресу '{conn_str}'")
    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    if callable(__factory):
        return __factory()
