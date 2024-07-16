from sqlmodel import Session
from core.socketio_config import (
    check_conversation_exist_and_generate_queue_message,
    Sender_Role_Enum,
    Platform_Enum,
)


def test_check_conversation_exist_and_generate_queue_message(session: Session):
    msg = {
        "conversation_envelope": {
            "client_phone_number": "+6281234567890",
            "sender_role": "client",
            "platform": "WHATSAPP",
            "message_id": "12345",
        },
        "body": "Hello",
        "media": None,
        "context": None,
        "transformation_log": None,
    }

    result = check_conversation_exist_and_generate_queue_message(
        session=session, msg=msg, user_phone_number="+12345678900"
    )

    assert result is not None
    conversation_envelope = result["conversation_envelope"]
    assert conversation_envelope["message_id"] == "12345"
    assert conversation_envelope["client_phone_number"] == "+6281234567890"
    assert (
        conversation_envelope["sender_role"] == Sender_Role_Enum.CLIENT.value
    )
    assert conversation_envelope["platform"] == Platform_Enum.WHATSAPP.value
    assert result["body"] == "Hello"


def test_check_conversation_exist_and_generate_queue_message_no_conversation(
    session: Session,
):
    msg = {
        "conversation_envelope": {
            "client_phone_number": "+0987654321",
            "sender_role": "user",
            "platform": "WHATSAPP",
            "message_id": "12345",
        },
        "body": "Hello",
        "media": None,
        "context": None,
        "transformation_log": None,
    }

    result = check_conversation_exist_and_generate_queue_message(
        session=session, msg=msg, user_phone_number="+1234567890"
    )

    assert result is None
