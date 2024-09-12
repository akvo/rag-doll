import os
import re
import sys
from faker import Faker
from pydantic import BaseModel, ValidationError
from pydantic_extra_types.phone_numbers import PhoneNumber
from models.user import User, User_Properties
from core.database import engine
from sqlmodel import Session


faker = Faker(["en_US"])


class ValidatePhoneNumber(BaseModel):
    phone_number: PhoneNumber


def validate_phone_number(phone_number: str):
    try:
        validated_data = ValidatePhoneNumber(phone_number=phone_number)
        return int("".join(filter(str.isdigit, validated_data.phone_number)))
    except ValidationError as e:
        print(f"Validation error for phone number {phone_number}: {e}")
        return None


def save_user(session: Session, phone_number: str, name: str = None):
    validated_phone_number = validate_phone_number(phone_number)
    if validated_phone_number is None:
        return None

    user = User(phone_number=validated_phone_number, login_code=None)
    session.add(user)
    session.flush()

    if name:
        user_properties = User_Properties(user_id=user.id, name=name)
        session.add(user_properties)
    session.commit()
    print(f"Seeded user {user.id} with phone number {phone_number}")


def seed_users(session: Session, count: int):
    try:
        for _ in range(count):
            phone_number = faker.phone_number()
            phone_number = f"+{re.sub(r'\D', '', phone_number)}"
            save_user(
                session=session, phone_number=phone_number, name=faker.name
            )
    finally:
        session.close()
        print("Seeder process completed.")


def interactive_seeder(session: Session):
    try:
        phone_number = input("Enter phone number: ")
        name = None
        if input("Does the user have properties? (y/n): ").lower() == "y":
            name = input("Enter name: ")
        save_user(session=session, phone_number=phone_number, name=name)
    except ValidationError as e:
        print(f"Validation error for phone number {phone_number}: {e}")
        if os.getenv("TESTING"):
            raise e
    finally:
        session.close()
        print("Seeder process completed.")


if __name__ == "__main__":
    session = Session(engine)

    if "-i" in sys.argv:
        interactive_seeder(session)
    else:
        count = int(input("How many users do you want to seed? "))
        seed_users(session, count)
