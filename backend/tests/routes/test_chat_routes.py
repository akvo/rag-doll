from fastapi.testclient import TestClient
from models import (
    Sender_Role_Enum,
    Chat_Session,
    User,
    Client,
    Chat,
    Chat_Status_Enum,
)
from sqlmodel import Session, select, and_


def test_get_chats(client: TestClient) -> None:
    response = client.get("/chat-list")
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not authenticated"


def test_get_chats_authenticated(client: TestClient, session: Session) -> None:
    response = client.post("/login?phone_number=%2B12345678900")
    assert response.status_code == 200

    user = session.exec(
        select(User).where(User.phone_number == "+12345678900")
    ).first()

    verification_uuid = user.login_code
    response = client.get(f"/verify/{verification_uuid}")
    assert response.status_code == 200
    content = response.json()
    assert "token" in content
    token = content["token"]

    response = client.get(
        "/chat-list", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    content = response.json()

    assert "total_chats" in content
    assert "chats" in content
    assert "limit" in content
    assert "offset" in content

    assert content["limit"] == 10
    assert content["offset"] == 0

    assert isinstance(content["chats"], list)
    assert len(content["chats"]) >= 1

    chat_session = content["chats"][0].get("chat_session")
    assert chat_session.get("id")
    assert chat_session.get("client_id")
    assert chat_session.get("phone_number")
    assert chat_session.get("last_read")

    # check with last message
    assert "unread_message_count" in content["chats"][0]
    assert "unread_assistant_message" in content["chats"][0]
    assert content["chats"][0]["unread_message_count"] == 1

    last_chat_message = content["chats"][0].get("last_message")
    assert last_chat_message is not None
    sender = last_chat_message.get("sender_role")
    assert sender == Sender_Role_Enum.CLIENT.value
    assert (
        last_chat_message.get("message") == "Yes, I need help with something."
    )


def test_get_chat_details_by_client_id(
    client: TestClient, session: Session
) -> None:
    response = client.post("/login?phone_number=%2B12345678900")
    assert response.status_code == 200

    user = session.exec(
        select(User).where(User.phone_number == "+12345678900")
    ).first()

    verification_uuid = user.login_code
    response = client.get(f"/verify/{verification_uuid}")
    assert response.status_code == 200
    content = response.json()
    assert "token" in content
    token = content["token"]

    cur_client = session.exec(
        select(Chat_Session).order_by(Chat_Session.client_id.desc())
    ).first()
    client_id = cur_client.client_id + 1
    response = client.get(
        f"/chat-details/{client_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404

    cur_client = session.exec(select(Chat_Session)).first()
    client_id = cur_client.client_id
    response = client.get(
        f"/chat-details/{client_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    content = response.json()

    assert content["client_id"] == client_id
    assert "chat_session" in content
    assert "messages" in content

    chat_session = content["chat_session"]
    assert chat_session.get("phone_number")
    assert chat_session.get("last_read")

    messages = content["messages"]
    assert isinstance(messages, list)
    assert len(messages) >= 1

    first_message = messages[0]
    assert first_message.get("message") is not None
    assert "sender_role" in first_message
    assert "media" in first_message


def test_send_broadcast_unauthorized(client: TestClient) -> None:
    response = client.post(
        "/send-broadcast",
        json={
            "contacts": ["+12345678901", "+12345678902"],
            "message": "Hello, this is a broadcast message.",
        },
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not authenticated"


def test_send_broadcast_success(client: TestClient, session: Session) -> None:
    # log in to get the token
    response = client.post("/login?phone_number=%2B12345678900")
    assert response.status_code == 200

    user = session.exec(
        select(User).where(User.phone_number == "+12345678900")
    ).first()

    verification_uuid = user.login_code
    response = client.get(f"/verify/{verification_uuid}")
    assert response.status_code == 200
    content = response.json()
    assert "token" in content
    token = content["token"]

    # Prepare test clients
    contacts = ["+12345678901", "+12345678902"]
    test_clients = [
        Client(phone_number=contacts[0]),
        Client(phone_number=contacts[1]),
    ]
    session.add_all(test_clients)
    session.commit()

    test_clients = session.exec(
        select(Client).where(Client.phone_number.in_(contacts))
    ).all()
    for contact in test_clients:
        assert contact.phone_number is not None

    # Send the broadcast message
    response = client.post(
        "/send-broadcast",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "contacts": contacts,
            "message": "Hello, this is a broadcast message.",
        },
    )
    assert response.status_code == 200

    # Verify that messages were saved in the database
    for contact in test_clients:
        chat_session = session.exec(
            select(Chat_Session).where(
                and_(
                    Chat_Session.client_id == contact.id,
                    Chat_Session.user_id == user.id,
                )
            )
        ).first()
        assert chat_session is not None

        # Check that the broadcast message was stored
        messages = session.exec(
            select(Chat).where(Chat.chat_session_id == chat_session.id)
        ).all()

        assert len(messages) > 0
        assert (
            messages[-1].message
            == "[Broadcast]\n\nHello, this is a broadcast message."
        )
        assert messages[-1].sender_role == Sender_Role_Enum.USER_BROADCAST
        assert messages[-1].status == Chat_Status_Enum.UNREAD
