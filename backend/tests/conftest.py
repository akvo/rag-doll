import os
import warnings
import pytest

from collections.abc import Generator
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.sql import text
from sqlmodel import create_engine, Session

from core.database import get_db_url, get_session
from models import (
    User,
    Client,
    Chat_Session,
    Chat,
)


def init_db(session: Session) -> None:
    session.exec(text("DELETE FROM chat"))
    session.exec(text("DELETE FROM chat_session"))
    session.exec(text("DELETE FROM client"))
    session.exec(text("DELETE FROM public.user"))
    user = User(
        email="test@test.org",
        username="testing",
        phone_number=999,
    )
    session.add(user)
    session.commit()
    client = Client(
        phone_number=998,
    )
    session.add(client)
    session.commit()
    chat_session = Chat_Session(
        user_id=user.id,
        client_id=client.id,
    )
    session.add(chat_session)
    session.commit()
    messages = [
        {
            "message": "Hello Admin!",
            "is_client": 1,
        },
        {
            "message": "Hello, 998",
        },
        {
            "message": "Is there anything I can help you with?",
        },
        {
            "message": "Yes, I need help with something.",
            "is_client": 1,
        },
    ]
    for message in messages:
        chat = Chat(
            chat_session_id=chat_session.id,
            message=message["message"],
            is_client=message.get("is_client", 0),
        )
        session.add(chat)
        session.commit()


@pytest.fixture
def session() -> Session:
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    engine = create_engine(get_db_url())
    session = Session(engine)
    return session


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    os.environ["TESTING"] = "1"
    engine = create_engine(get_db_url())

    config = Config("alembic.ini")
    command.upgrade(config, "head")

    with Session(engine) as session:
        init_db(session)
        yield session


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    from core.config import app

    os.environ["TESTING"] = "1"
    engine = create_engine(get_db_url())

    def override_get_db():
        session = Session(engine)
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_get_db
    with TestClient(app) as c:
        yield c
