import os
import json
import logging
import time
import phonenumbers

from datetime import datetime
from json.decoder import JSONDecodeError
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client
from pydantic import BaseModel, ValidationError
from pydantic_extra_types.phone_numbers import PhoneNumber


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IncomingMessage(BaseModel):
    MessageSid: str
    From: str
    Body: str
    NumMedia: int


class PhoneValidationModel(BaseModel):
    phone: PhoneNumber


class TwilioClient:
    def __init__(self):
        self.TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
        self.TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
        self.TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
        if os.getenv("TESTING"):
            # only for testing purpose
            self.TWILIO_WHATSAPP_NUMBER = "+12345678911"
        self.TWILIO_WHATSAPP_FROM = f"whatsapp:{self.TWILIO_WHATSAPP_NUMBER}"

        self.twilio_client = Client(
            self.TWILIO_ACCOUNT_SID,
            self.TWILIO_AUTH_TOKEN)

    def chunk_text_by_paragraphs(self, text: str, max_length: int) -> list[str]:
        """
        Split text into chunks by paragraphs,
        ensuring each chunk is within the max_length.
        """
        paragraphs = text.split("\n\n")
        chunks = []
        for paragraph in paragraphs:
            if len(paragraph) <= max_length:
                chunks.append(paragraph)
            else:
                for i in range(0, len(paragraph), max_length):
                    chunk = paragraph[i:i + max_length]
                    chunks.append(chunk)
        return chunks

    def send_whatsapp_message(self, body: str, headers: dict) -> None:
        """
        Consume messages from the RabbitMQ queue and send them via Twilio.
        """
        try:
            queue_message = json.loads(body)
            text = queue_message["text"]
            phone = queue_message["to"]["phone"]

            chunks = self.chunk_text_by_paragraphs(text, 1500)
            logger.info(f"sending '{text}' to WhatsApp number {phone}")
            for chunk in chunks:
                response = self.twilio_client.messages.create(
                    from_=self.TWILIO_WHATSAPP_FROM,
                    body=chunk,
                    to=f"whatsapp:{phone}",
                )
                if response.error_code is not None:
                    logger.error(
                        f"Failed to send message to WhatsApp number "
                        f"{phone}: {response.error_message}"
                    )
                time.sleep(0.5)  # 500ms delay

        except JSONDecodeError as e:
            logger.error(f"Error decoding JSON message: {e}")
        except TwilioRestException as e:
            logger.error(f"Error sending message to Twilio: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

    def validate_and_format_phone_number(self, phone_number: str) -> str:
        try:
            parsed_number = phonenumbers.parse(phone_number)
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValueError(f"Invalid phone number: {phone_number}")
            # Format the phone number
            formatted_number = phonenumbers.format_number(
                parsed_number, phonenumbers.PhoneNumberFormat.E164)
            # Validate the formatted phone number using the Pydantic model
            PhoneValidationModel(phone=formatted_number)
            return formatted_number
        except phonenumbers.phonenumberutil.NumberParseException as e:
            raise ValueError(f"Phone number parsing error: {e}")
        except ValidationError as e:
            raise ValidationError(f"Phone number validation error: {e}")

    def format_to_queue_message(self, values: dict) -> str:
        """
        Consume messages from Twilio then format into queue message.
        """
        iso_timestamp = datetime.now().isoformat()
        try:
            # Validate and format the phone number
            phone_number = values.get('From').split(':')[1]
            formatted_phone = self.validate_and_format_phone_number(
                phone_number=phone_number)
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
            raise ValueError(f"Error formatting message: {e}")
