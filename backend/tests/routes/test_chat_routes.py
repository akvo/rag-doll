from fastapi.testclient import TestClient
from models import Sender_Role_Enum


def test_get_chats(client: TestClient) -> None:
    response = client.get("/chat-list")
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not authenticated"


def test_get_chats_authenticated(client: TestClient) -> None:
    response = client.post("/login?phone_number=%2B12345678900")
    assert response.status_code == 200
    content = response.json()
    verification_uuid = content.split("/")[-1]
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
    assert len(content) == 1
    chat_session = content[0].get("chat_session")
    assert chat_session.get("phone_number")
    assert chat_session.get("last_read")
    last_chat_message = content[0].get("last_message")
    sender = content[0].get("last_message").get("sender_role")
    assert sender == Sender_Role_Enum.CLIENT.value
    assert (
        last_chat_message.get("message") == "Yes, I need help with something."
    )
