import phonenumbers
from os import environ
from fastapi import APIRouter, HTTPException, Depends, Form
from fastapi.security import HTTPBearer, HTTPBasicCredentials as credentials
from sqlmodel import Session, select

from pydantic_extra_types.phone_numbers import PhoneNumber
from models import (
    Client,
    Client_Properties,
    Chat_Session,
    Chat,
    Sender_Role_Enum,
)
from core.database import get_session
from clients.twilio_client import TwilioClient
from middleware import verify_user
from typing_extensions import Annotated


router = APIRouter()
security = HTTPBearer()

webdomain = environ.get("WEBDOMAIN")
INITIAL_CHAT_TEMPLATE = environ.get("INITIAL_CHAT_TEMPLATE")

twilio_client = TwilioClient()


@router.post("/client")
async def add_client(
    name: Annotated[str, Form()],
    phone_number: Annotated[PhoneNumber, Form()],
    session: Session = Depends(get_session),
    auth: credentials = Depends(security),
):
    user = verify_user(session, auth)
    phone_number = phonenumbers.parse(phone_number)
    phone_number = (
        f"+{phone_number.country_code}{phone_number.national_number}"
    )
    client = session.exec(
        select(Client).where(Client.phone_number == phone_number)
    ).first()
    if client:
        raise HTTPException(
            status_code=409,
            detail=f"Client {phone_number} already registered.",
        )

    # save client
    new_client = Client(phone_number=phone_number)
    session.add(new_client)
    session.commit()

    new_client_properties = Client_Properties(
        client_id=new_client.id, name=name
    )
    session.add(new_client_properties)
    session.commit()
    # eol save client

    # format initial message for the client
    initial_message = INITIAL_CHAT_TEMPLATE.format(farmer_name=name)

    # create new chat session
    new_chat_session = Chat_Session(user_id=user.id, client_id=new_client.id)
    session.add(new_chat_session)
    session.commit()

    new_chat = Chat(
        chat_session_id=new_chat_session.id,
        message=initial_message,
        sender_role=Sender_Role_Enum.SYSTEM,
    )
    session.add(new_chat)
    session.commit()
    # eol create new chat session
    session.flush()

    if environ.get("TESTING"):
        return new_client.serialize()

    # send initial chat to client
    twilio_client.whatsapp_message_create(
        to=phone_number, body=initial_message
    )
    return new_client.serialize()
