from datetime import datetime, timezone, timedelta
from db import check_if_after_24h_window, add_media
from models import (
    Chat,
    Chat_Session,
    Sender_Role_Enum,
    Chat_Status_Enum,
    User,
    Client,
    Platform_Enum,
    Chat_Media,
)
from sqlmodel import Session, select


tz = timezone.utc


def test_check_if_after_24h_window_return_false(session: Session):
    chat = session.exec(select(Chat)).first()
    res = check_if_after_24h_window(
        session=session, chat_session_id=chat.chat_session_id
    )
    assert res is False


def test_check_if_after_24h_window_return_true(session: Session):
    # create new conversation > 24hr for this condition
    user = session.exec(select(User)).first()
    new_client = Client(phone_number="+62819991035101")
    session.add(new_client)
    session.commit()
    session.flush()

    new_chat_session = Chat_Session(
        user_id=user.id,
        client_id=new_client.id,
        platform=Platform_Enum.WHATSAPP,
    )
    session.add(new_chat_session)
    session.commit()
    session.flush()

    new_chat = Chat(
        chat_session_id=new_chat_session.id,
        message="First message",
        sender_role=Sender_Role_Enum.CLIENT,
        status=Chat_Status_Enum.READ,
        created_at=datetime.now(tz) - timedelta(hours=26),
    )
    session.add(new_chat)
    session.commit()
    new_chat = Chat(
        chat_session_id=new_chat_session.id,
        message="24h message test",
        sender_role=Sender_Role_Enum.CLIENT,
        status=Chat_Status_Enum.READ,
        created_at=datetime.now(tz) - timedelta(hours=25),
    )
    session.add(new_chat)
    session.commit()
    session.flush()

    res = check_if_after_24h_window(
        session=session, chat_session_id=new_chat_session.id
    )
    assert res is True


def test_add_media_for_a_chat(session: Session):
    client = session.exec(
        select(Client).where(Client.phone_number == "+62819991035101")
    ).first()
    chat_session = session.exec(
        select(Chat_Session).where(Chat_Session.client_id == client.id)
    ).first()

    new_chat = Chat(
        chat_session_id=chat_session.id,
        message="Message with media",
        sender_role=Sender_Role_Enum.CLIENT,
        created_at=datetime.now(tz) - timedelta(hours=24),
    )
    session.add(new_chat)
    session.commit()

    media = [
        {
            "url": "https://mediaurl.test/filename.jpg",
            "type": "image/jpg",
        },
        {"url": "https://mediaurl.test/filename2.jpg", "type": "image/jpg"},
    ]
    add_media(session=session, chat=new_chat, media=media)

    media = session.exec(
        select(Chat_Media).where(Chat_Media.chat_id == new_chat.id)
    ).all()
    res = [m.simplify() for m in media]
    assert res == [
        {
            "type": "image/jpg",
            "url": "https://mediaurl.test/filename.jpg",
        },
        {
            "type": "image/jpg",
            "url": "https://mediaurl.test/filename2.jpg",
        },
    ]
