import json
import pytest
from seeder.conversation import (
    create_client,
    seed_chat_data,
    get_last_user,
    Client,
    Chat,
    Chat_Session,
    Sender_Role_Enum,
)
from sqlmodel import Session, select


@pytest.fixture
def conversation_data():
    json_path = "./seeder/fixtures/conversation_demo.json"
    with open(json_path, "r") as f:
        data = json.load(f)
    return data


def test_create_client(session: Session):
    create_client(session=session)
    result = session.exec(select(Client.id)).all()
    assert len(result) > 1


def test_seed_chat_data(session: Session, conversation_data):
    last_user = get_last_user(session=session)
    assert last_user is not None

    user_id = last_user.id
    client_id = create_client(session=session)
    assert client_id is not None

    seed_chat_data(session=session, user_id=user_id, client_id=client_id)

    # Verify chat sessions after seeding
    chat_session = session.exec(
        select(Chat_Session).order_by(Chat_Session.id.desc())
    ).first()

    # Find the chat session ID for the created session
    chat_session_id = chat_session.id if chat_session else None
    assert chat_session_id is not None

    # Verify that chat messages are seeded correctly
    chat_messages = session.exec(
        select(Chat).where(Chat.chat_session_id == chat_session_id)
    ).all()
    assert len(chat_messages) == len(conversation_data)

    # Check sender and message content
    for i, chat_message in enumerate(chat_messages):
        assert (
            chat_message.sender_role
            == Sender_Role_Enum[conversation_data[i]["sender"].upper()]
        )
        assert chat_message.message == conversation_data[i]["message"]
