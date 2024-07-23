from sqlmodel import Session, select
from clients.twilio_client import (
    save_chat_history,
    Sender_Role_Enum,
    Platform_Enum,
    Chat_Session,
    ClientModel,
    User,
    Chat,
)


def test_save_chat_history_when_send_a_message_into_platform(session: Session):
    conversation = session.exec(select(Chat_Session)).first()
    client = session.exec(
        select(ClientModel).where(ClientModel.id == conversation.client_id)
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
    }

    result = save_chat_history(
        session=session,
        conversation_envelope=conversation_envelope,
        message_body="Saved message",
    )

    assert result is not None
    chat = session.exec(select(Chat).where(Chat.id == result)).first()
    assert chat.message == "Saved message"
    assert chat.sender_role == Sender_Role_Enum.USER
