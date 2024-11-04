from fastapi.testclient import TestClient
from sqlmodel import Session, select
from models import User, Client


def test_get_phone_number_in_international_format(session: Session) -> None:
    user = session.exec(
        select(User).where(User.phone_number == "+12345678900")
    ).first()
    assert str(user) == "+12345678900"
    assert user.serialize() == {
        "id": user.id,
        "phone_number": "+12345678900",
        "name": None,
    }

    client = session.exec(
        select(Client).where(Client.phone_number == "+6281234567890")
    ).first()
    assert str(client) == "+6281234567890"
    assert client.serialize() == {
        "id": client.id,
        "name": "John Doe",
        "phone_number": "+6281234567890",
    }


def test_send_login_link(client: TestClient, session: Session) -> None:
    response = client.post("/login?phone_number=%2B12345678900")
    assert response.status_code == 200

    user = session.exec(
        select(User).where(User.phone_number == "+12345678900")
    ).first()
    assert user.login_code is not None


def test_verify_login_link(client: TestClient, session: Session) -> None:
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
    assert "phone_number" in content
    assert "name" in content

    response = client.get(f"/verify/{verification_uuid}")
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "Invalid verification UUID"


def test_phone_number_must_start_with_plus_sign(client: TestClient) -> None:
    response = client.post("/login?phone_number=12345678900")
    assert response.status_code == 422
    content = response.json()
    assert content["detail"] == [
        {
            "input": "12345678900",
            "loc": ["query", "phone_number"],
            "msg": "value is not a valid phone number",
            "type": "value_error",
        }
    ]


def test_verify_login_link_invalid_uuid(client: TestClient) -> None:
    response = client.get("/verify/invalid_uuid")
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "Invalid verification UUID"


def test_user_set_phone_number_strips_plus_sign(session: Session) -> None:
    user = User(phone_number="+12345678901")
    session.add(user)
    session.commit()
    session.refresh(user)
    assert user.phone_number == 12345678901
    assert str(user) == "+12345678901"
    assert user.serialize() == {
        "id": user.id,
        "phone_number": "+12345678901",
        "name": None,
    }


def test_user_invalid_phone_number_with_invalid_characters(
    session: Session,
) -> None:
    invalid_phone_numbers = ["+123 45", "+123-45", "+123#45"]
    for phone_number in invalid_phone_numbers:
        try:
            user = User(phone_number=phone_number)
            session.add(user)
            session.commit()
            assert (
                False
            ), f"Expected ValueError for phone number {phone_number}"
        except ValueError as e:
            assert str(e) == "Phone number contains invalid characters"


def test_client_set_phone_number_strips_plus_sign(session: Session) -> None:
    client = Client(phone_number="+12345")
    session.add(client)
    session.commit()
    session.refresh(client)
    assert client.phone_number == 12345
    assert str(client) == "+12345"
    assert client.serialize() == {
        "id": client.id,
        "name": None,
        "phone_number": "+12345",
    }


def test_client_invalid_phone_number_with_invalid_characters(
    session: Session,
) -> None:
    invalid_phone_numbers = ["+123 45", "+123-45", "+123#45"]
    for phone_number in invalid_phone_numbers:
        try:
            client = Client(phone_number=phone_number)
            session.add(client)
            session.commit()
            assert (
                False
            ), f"Expected ValueError for phone number {phone_number}"
        except ValueError as e:
            assert str(e) == "Phone number contains invalid characters"


def test_get_user_me(client: TestClient, session: Session) -> None:
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

    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    content = response.json()
    clients = content["clients"]
    assert len(clients) > 0
    assert "id" in clients[0]
    assert "name" in clients[0]
    assert "phone_number" in clients[0]
    user = user.serialize()
    user.update({"clients": clients})
    assert content == user
