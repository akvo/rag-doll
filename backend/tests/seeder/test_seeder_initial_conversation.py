from seeder.initial_conversation import (
    create_client,
    seed_chat_data,
    get_client_phone_numbers,
    get_users,
    Client,
    Chat,
    Chat_Session,
)
from sqlmodel import Session, select, and_


def test_get_client_phone_numbers(session: Session):
    res = get_client_phone_numbers(session=session)
    assert res is not None


def test_get_users(session: Session):
    client_phone_numbers = get_client_phone_numbers(session=session)
    users = get_users(session=session, phone_numbers=client_phone_numbers)
    assert users is not None


def test_create_client(session: Session):
    client_phone_numbers = get_client_phone_numbers(session=session)
    users = get_users(session=session, phone_numbers=client_phone_numbers)
    create_client(session=session, user=users[0])
    result = session.exec(select(Client.id)).all()
    assert len(result) > 1


def test_seed_chat_data(session: Session):
    client_phone_numbers = get_client_phone_numbers(session=session)
    users = get_users(session=session, phone_numbers=client_phone_numbers)
    for user in users:
        client_id = create_client(session=session, user=user)
        seed_chat_data(session=session, user_id=user.id, client_id=client_id)

        chat_session = session.exec(
            select(Chat_Session).where(
                and_(
                    Chat_Session.user_id == user.id,
                    Chat_Session.client_id == client_id,
                )
            )
        ).first()
        assert chat_session is not None

        chat = session.exec(
            select(Chat).where(Chat.chat_session_id == chat_session.id)
        ).first()
        assert chat is not None
