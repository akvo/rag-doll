import pytest

from sqlmodel import Session, select
from core.socketio_config import resend_messages, Chat_Session, Chat


@pytest.mark.asyncio
async def test_resend_messages_chat_session_exist(session: Session):
    chat = session.exec(select(Chat)).first()
    chat_session = session.exec(
        select(Chat_Session).where(Chat_Session.id == chat.chat_session_id)
    ).first()

    res = await resend_messages(
        session=session, user_id=chat_session.user_id, user_sid="userSid"
    )

    assert res is not None
    assert len(res) > 0


@pytest.mark.asyncio
async def test_resend_messages_chat_session_not_exist(session: Session):
    res = await resend_messages(session=session, user_id=0, user_sid="userSid")
    assert res is None
