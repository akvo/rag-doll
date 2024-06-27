from seeder.user import (
    seed_users,
    interactive_seeder,
    User,
    User_Properties
)
from sqlmodel import Session, select


def test_seed_users(session: Session):
    # Test seeding users
    seed_users(session=session, count=10)
    result = session.exec(select(User)).all()
    assert len(result) > 10
    result_up = session.exec(select(User_Properties)).all()
    assert len(result_up) > 0


def test_interactive_seeder(session: Session, monkeypatch):
    # Simulate user input for interactive seeder
    user_input = [
        "+12345678909",  # Phone number
        "y",           # User has properties
        "John Doe",    # Name
        "john.doe@example.com",  # Email
    ]
    monkeypatch.setattr('builtins.input', lambda _: user_input.pop(0))

    interactive_seeder(session=session)

    phone_number = "+12345678909"
    result = session.exec(
        select(User).where(User.phone_number == phone_number)).one()
    assert result.phone_number == int(phone_number)

    user_id = result.id
    result_up = session.exec(
        select(User_Properties).where(User_Properties.user_id == user_id)
    ).first()
    assert result_up.name == "John Doe"
    assert result_up.email == "john.doe@example.com"
