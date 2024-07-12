import os
import warnings
import pytest

from collections.abc import Generator
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.sql import text
from sqlmodel import create_engine, Session

from core.config import app
from core.database import get_db_url, get_session
from models import User, Client, Chat_Session, Chat, Sender_Role_Enum


def truncate(session: Session, table: str):
    session.exec(text(f"TRUNCATE TABLE public.{table} CASCADE;"))
    session.commit()
    session.flush()


def init_db(session: Session) -> None:
    truncate(session=session, table="chat")
    truncate(session=session, table="chat_session")
    truncate(session=session, table="client_properties")
    truncate(session=session, table="client")
    truncate(session=session, table="user_properties")
    truncate(session=session, table="user")
    user = User(
        phone_number="+12345678900",
    )
    session.add(user)
    session.commit()
    client = Client(
        phone_number="+6281234567890",
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
            "sender": Sender_Role_Enum.CLIENT,
        },
        {
            "message": "Hello, +62 812 3456 7890",
            "sender": Sender_Role_Enum.USER,
        },
        {
            "message": "Is there anything I can help you with?",
            "sender": Sender_Role_Enum.USER,
        },
        {
            "message": "Yes, I need help with something.",
            "sender": Sender_Role_Enum.CLIENT,
        },
    ]
    for message in messages:
        chat = Chat(
            chat_session_id=chat_session.id,
            message=message["message"],
            sender_role=message["sender"],
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


class MockRabbitMQClient:
    async def initialize(self):
        pass

    async def disconnect(self):
        pass

    async def consume(self, queue_name, routing_key, callback):
        pass

    async def producer(self, body, routing_key, reply_to):
        pass


class MockTwilioBotClient:
    async def send_whatsapp_message(self, message):
        pass


@pytest.fixture
def run_app():
    app.dependency_overrides[MockRabbitMQClient] = MockRabbitMQClient()
    app.dependency_overrides[MockTwilioBotClient] = MockTwilioBotClient()
