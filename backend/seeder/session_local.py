from core.database import get_db_url
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def get_session_local():
    # generate sesssion local for seeder
    DATABASE_URL = get_db_url()
    engine = create_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()
