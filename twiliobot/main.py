import os
import logging
import json
import asyncio
import phonenumbers

from datetime import datetime
from quart import Quart, request, make_response
from Akvo_rabbitmq_client import rabbitmq_client
from twiliobot_client import twiliobot_client
from pydantic import BaseModel, ValidationError
from pydantic_extra_types.phone_numbers import PhoneNumber

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Quart(__name__)


RABBITMQ_QUEUE_TWILIOBOT_REPLIES = os.getenv('RABBITMQ_QUEUE_TWILIOBOT_REPLIES')
RABBITMQ_QUEUE_USER_CHATS = os.getenv('RABBITMQ_QUEUE_USER_CHATS')


class IncomingMessage(BaseModel):
    MessageSid: str
    From: str
    Body: str
    NumMedia: int


class PhoneValidationModel(BaseModel):
    phone: PhoneNumber


# Helper function to validate and format phone numbers
def validate_and_format_phone_number(phone_number: str) -> str:
    try:
        parsed_number = phonenumbers.parse(phone_number)
        if not phonenumbers.is_valid_number(parsed_number):
            raise ValueError(f"Invalid phone number: {phone_number}")
        # Format the phone number
        formatted_number = phonenumbers.format_number(
            parsed_number, phonenumbers.PhoneNumberFormat.E164)
        # Validate the formatted phone number using the Pydantic model
        phone_data = PhoneValidationModel(phone=formatted_number)
        return phone_data.phone
    except phonenumbers.phonenumberutil.NumberParseException as e:
        raise ValueError(f"Phone number parsing error: {e}")
    except ValidationError as e:
        raise ValidationError(f"Phone number validation error: {e}")


# Helper function to format Twilio messages for RabbitMQ
def twilio_POST_to_queue_message(values: dict) -> str:
    iso_timestamp = datetime.now().isoformat()
    try:
        # Validate and format the phone number
        formatted_phone = validate_and_format_phone_number(
            phone_number=values['From'])
        queue_message = {
            'id': values['MessageSid'],
            'timestamp': iso_timestamp,
            'platform': 'WHATSAPP',
            'from': {
                'phone': formatted_phone,
            },
            'text': values['Body'],
            'media': []
        }
        # Add media files if present
        num_media = values.get('NumMedia', 0)
        for i in range(num_media):
            media_url = values.get(f'MediaUrl{i}', '')
            if media_url:
                queue_message['media'].append(media_url)
        return json.dumps(queue_message)
    except ValueError as e:
        logger.error(f"Error formatting message: {e}")
        raise


@app.before_serving
async def before_server_start():
    await rabbitmq_client.initialize()
    asyncio.create_task(rabbitmq_client.consume(
        queue_name=RABBITMQ_QUEUE_TWILIOBOT_REPLIES,
        routing_key=f"*.{RABBITMQ_QUEUE_TWILIOBOT_REPLIES}",
        callback=twiliobot_client.send_whatsapp_message
    ))


@app.after_serving
async def after_server_stop():
    if rabbitmq_client:
        await rabbitmq_client.disconnect()


@app.post("/whatsapp")
async def receive_whatsapp_message():
    try:
        values = await request.form
        logger.info(f"Received Whatsapp message: {values}")
        # Validate the incoming data using the Pydantic model
        data = IncomingMessage(
            MessageSid=values.get('MessageSid'),
            From=values.get('From'),
            Body=values.get('Body'),
            NumMedia=int(values.get('NumMedia', 0))
        )
        body = twilio_POST_to_queue_message(data.model_dump())

        # Ensure RabbitMQ is initialized before sending message
        await rabbitmq_client.initialize()
        # Send message to RabbitMQ
        asyncio.create_task(rabbitmq_client.producer(
            body=body,
            routing_key=RABBITMQ_QUEUE_USER_CHATS,
            reply_to=RABBITMQ_QUEUE_TWILIOBOT_REPLIES
        ))
        logger.info(f"Message sent to RabbitMQ: {body}")
        return await make_response('', 204)

    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return await make_response({"error": f"Validation error: {e}"}, 400)

    except ValueError as e:
        logger.error(f"Invalid phone number or message format: {e}")
        return await make_response(
            {"error": f"Invalid phone number or message format: {e}"}, 400)

    except Exception as e:
        logger.error(f"Error receiving Whatsapp message: {values}: {e}")
        return await make_response({"error": f"Internal error: {str(e)}"}, 500)


if __name__ == "__main__":
    app.run()
