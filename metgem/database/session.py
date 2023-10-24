import sqlite3

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from metgem.database.models import Base


def create_session(filename=None, echo=False, drop_all=False, read_only=False):
    if read_only:
        engine = create_engine(f'sqlite:///', echo=echo,
                               creator=lambda: sqlite3.connect(f"file:{filename}?mode=ro", uri=True))
    else:
        engine = create_engine(f'sqlite:///{filename}', echo=echo)
    Base.metadata.bind = engine

    if drop_all:
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

    # noinspection PyPep8Naming
    DBSession = sessionmaker(bind=engine)

    return DBSession()
