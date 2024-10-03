from sqlmodel import Session, select
from core.socketio_config import (
    get_chat_history_for_assistant,
    Chat,
)


def test_get_chat_history_for_assistant_if_chat_session_exist(
    session: Session,
):
    chat = session.exec(select(Chat)).first()

    res = get_chat_history_for_assistant(
        session=session, chat_session_id=chat.chat_session_id
    )

    assert res is not None
    assert len(res) > 0
    assert res == [
        {"role": "user", "content": "Yes, I need help with something."},
        {
            "role": "assistant",
            "content": "Is there anything I can help you with?",
        },
        {"role": "assistant", "content": "Hello, +62 812 3456 7890"},
        {"role": "user", "content": "Hello Admin!"},
    ]


def test_get_chat_history_for_assistant_if_chat_session_not_exist(
    session: Session,
):
    res = get_chat_history_for_assistant(session=session, chat_session_id=0)
    assert res is None
