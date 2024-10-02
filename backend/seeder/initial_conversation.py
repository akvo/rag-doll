from faker import Faker
from models.user import User
from models.client import Client
from models.chat import Chat, Sender_Role_Enum, Chat_Session, Platform_Enum
from sqlalchemy.exc import IntegrityError
from core.database import engine
from sqlmodel import Session, select
from typing import List


faker = Faker()


def get_client_phone_numbers(session: Session):
    clients = session.exec(select(Client)).all()
    if not clients:
        return []
    return [c.phone_number for c in clients]


def get_users(session: Session, phone_numbers: List):
    users = session.exec(
        select(User).where(User.phone_number.notin_(phone_numbers))
    ).all()
    return users


def create_client(session: Session, user: User):
    client = Client(phone_number=user.phone_number)
    try:
        session.add(client)
        session.flush()
        session.commit()
        return client.id
    except IntegrityError:
        session.rollback()
        return None


def seed_chat_data(session: Session, user_id: int, client_id: int):
    # Create a chat session
    chat_session = Chat_Session(
        user_id=user_id, client_id=client_id, platform=Platform_Enum.WHATSAPP
    )
    session.add(chat_session)
    session.commit()
    # Create Chat object
    chat = Chat(
        chat_session_id=chat_session.id,
        message="Welcome to Agriconnect. This is initial conversation..",
        sender_role=Sender_Role_Enum.SYSTEM,
    )
    session.add(chat)
    session.commit()


if __name__ == "__main__":
    session = Session(engine)
    # Get clients
    client_phone_numbers = get_client_phone_numbers(session=session)

    # Get users
    users = get_users(session=session, phone_numbers=client_phone_numbers)
    if not users:
        print("No users found in the database.")
        exit()

    for user in users:
        # Create a client and get client_id
        client_id = create_client(session=session, user=user)
        if not client_id:
            print("Client creation failed. Exiting.")
            exit()
        # Seed initial chat data
        seed_chat_data(session=session, user_id=user.id, client_id=client_id)
    print("Initial chat seeded successfully.")

    session.close()
