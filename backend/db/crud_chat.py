from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select
from models import Chat, Chat_Media, Sender_Role_Enum


tz = timezone.utc


def add_media(session: Session, chat: Chat, media: list[dict]):
    media_objects = [
        Chat_Media(chat_id=chat.id, url=md.get("url"), type=md.get("type"))
        for md in media
    ]
    session.add_all(media_objects)
    session.commit()


def check_24h_window(session: Session, chat_session_id: int):
    current_time = datetime.now(tz)
    last_message = session.exec(
        select(Chat)
        .where(Chat.chat_session_id == chat_session_id)
        .where(
            Chat.sender_role != Sender_Role_Enum.ASSISTANT,
        )
        .order_by(Chat.created_at.desc(), Chat.id.desc())
    ).first()
    # add UTC format to created_at
    time_diff = current_time - last_message.created_at.replace(tzinfo=tz)
    if time_diff >= timedelta(hours=24):
        return True
    return False
