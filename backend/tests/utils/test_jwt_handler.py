from datetime import timedelta
from utils.jwt_handler import create_jwt_token, verify_jwt_token


def test_create_jwt_token_with_timedelta():
    res = create_jwt_token(
        {
            "uid": 1000,
            "uphone_number": "+628123456789",
        },
        expires_delta=timedelta(days=1),
    )
    assert res is not None


def test_create_jwt_token_without_timedelta():
    res = create_jwt_token(
        {
            "uid": 1000,
            "uphone_number": "+628123456789",
        },
    )
    assert res is not None


def test_verify_jwt_token():
    token = create_jwt_token(
        {
            "uid": 1000,
            "uphone_number": "+628123456789",
        },
        expires_delta=timedelta(days=1),
    )
    assert token is not None

    res = verify_jwt_token(token=token)
    assert res == {
        "uid": 1000,
        "uphone_number": "+628123456789",
        "exp": res.get("exp"),
    }
