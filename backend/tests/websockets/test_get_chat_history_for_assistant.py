import json
from sqlmodel import Session, select
from core.socketio_config import (
    get_chat_history_for_assistant,
    Chat,
    Chat_Session,
    Client,
    User,
    Platform_Enum,
)


MESSAGE = {
    "conversation_envelope": {
        "message_id": "SM48e12712cab50ba0a061cf8058d6ed48",
        "client_phone_number": "+6281222304050",
        "user_phone_number": None,
        "sender_role": "client",
        "platform": "WHATSAPP",
        "timestamp": "2024-07-16T04:29:47.799230+00:00",
    },
    "body": "Message with history",
    "media": [],
    "context": [],
    "transformation_log": ["Message with history"],
}


def test_get_chat_history_for_assistant_if_chat_session_exist(
    session: Session,
):
    chat = session.exec(select(Chat)).first()

    res = get_chat_history_for_assistant(
        session=session,
        chat_session_id=chat.chat_session_id,
        body=json.dumps(MESSAGE),
    )

    assert res is not None
    res = json.loads(res)
    assert res == {
        "conversation_envelope": {
            "message_id": "SM48e12712cab50ba0a061cf8058d6ed48",
            "client_phone_number": "+6281222304050",
            "user_phone_number": None,
            "sender_role": "client",
            "platform": "WHATSAPP",
            "timestamp": "2024-07-16T04:29:47.799230+00:00",
        },
        "body": "Message with history",
        "media": [],
        "context": [],
        "transformation_log": ["Message with history"],
        "history": [
            {"role": "user", "content": "Hello Admin!"},
            {"role": "assistant", "content": "Hello, +62 812 3456 7890"},
            {
                "role": "assistant",
                "content": "Is there anything I can help you with?",
            },
        ],
    }


def test_get_chat_history_for_assistant_if_chat_session_not_exist(
    session: Session,
):
    res = get_chat_history_for_assistant(
        session=session,
        chat_session_id=0,
        body=json.dumps(MESSAGE),
    )
    assert res == json.dumps(MESSAGE)


def test_get_chat_history_for_assistant_if_chat_session_doesnt_have_chats(
    session: Session,
):
    user = session.exec(select(User)).first()

    new_client = Client(phone_number="+628923456789")
    session.add(new_client)
    session.commit()

    new_chat_session = Chat_Session(
        user_id=user.id,
        client_id=new_client.id,
        platform=Platform_Enum.WHATSAPP,
    )
    session.add(new_chat_session)
    session.commit()

    find_chat = session.exec(
        select(Chat).where(Chat.chat_session_id == new_chat_session.id)
    ).first()
    assert find_chat is None

    res = get_chat_history_for_assistant(
        session=session,
        chat_session_id=new_chat_session.id,
        body=json.dumps(MESSAGE),
    )
    assert res == json.dumps(MESSAGE)
