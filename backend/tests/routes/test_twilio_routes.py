from fastapi.testclient import TestClient


def test_receive_whatsapp_message_from_wrong_phone_number(
    run_app, client: TestClient
) -> None:
    form_data = {
        "MessageSid": "test_sid",
        "From": "whatsapp:invalid_phone",
        "Body": "Test message",
    }
    response = client.post("/whatsapp", data=form_data)
    assert response.status_code == 400
    assert "Invalid phone number" in response.text


def test_receive_whatsapp_message(run_app, client: TestClient) -> None:
    form_data = {
        "MessageSid": "test_sid",
        "From": "whatsapp:+6281234567890",
        "Body": "Test message",
    }
    response = client.post("/whatsapp", data=form_data)
    assert response.status_code == 204


def test_receive_whatsapp_message_format_error(
    run_app, client: TestClient
) -> None:
    form_data = {
        "sid": "test_sid",
        "from": "whatsapp:+6281234567890",
        "body": "Test message",
    }
    response = client.post("/whatsapp", data=form_data)
    assert response.status_code == 400
    assert "Validation error" in response.text


def test_receive_whatsapp_message_parsing_error(
    run_app, client: TestClient
) -> None:
    form_data = {
        "MessageSid": "test_sid",
        "From": "whatsapp:abcd",
        "Body": "Test message",
    }
    response = client.post("/whatsapp", data=form_data)
    assert response.status_code == 400
    assert "Phone number parsing error" in response.text


def test_receive_whatsapp_message_invalid_phone_number(
    run_app, client: TestClient
) -> None:
    form_data = {
        "MessageSid": "test_sid",
        "From": "whatsapp:+6281234567",
        "Body": "Test message",
    }
    response = client.post("/whatsapp", data=form_data)
    assert response.status_code == 400
    assert "Invalid phone number" in response.text


def test_receive_whatsapp_message_missing_field(
    run_app, client: TestClient
) -> None:
    form_data = {"From": "whatsapp:+6281234567890", "Body": "Test message"}
    response = client.post("/whatsapp", data=form_data)
    assert response.status_code == 400
    assert "Validation error" in response.text
