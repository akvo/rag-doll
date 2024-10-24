import phonenumbers
from os import environ
from fastapi import APIRouter, HTTPException, Depends, Form, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPBasicCredentials as credentials
from sqlmodel import Session, select

from pydantic_extra_types.phone_numbers import PhoneNumber
from models import (
    Client,
    Client_Properties,
    Chat_Session,
    Chat,
    Sender_Role_Enum,
    Platform_Enum,
    Chat_Status_Enum,
)
from core.database import get_session
from clients.twilio_client import TwilioClient
from middleware import verify_user
from typing_extensions import Annotated


router = APIRouter()
security = HTTPBearer()

INITIAL_CHAT_TEMPLATE = environ.get(
    "INITIAL_CHAT_TEMPLATE",
    "Hi {farmer_name}, I'm {officer_name} the extension officer.",
)
twilio_client = TwilioClient()


@router.post("/client")
async def add_client(
    name: Annotated[str, Form()],
    phone_number: Annotated[PhoneNumber, Form()],
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    auth: credentials = Depends(security),
):
    user = verify_user(session, auth)

    # format initial message for the client
    user_name = user.properties.name if user.properties else user.phone_number
    initial_message = INITIAL_CHAT_TEMPLATE.format(
        farmer_name=name, officer_name=user_name
    )

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
            detail=client.serialize(),
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

    # create new chat session
    new_chat_session = Chat_Session(
        user_id=user.id,
        client_id=new_client.id,
        platform=Platform_Enum.WHATSAPP,
    )
    session.add(new_chat_session)
    session.commit()

    new_chat = Chat(
        chat_session_id=new_chat_session.id,
        message=initial_message,
        sender_role=Sender_Role_Enum.SYSTEM,
        status=Chat_Status_Enum.READ,  # user/officer message mark as READ
    )
    session.add(new_chat)
    session.commit()
    # eol create new chat session
    session.flush()

    if environ.get("TESTING"):
        return new_client.serialize()

    # send initial chat to client
    background_tasks.add_task(
        twilio_client.whatsapp_message_create,
        to=phone_number,
        body=initial_message,
    )
    return new_client.serialize()


@router.put("/client/{client_id}")
async def update_client(
    client_id: int,
    name: str,
    session: Session = Depends(get_session),
    auth: credentials = Depends(security),
):
    verify_user(session, auth)
    curr_client = session.exec(
        select(Client).where(Client.id == client_id)
    ).first()
    if not curr_client:
        raise HTTPException(
            status_code=404, detail=f"Client {client_id} not found"
        )
    # create or update the details
    curr_client_properties = session.exec(
        select(Client_Properties).where(
            Client_Properties.client_id == curr_client.id
        )
    ).first()
    if not curr_client_properties:
        new_client_properties = Client_Properties(
            client_id=curr_client.id, name=name
        )
        session.add(new_client_properties)
    else:
        curr_client_properties.name = name
    session.commit()
    session.flush()
    return curr_client.serialize()
