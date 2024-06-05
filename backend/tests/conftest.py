import warnings
import pytest

from collections.abc import Generator
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlmodel import create_engine, Session, select

from core.config import app
from core.database import get_db_url
from models import User


def init_db(session: Session) -> None:
    user = session.exec(select(User).where(User.username == "testing")).first()
    if not user:
        user = User(
            email="test@test.org",
            username="testing",
            phone_number=999,
        )
        session.add(user)
        session.commit()


@pytest.fixture(scope="session")
def apply_migrations():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    config = Config("alembic.ini")
    command.upgrade(config, "head")


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    engine = create_engine(get_db_url())
    with Session(engine) as session:
        init_db(session)
        yield session


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c
