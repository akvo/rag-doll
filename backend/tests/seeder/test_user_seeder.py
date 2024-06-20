from seeder.user_seeder import seed_users, interactive_seeder
from sqlalchemy.sql import text


def test_seed_users(session):
    # Test seeding users
    seed_users(3)  # Seed 3 users
    result = session.exec(text("SELECT COUNT(*) FROM \"user\""))
    assert result.scalar() > 3


def test_interactive_seeder(session, monkeypatch):
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
        "SELECT COUNT(*) FROM \"user\" WHERE phone_number = :phone_number"
    ).bindparams(phone_number=phone_number))
    assert result.scalar() == 1
