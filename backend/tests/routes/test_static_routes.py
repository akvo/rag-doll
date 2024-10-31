import json
import pytest

from fastapi.testclient import TestClient
from pathlib import Path

from routes.static_routes import router


# Define paths for valid and invalid JSON files
valid_policy_path = "./sources/static/data-retention-policy.json"
invalid_policy_path = "./sources/static/invalid-data-retention-policy.json"
missing_policy_path = "./sources/static/missing-data-retention-policy.json"

# Sample JSON data for valid policy content
sample_policy_data = [
    {
        "title": "Data Retention",
        "sections": [
            {
                "subtitle": "Retention Duration",
                "content": "Farmer and officer data is retained for a max...",
            }
        ],
    }
]


@pytest.fixture
def setup_valid_policy_file():
    # Set up a valid JSON policy file
    with open(valid_policy_path, "w") as file:
        json.dump(sample_policy_data, file)
    yield
    Path(valid_policy_path).unlink()


@pytest.fixture
def setup_invalid_policy_file():
    # Set up an invalid JSON policy file
    with open(invalid_policy_path, "w") as file:
        file.write("{invalid_json")
    yield
    Path(invalid_policy_path).unlink()


def test_get_policy_json_success(client: TestClient, monkeypatch):
    # Set up test environment with a valid policy file
    monkeypatch.setattr(router, "POLICY_FILE_PATH", valid_policy_path)
    response = client.get("/data-retention-policy")
    assert response.status_code == 200
    content = response.json()

    # Validate returned JSON content structure
    assert isinstance(content, list)
    assert content[0]["title"] == sample_policy_data[0]["title"]
    assert (
        content[0]["sections"][0]["subtitle"]
        == sample_policy_data[0]["sections"][0]["subtitle"]
    )
    assert (
        content[0]["sections"][0]["content"]
        == sample_policy_data[0]["sections"][0]["content"]
    )


def test_get_policy_json_file_not_found(client: TestClient, monkeypatch):
    # Simulate missing file by pointing to a non-existing path
    monkeypatch.setattr(router, "POLICY_FILE_PATH", missing_policy_path)
    response = client.get("/data-retention-policy")
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Policy file not found"


def test_get_policy_json_invalid_json_format(client: TestClient, monkeypatch):
    # Simulate invalid JSON by pointing to an improperly formatted file
    monkeypatch.setattr(router, "POLICY_FILE_PATH", invalid_policy_path)
    response = client.get("/data-retention-policy")
    assert response.status_code == 500
    content = response.json()
    assert content["detail"] == "Error decoding policy JSON"
