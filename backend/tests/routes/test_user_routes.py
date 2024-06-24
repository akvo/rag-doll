from fastapi.testclient import TestClient
from sqlmodel import Session, select
from models import User, Client


def test_get_phone_number_in_international_format(session: Session) -> None:
    user = session.exec(select(User).where(User.phone_number == "+999")).first()
    assert str(user) == "+999"
    assert user.serialize() == {
        "id": user.id,
        "phone_number": "+999",
        "login_code": None,
    }

    client = session.exec(
        select(Client).where(Client.phone_number == "+998")
    ).first()
    assert str(client) == "+998"
    assert client.serialize() == {
        "id": client.id,
        "phone_number": "+998",
    }


def test_send_login_link(client: TestClient) -> None:
    response = client.post("/login?phone_number=%2B999")
    assert response.status_code == 200
    content = response.json()
    assert content.split("/")[-2] == "verify"
    assert content.split("/")[-1] != ""


def test_verify_login_link(client: TestClient, session: Session) -> None:
    response = client.post("/login?phone_number=%2B999")
    assert response.status_code == 200
    content = response.json()
    verification_uuid = content.split("/")[-1]
    response = client.get(f"/verify/{verification_uuid}")
    assert response.status_code == 200
    content = response.json()
    assert "token" in content
    response = client.get(f"/verify/{verification_uuid}")
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "Invalid verification UUID"
    user = session.exec(select(User).where(User.phone_number == "+999")).first()
    assert user.login_code is None


def test_phone_number_must_start_with_plus_sign(client: TestClient) -> None:
    response = client.post("/login?phone_number=999")
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "Phone number must start with +"


def test_verify_login_link_invalid_uuid(client: TestClient) -> None:
    response = client.get("/verify/invalid_uuid")
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "Invalid verification UUID"


def test_user_set_phone_number_strips_plus_sign(session: Session) -> None:
    user = User(phone_number="+12345")
    session.add(user)
    session.commit()
    session.refresh(user)
    assert user.phone_number == 12345
    assert str(user) == "+12345"
    assert user.serialize() == {
        "id": user.id,
        "phone_number": "+12345",
        "login_code": None,
    }


def test_user_invalid_phone_number_with_invalid_characters(
    session: Session
) -> None:
    invalid_phone_numbers = ["+123 45", "+123-45", "+123#45"]
    for phone_number in invalid_phone_numbers:
        try:
            user = User(phone_number=phone_number)
            session.add(user)
            session.commit()
            assert False, f"Expected ValueError for phone number {phone_number}"
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
        "phone_number": "+12345",
    }


def test_client_invalid_phone_number_with_invalid_characters(
    session: Session
) -> None:
    invalid_phone_numbers = ["+123 45", "+123-45", "+123#45"]
    for phone_number in invalid_phone_numbers:
        try:
            client = Client(phone_number=phone_number)
            session.add(client)
            session.commit()
            assert False, f"Expected ValueError for phone number {phone_number}"
        except ValueError as e:
            assert str(e) == "Phone number contains invalid characters"
