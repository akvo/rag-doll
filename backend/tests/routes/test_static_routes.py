import json

from fastapi.testclient import TestClient
from routes.static_routes import POLICY_FILE_PATH


def test_get_policy_json_success(client: TestClient):
    with open(POLICY_FILE_PATH, "r") as file:
        expected_content = json.load(file)

    response = client.get("/data-retention-policy")
    assert response.status_code == 200
    content = response.json()

    assert isinstance(content, list)
    assert content == expected_content
