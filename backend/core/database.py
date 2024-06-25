from os import environ
from sqlmodel import create_engine, Session


def get_db_url():
    TESTING = environ.get("TESTING")
    DATABASE_URL = environ["DATABASE_URL"]
    DB_URL = f"{DATABASE_URL}_test" if TESTING else DATABASE_URL
    return DB_URL


engine = create_engine(get_db_url(), echo=False)


def get_session():
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
