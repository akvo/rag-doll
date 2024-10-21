from fastapi.testclient import TestClient
from sqlmodel import Session, select
from models import User, Client, Chat_Session, Chat, Chat_Status_Enum


# Sample data for tests
new_client_data = {
    "name": "Test Farmer",
    "phone_number": "+6281222345678",
}


def test_add_new_client_return_not_authorized(
    client: TestClient, session: Session
):
    response = client.post(
        "/client",
        data=new_client_data,
    )
    assert response.status_code == 403


def test_add_new_client(client: TestClient, session: Session):
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

    response = client.post(
        "/client",
        data=new_client_data,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    # Verify the client is saved in the database
    check_client = session.exec(
        select(Client).where(
            Client.phone_number == new_client_data["phone_number"]
        )
    ).first()
    assert check_client is not None
    res_client = check_client.serialize()
    assert res_client["phone_number"] == new_client_data["phone_number"]
    assert res_client["name"] == new_client_data["name"]

    # Verify that a chat session is created
    chat_session = session.exec(
        select(Chat_Session)
        .where(Chat_Session.client_id == check_client.id)
        .where(Chat_Session.user_id == user.id)
    ).first()
    assert chat_session is not None

    # Verify that the chat message is saved
    chat_message = session.exec(
        select(Chat).where(Chat.chat_session_id == chat_session.id)
    ).first()
    assert chat_message is not None
    assert chat_message.message.startswith(f"Hi {new_client_data["name"]}")
    assert chat_message.status == Chat_Status_Enum.READ


def test_add_new_client_with_registered_phone_number(
    client: TestClient, session: Session
):
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

    response = client.post(
        "/client",
        data=new_client_data,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409


def test_update_client_return_not_authorized(
    client: TestClient, session: Session
):
    response = client.put("/client/1000?name=John Doe Updated")
    assert response.status_code == 403


def test_update_client_return_404(client: TestClient, session: Session):
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

    response = client.put(
        "/client/1000?name=John Doe Updated",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_update_client(client: TestClient, session: Session):
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

    curr_client = session.exec(select(Client)).first()

    response = client.put(
        f"/client/{curr_client.id}?name=John Doe Updated",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == "John Doe Updated"

    # update same client
    response = client.put(
        f"/client/{curr_client.id}?name=John Doe",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == "John Doe"
