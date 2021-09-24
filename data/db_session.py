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


def global_init(*, conn_str: str = None, db_file: str = None, mkdir=False):
    global __factory

    if __factory:
        return

    if not conn_str and not db_file:
        raise FileNotFoundError("Необходимо указать файл базы данных.")

    if not bool(conn_str) ^ bool(db_file):
        raise AttributeError("Укажите одно из conn_str или db_file")
    print(f"Подключение к базе данных по адресу '{conn_str}'")

    engine = sa.create_engine(conn_str or db_file, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    if callable(__factory):
        return __factory()
