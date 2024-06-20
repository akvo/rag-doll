import json
from faker import Faker
from models.user import User
from models.client import Client, Client_Properties
from models.chat import Chat, Chat_Sender, Chat_Session
from seeder.session_local import get_session_local
from sqlalchemy.exc import IntegrityError


faker = Faker()


def get_last_user():
    session = get_session_local()
    try:
        last_user = session.query(User).order_by(User.id.desc()).first()
        return last_user
    finally:
        session.close()


def create_client():
    # Generate a random phone number for the client
    phone_number = faker.phone_number()
    client = Client(
        phone_number=int("".join(filter(str.isdigit, phone_number))))

    session = get_session_local()
    try:
        session.add(client)
        session.flush()  # Flush to generate client.id

        # Create Client_Properties with the generated client.id
        client_properties = Client_Properties(
            client_id=client.id, name=faker.name())
        session.add(client_properties)

        session.commit()
        return client.id
    except IntegrityError:
        session.rollback()
        return None
    finally:
        session.close()


def seed_chat_data(user_id, client_id):
    session = get_session_local()
    try:
        # Create a chat session
        chat_session = Chat_Session(user_id=user_id, client_id=client_id)
        session.add(chat_session)
        session.commit()

        # Load conversation demo from JSON
        # (assuming conversation_demo.json is in the seeder folder)
        json_path = "seeder/conversation_demo.json"
        with open(json_path, "r") as f:
            conversation_data = json.load(f)

        for message_data in conversation_data:
            message = message_data["message"]
            sender = message_data["sender"]

            # Determine sender type
            if sender == "user":
                chat_sender = Chat_Sender.USER
            elif sender == "client":
                chat_sender = Chat_Sender.CLIENT
            elif sender == "system":
                chat_sender = Chat_Sender.SYSTEM

            # Create Chat object
            chat = Chat(
                chat_session_id=chat_session.id,
                message=message,
                sender=chat_sender,
            )
            session.add(chat)

        session.commit()
        print("Chat data seeded successfully.")
    finally:
        session.close()


if __name__ == "__main__":
    # Get the last user
    last_user = get_last_user()
    if last_user:
        user_id = last_user.id
    else:
        print("No users found in the database.")
        exit()

    # Create a client and get client_id
    client_id = create_client()
    if not client_id:
        print("Client creation failed. Exiting.")
        exit()

    # Seed chat data
    seed_chat_data(user_id, client_id)
