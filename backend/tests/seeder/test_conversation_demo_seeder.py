import json
import pytest
from seeder.conversation_demo_seeder import (
    create_client,
    seed_chat_data,
    get_last_user
)
from sqlalchemy import text
from sqlmodel import Session


@pytest.fixture
def conversation_data():
    json_path = "./seeder/conversation_demo.json"
    with open(json_path, "r") as f:
        data = json.load(f)
    return data


def test_create_client(session: Session):
    create_client(session=session)
    result = session.exec(text("SELECT COUNT(*) FROM \"client\""))
    assert result.scalar() > 1


def test_seed_chat_data(session: Session, conversation_data):
    last_user = get_last_user(session=session)
    assert last_user is not None

    user_id = last_user.id
    client_id = create_client(session=session)
    assert client_id is not None

    seed_chat_data(session=session, user_id=user_id, client_id=client_id)

    # Verify chat sessions after seeding
    chat_sessions = session.exec(
        text("SELECT * FROM chat_session ORDER BY id DESC")
    ).fetchall()

    # Find the chat session ID for the created session
    chat_session_id = chat_sessions[0].id if chat_sessions else None
    assert chat_session_id is not None

    # Verify that chat messages are seeded correctly
    chat_messages = session.exec(text(
        "SELECT * FROM chat WHERE chat_session_id = :chat_session_id"
    ).bindparams(chat_session_id=chat_session_id)).fetchall()
    assert len(chat_messages) == len(conversation_data)

    # Check sender and message content
    for i, chat_message in enumerate(chat_messages):
        assert chat_message.sender == conversation_data[i]["sender"].upper()
        assert chat_message.message == conversation_data[i]["message"]
