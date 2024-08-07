import re
import os

from faker import Faker
from models.user import User, User_Properties
from core.database import engine
from sqlmodel import Session
from pydantic import BaseModel, ValidationError
from pydantic_extra_types.phone_numbers import PhoneNumber


faker = Faker(["en_US"])


class UserCreateModel(BaseModel):
    phone_number: PhoneNumber


def seed_users(session: Session, count: int):
    try:
        for _ in range(count):
            phone_number = faker.phone_number()
            phone_number = re.sub(r"\D", "", phone_number)
            phone_number = f"+{phone_number}"
            try:
                user = User(
                    phone_number=int(
                        "".join(filter(str.isdigit, phone_number))
                    ),
                    login_code=None,
                )

                session.add(user)
                session.flush()  # Flush to get the user ID

                # User Properties
                name = faker.name()
                user_properties = User_Properties(user_id=user.id, name=name)
                session.add(user_properties)
                session.commit()
                print(
                    f"Seeded user {user.id} with phone number {phone_number}"
                )
            except ValidationError as e:
                print(f"Validation error for phone number {phone_number}: {e}")
    finally:
        session.close()
        print("Seeder process completed.")


def interactive_seeder(session: Session):
    try:
        phone_number = input("Enter phone number: ")
        try:
            validated_data = UserCreateModel(phone_number=phone_number)
            user = User(
                phone_number=int(
                    "".join(filter(str.isdigit, validated_data.phone_number))
                ),
                login_code=None,
            )
            session.add(user)
            session.flush()  # Flush to get the user ID

            if input("Does the user have properties? (y/n): ").lower() == "y":
                name = input("Enter name: ")
                user_properties = User_Properties(user_id=user.id, name=name)
                session.add(user_properties)

            session.commit()
            print(f"Seeded user {user.id} with phone number {phone_number}")
        except ValidationError as e:
            print(f"Validation error for phone number {phone_number}: {e}")
            if os.getenv("TESTING"):
                raise e
    finally:
        session.close()
        print("Seeder process completed.")


if __name__ == "__main__":
    import sys

    session = Session(engine)

    if "-i" in sys.argv:
        interactive_seeder(session=session)
    else:
        count = int(input("How many users do you want to seed? "))
        seed_users(session=session, count=count)

    session.close()
