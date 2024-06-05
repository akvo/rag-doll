from fastapi.testclient import TestClient


def test_send_login_link(client: TestClient) -> None:
    response = client.post("/login?phone_number=1234567890")
    assert response.status_code == 200
    content = response.json()
    assert content.split("/")[-2] == "verify"
    assert content.split("/")[-1] != ""
