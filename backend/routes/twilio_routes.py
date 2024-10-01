import logging
import asyncio
import json

from fastapi import (
    APIRouter,
    Request,
    HTTPException,
    Response,
    status,
    Depends,
    BackgroundTasks,
)
from fastapi.security import HTTPBearer
from pydantic import ValidationError
from clients.twilio_client import (
    IncomingMessage,
    TwilioClient,
    ALLOWED_MESSAGE_TYPES,
)
from core.socketio_config import client_to_user


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


def get_twilio_client():
    return TwilioClient()


@router.post("/whatsapp")
async def receive_whatsapp_message(
    request: Request,
    background_tasks: BackgroundTasks,
    twilio_client=Depends(get_twilio_client),
):
    try:
        form_data = await request.form()
        values = {key: form_data[key] for key in form_data}
        data = IncomingMessage(
            MessageSid=values.get("MessageSid"),
            From=values.get("From"),
            Body=values.get("Body"),
            NumMedia=int(values.get("NumMedia", 0)),
        )
        values.update(data.model_dump())
        body = twilio_client.format_to_queue_message(values)
        # BEGIN repy directly with a notification
        message_type = values["MessageType"]
        if message_type not in ALLOWED_MESSAGE_TYPES:
            body = json.loads(body)
            background_tasks.add_task(
                twilio_client.whatsapp_message_create,
                to=body["conversation_envelope"].get("client_phone_number"),
                body=f"This ({message_type}) media type is not yet supported.",
            )
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        # END repy directly with a notification
        asyncio.create_task(client_to_user(body=body))
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {e}",
        )

    except ValueError as e:
        logger.error(f"Invalid phone number or message format: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid phone number or message format: {e}",
        )

    except Exception as e:
        logger.error(f"Error receiving Whatsapp message: {values}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}",
        )
