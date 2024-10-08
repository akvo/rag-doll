import pytest
from seeder.user import (
    seed_users,
    interactive_seeder,
    validate_phone_number,
    User,
    User_Properties,
)
from sqlmodel import Session, select
from pydantic import ValidationError


def validate_phone_number_with_wrong_phone_number(session: Session):
    validate_phone_number(phone_number="+999")
    with pytest.raises(ValidationError):
        interactive_seeder(session=session)


def test_seed_users(session: Session):
    # Test seeding users
    seed_users(session=session, count=10)
    result = session.exec(select(User)).all()
    assert len(result) > 0


def test_interactive_seeder(session: Session, monkeypatch):
    # Simulate user input for interactive seeder
    user_input = [
        "+12345678909",  # Phone number
        "y",  # User has properties
        "John Doe",  # Name
    ]
    monkeypatch.setattr("builtins.input", lambda _: user_input.pop(0))

    interactive_seeder(session=session)

    phone_number = "+12345678909"
    result = session.exec(
        select(User).where(
            User.phone_number
            == int("".join(filter(str.isdigit, phone_number)))
        )
    ).one()
    assert result.phone_number == int(
        "".join(filter(str.isdigit, phone_number))
    )

    user_id = result.id
    result_up = session.exec(
        select(User_Properties).where(User_Properties.user_id == user_id)
    ).first()
    assert result_up.name == "John Doe"
