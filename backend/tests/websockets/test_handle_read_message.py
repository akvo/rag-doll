from sqlmodel import Session, select
from core.socketio_config import handle_read_message, Chat, Chat_Status_Enum


def test_handle_read_message(session: Session):
    unread_message = session.exec(
        select(Chat).where(Chat.status == Chat_Status_Enum.UNREAD)
    ).first()
    assert unread_message is not None

    res = handle_read_message(
        session=session, chat_session_id=unread_message.chat_session_id
    )

    for r in res:
        assert r.status == Chat_Status_Enum.READ
