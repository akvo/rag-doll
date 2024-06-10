from fastapi.testclient import TestClient


def test_send_login_link(client: TestClient) -> None:
    response = client.post("/login?phone_number=999")
    assert response.status_code == 200
    content = response.json()
    assert content.split("/")[-2] == "verify"
    assert content.split("/")[-1] != ""


def test_verify_login_link(client: TestClient) -> None:
    response = client.post("/login?phone_number=999")
    assert response.status_code == 200
    content = response.json()
    verification_uuid = content.split("/")[-1]
    response = client.get(f"/verify/{verification_uuid}")
    assert response.status_code == 200
    content = response.json()
    assert "token" in content


def test_verify_login_link_invalid_uuid(client: TestClient) -> None:
    response = client.get("/verify/invalid_uuid")
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "Invalid verification UUID"
