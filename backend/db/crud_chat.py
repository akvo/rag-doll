from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select
from models import Chat, Chat_Media, Sender_Role_Enum, Chat_Session


tz = timezone.utc


def add_media(session: Session, chat: Chat, media: list[dict]):
    media_objects = [
        Chat_Media(chat_id=chat.id, url=md.get("url"), type=md.get("type"))
        for md in media
    ]
    session.add_all(media_objects)
    session.commit()


def get_last_message(session: Session, chat: Chat):
    last_message = session.exec(
        select(Chat)
        .where(Chat.chat_session_id == chat.id)
        .where(
            Chat.sender_role != Sender_Role_Enum.ASSISTANT,
        )
        .order_by(Chat.created_at.desc(), Chat.id.desc())
    ).first()
    return last_message


def check_24h_window(session: Session):
    # TODO :: run as backgorund task
    # We also need to add an option for farmer
    # to choose to stop receive automated message
    current_time = datetime.now(tz)
    chats = session.exec(select(Chat_Session)).all()
    for chat in chats:
        last_message = get_last_message(session=session, chat=chat)
        # add UTC format to created_at
        time_diff = current_time - last_message.created_at.replace(tzinfo=tz)
        if time_diff >= timedelta(hours=24):
            # TODO :: send_template_message here
            print(last_message.message, chat.id)
