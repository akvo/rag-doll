import json

from fastapi.testclient import TestClient
from models import User, Subscription
from sqlmodel import Session, select


SUBSCRIPTION_EXAMPLE = {
    "endpoint": "https://fcm.googleapis.com/fcm/send/uniquesubcriptionendpoint",
    "expirationTime": None,
    "keys": {
        "p256dh": "keytoencryptmessage",
        "auth": "authsecret",
    },
}


def test_subscribe(client: TestClient, session: Session):
    # Log in and obtain a token
    response = client.post("/login?phone_number=%2B12345678900")
    assert response.status_code == 200

    user = session.exec(
        select(User).where(User.phone_number == "+12345678900")
    ).first()
    verification_uuid = user.login_code

    # Verify the login to get the token
    response = client.get(f"/verify/{verification_uuid}")
    assert response.status_code == 200
    content = response.json()
    assert "token" in content
    token = content["token"]

    # Send the subscription data to the /subscribe endpoint
    response = client.post(
        "/subscribe",
        json=SUBSCRIPTION_EXAMPLE,
        headers={"Authorization": f"Bearer {token}"},
    )

    # Check if the subscription was successfully received
    assert response.status_code == 200
    assert response.json() == {"message": "Subscription received"}

    # Verify the subscription was saved in the database
    saved_subscription = session.exec(
        select(Subscription).where(
            Subscription.endpoint == SUBSCRIPTION_EXAMPLE["endpoint"]
        )
    ).first()

    assert saved_subscription is not None
    assert saved_subscription.keys == json.dumps(SUBSCRIPTION_EXAMPLE["keys"])
