from sqlmodel import Session
from models import Chat, Chat_Media


def add_media(session: Session, chat: Chat, media: list[dict]):
    media_objects = [
        Chat_Media(chat_id=chat.id, url=md.get("url"), type=md.get("type"))
        for md in media
    ]
    session.add_all(media_objects)
    session.commit()
