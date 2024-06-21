from faker import Faker
from models.user import User, User_Properties
from core.database import engine
from sqlmodel import Session


faker = Faker()


def seed_users(session: Session, count: int):
    try:
        for _ in range(count):
            phone_number = faker.phone_number()
            user = User(
                phone_number=int("".join(filter(str.isdigit, phone_number))),
                login_code=None,
            )

            session.add(user)
            session.flush()  # Flush to get the user ID

            if faker.boolean():
                name = faker.name()
                email = faker.email()
                user_properties = User_Properties(
                    user_id=user.id, name=name, email=email
                )
                session.add(user_properties)

            session.commit()
            print(f"Seeded user {user.id} with phone number {phone_number}")

    finally:
        session.close()
        print("Seeder process completed.")


def interactive_seeder(session: Session):
    try:
        phone_number = input("Enter phone number: ")
        user = User(
            phone_number=int("".join(filter(str.isdigit, phone_number))),
            login_code=None,
        )
        session.add(user)
        session.flush()  # Flush to get the user ID

        if input("Does the user have properties? (y/n): ").lower() == "y":
            name = input("Enter name: ")
            email = input("Enter email: ")
            user_properties = User_Properties(
                user_id=user.id, name=name, email=email
            )
            session.add(user_properties)

        session.commit()
        print(f"Seeded user {user.id} with phone number {phone_number}")
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
