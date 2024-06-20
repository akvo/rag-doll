from seeder.user_seeder import seed_users, interactive_seeder
from sqlalchemy.sql import text
from sqlmodel import Session


def test_seed_users(session: Session):
    # Test seeding users
    seed_users(10)  # Seed 3 users
    result = session.exec(text("SELECT COUNT(*) FROM \"user\""))
    assert result.scalar() > 10
    result_up = session.exec(text("SELECT COUNT(*) FROM \"user_properties\""))
    assert result_up.scalar() > 0


def test_interactive_seeder(session: Session, monkeypatch):
    # Simulate user input for interactive seeder
    user_input = [
        "123456789",  # Phone number
        "y",           # User has properties
        "John Doe",    # Name
        "john.doe@example.com",  # Email
    ]
    monkeypatch.setattr('builtins.input', lambda _: user_input.pop(0))
    interactive_seeder()
    phone_number = "123456789"
    result = session.exec(text(
        "SELECT * FROM \"user\" WHERE phone_number = :phone_number"
    ).bindparams(phone_number=phone_number)).fetchall()
    assert len(result) == 1
    user_id = result[0].id
    result_up = session.exec(text(
        "SELECT COUNT(*) FROM \"user_properties\" WHERE user_id = :user_id"
    ).bindparams(user_id=user_id))
    assert result_up.scalar() > 0
