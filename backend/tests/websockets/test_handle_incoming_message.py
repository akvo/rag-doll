from sqlmodel import Session, select
from core.socketio_config import (
    handle_incoming_message,
    Chat,
    Chat_Session,
    Client,
    Chat_Media,
)


MESSAGE = {
    "conversation_envelope": {
        "message_id": "SM48e12712cab50ba0a061cf8058d6ed47",
        "client_phone_number": "+6281222304050",
        "user_phone_number": None,
        "sender_role": "client",
        "platform": "WHATSAPP",
        "timestamp": "2024-07-16T04:29:47.799230+00:00",
    },
    "body": "Test message!",
    "media": [],
    "context": [],
    "transformation_log": ["Test message!"],
}


def test_handle_incoming_message_new_conversation(session: Session):
    handle_incoming_message(session=session, message=MESSAGE)

    new_client = session.exec(
        select(Client).where(Client.phone_number == "+6281222304050")
    ).first()
    assert new_client.phone_number == 6281222304050

    new_chat_session = session.exec(
        select(Chat_Session).where(Chat_Session.client_id == new_client.id)
    ).first()
    assert new_chat_session.client_id == new_client.id

    new_chat = session.exec(
        select(Chat).where(Chat.chat_session_id == new_chat_session.id)
    ).first()
    assert new_chat.message == "Test message!"


def test_handle_incoming_message_existing_conversation(session: Session):
    MESSAGE["body"] = "Second message"
    MESSAGE["transformation_log"] = ["Second message"]

    handle_incoming_message(session=session, message=MESSAGE)

    updated_chat_session = session.exec(
        select(Chat_Session)
        .join(Client)
        .where(Client.phone_number == "+6281222304050")
    ).all()
    assert len(updated_chat_session) == 1

    chats = session.exec(
        select(Chat).where(Chat.chat_session_id == updated_chat_session[0].id)
    ).all()
    assert chats[0].message == "Test message!"
    assert chats[1].message == "Second message"


def test_handle_incoming_message_existing_conversation_with_image(
    session: Session,
):
    image_url = "https://akvo.org/wp-content/themes/Akvo-Theme"
    image_url += "/images/logos/akvologoblack.png"

    MESSAGE["body"] = "Image caption"
    MESSAGE["transformation_log"] = ["Image caption"]
    MESSAGE["media"] = [
        {"url": image_url, "type": "image/png"},
    ]
    MESSAGE["context"] = [
        {"url": image_url, "type": "image/png", "caption": "Image caption"},
    ]

    handle_incoming_message(session=session, message=MESSAGE)

    updated_chat_session = session.exec(
        select(Chat_Session)
        .join(Client)
        .where(Client.phone_number == "+6281222304050")
    ).first()
    assert updated_chat_session is not None

    chats = session.exec(
        select(Chat).where(Chat.chat_session_id == updated_chat_session.id)
    ).all()
    assert chats[0].message == "Test message!"
    assert chats[1].message == "Second message"
    assert chats[2].message == "Image caption"

    chat_media = session.exec(
        select(Chat_Media).where(Chat_Media.chat_id == chats[2].id)
    ).all()
    assert len(chat_media) == 1
    assert chat_media[0].url == image_url
    assert chat_media[0].type == "image/png"
