import pytest

from sqlmodel import Session, select, and_
from core.socketio_config import (
    save_chat_history,
    Sender_Role_Enum,
    Platform_Enum,
    Chat_Session,
    Client,
    User,
    Chat,
    Chat_Status_Enum,
)
from models import Chat_Media


@pytest.mark.asyncio
async def test_save_chat_history_when_send_a_message_into_platform(
    session: Session,
):
    chat = session.exec(select(Chat)).first()
    conversation = session.exec(
        select(Chat_Session).where(Chat_Session.id == chat.chat_session_id)
    ).first()
    client = session.exec(
        select(Client).where(Client.id == conversation.client_id)
    ).first()
    user = session.exec(
        select(User).where(User.id == conversation.user_id)
    ).first()

    conversation_envelope = {
        "user_phone_number": f"+{user.phone_number}",
        "client_phone_number": f"+{client.phone_number}",
        "sender_role": Sender_Role_Enum.USER.value,
        "platform": Platform_Enum.WHATSAPP.value,
        "message_id": "123456",
        "timestamp": "2024-11-05T03:03:00.308848+00:00",
    }

    result = await save_chat_history(
        session=session,
        conversation_envelope=conversation_envelope,
        message_body="Saved message",
    )

    assert result is not None
    chat_id = result.get("chat_id")
    chat = session.exec(select(Chat).where(Chat.id == chat_id)).first()
    send_conversation_reconnect_template = result.get(
        "send_conversation_reconnect_template"
    )
    assert send_conversation_reconnect_template is False
    assert chat.message == "Saved message"
    assert chat.sender_role == Sender_Role_Enum.USER
    assert chat.status == Chat_Status_Enum.READ


@pytest.mark.asyncio
async def test_save_chat_history_with_image(session: Session):
    chat = session.exec(select(Chat)).first()
    conversation = session.exec(
        select(Chat_Session).where(Chat_Session.id == chat.chat_session_id)
    ).first()
    client = session.exec(
        select(Client).where(Client.id == conversation.client_id)
    ).first()
    user = session.exec(
        select(User).where(User.id == conversation.user_id)
    ).first()

    image_url = "https://akvo.org/wp-content/themes/Akvo-Theme"
    image_url += "/images/logos/akvologoblack.png"

    conversation_envelope = {
        "user_phone_number": f"+{user.phone_number}",
        "client_phone_number": f"+{client.phone_number}",
        "sender_role": Sender_Role_Enum.USER.value,
        "platform": Platform_Enum.WHATSAPP.value,
        "message_id": "123457",
        "timestamp": "2024-11-05T03:03:00.308848+00:00",
    }

    media = [
        {"url": image_url, "type": "image/png"},
        {"url": image_url, "type": "image/png"},
    ]

    result = await save_chat_history(
        session=session,
        conversation_envelope=conversation_envelope,
        message_body="Saved message with image",
        media=media,
    )

    assert result is not None
    chat_id = result.get("chat_id")
    chat = session.exec(select(Chat).where(Chat.id == chat_id)).first()
    send_conversation_reconnect_template = result.get(
        "send_conversation_reconnect_template"
    )
    assert send_conversation_reconnect_template is False
    assert chat.message == "Saved message with image"
    assert chat.sender_role == Sender_Role_Enum.USER
    assert chat.status == Chat_Status_Enum.READ

    chat_media = session.exec(
        select(Chat_Media).where(Chat_Media.chat_id == chat.id)
    ).all()
    assert len(chat_media) == 2


@pytest.mark.asyncio
async def test_save_chat_history_for_a_conversation_without_chat_before(
    session: Session,
):
    chats = session.exec(select(Chat)).all()
    conversation_ids = [c.chat_session_id for c in chats]
    conversation = session.exec(
        select(Chat_Session).where(Chat_Session.id.notin_(conversation_ids))
    ).first()
    assert conversation is not None

    client = session.exec(
        select(Client).where(Client.id == conversation.client_id)
    ).first()
    user = session.exec(
        select(User).where(User.id == conversation.user_id)
    ).first()

    client_phone_number = f"+{client.phone_number}"
    conversation_envelope = {
        "user_phone_number": f"+{user.phone_number}",
        "client_phone_number": client_phone_number,
        "sender_role": Sender_Role_Enum.USER.value,
        "platform": Platform_Enum.WHATSAPP.value,
        "message_id": "123456",
        "timestamp": "2024-11-05T03:03:00.308848+00:00",
    }

    result = await save_chat_history(
        session=session,
        conversation_envelope=conversation_envelope,
        message_body="First message",
    )

    assert result is not None
    chat_id = result.get("chat_id")
    chat = session.exec(select(Chat).where(Chat.id == chat_id)).first()
    send_conversation_reconnect_template = result.get(
        "send_conversation_reconnect_template"
    )
    chat_session_id = result.get("chat_session_id")
    assert chat_session_id is not None
    assert send_conversation_reconnect_template is True
    assert chat.message == "First message"
    assert chat.sender_role == Sender_Role_Enum.USER
    assert chat.status == Chat_Status_Enum.READ

    # assert system chat
    system_chat = session.exec(
        select(Chat)
        .where(
            and_(
                Chat.chat_session_id == chat_session_id,
                Chat.id <= chat_id,
                Chat.sender_role == Sender_Role_Enum.SYSTEM,
            )
        )
        .order_by(Chat.created_at.desc(), Chat.id.desc())
    ).first()
    assert system_chat is not None
    text = "Please reply this message to restart your conversation."
    assert system_chat.message == f"Hi {client_phone_number},\n{text}"
