import phonenumbers
from os import environ
from fastapi import APIRouter, HTTPException, Depends, Form, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPBasicCredentials as credentials
from sqlmodel import Session, select, and_

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
from datetime import datetime, timezone
from utils.util import (
    generate_message_template_lang_by_phone_number,
    get_template_content_from_json,
)


router = APIRouter()
security = HTTPBearer()

INITIAL_CHAT_TEMPLATE = environ.get(
    "INITIAL_CHAT_TEMPLATE",
    "Hi {farmer_name}, I'm {officer_name} the extension officer.",
)
twilio_client = TwilioClient()
tz = timezone.utc


@router.post("/client")
async def add_client(
    name: Annotated[str, Form()],
    phone_number: Annotated[PhoneNumber, Form()],
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    auth: credentials = Depends(security),
):
    TESTING = environ.get("TESTING")
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

    # get message template ID
    message_template_lang = generate_message_template_lang_by_phone_number(
        phone_number=phone_number
    )
    content_sid = environ.get(f"INTRO_TEMPLATE_ID_{message_template_lang}")
    # get message template from twilio
    template_content = get_template_content_from_json(content_sid=content_sid)
    if template_content and not TESTING:
        initial_message = template_content.replace("{{1}}", name)
        initial_message = initial_message.replace("{{2}}", user_name)

    client = session.exec(
        select(Client).where(Client.phone_number == phone_number)
    ).first()

    if client:
        current_chat_session = session.exec(
            select(Chat_Session).where(
                and_(
                    Chat_Session.user_id == user.id,
                    Chat_Session.client_id == client.id,
                )
            )
        ).first()
        if current_chat_session:
            raise HTTPException(
                status_code=409,
                detail=client.serialize(),
            )
        # client found in different chat session
        content = "Client is already registered and "
        content += "assigned to a different extension officer."
        raise HTTPException(
            status_code=403,
            detail=content,
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
        created_at=datetime.now(tz),
    )
    session.add(new_chat)
    session.commit()
    # eol create new chat session
    session.flush()

    if TESTING:
        return new_chat.serialize()

    # send initial chat to client
    if content_sid:
        # send message with template
        background_tasks.add_task(
            twilio_client.whatsapp_message_template_create,
            to=phone_number,
            content_variables={"1": name, "2": user_name},
            content_sid=content_sid,
        )
    else:
        # send message without template
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
