import os
import json
import logging
import time
import phonenumbers

from datetime import datetime, timezone
from json.decoder import JSONDecodeError
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client
from pydantic import BaseModel, ValidationError
from pydantic_extra_types.phone_numbers import PhoneNumber
from Akvo_rabbitmq_client import queue_message_util
from models.chat import Chat_Sender, PlatformEnum


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_WHATSAPP_MESSAGE_LENGTH = 1500


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
        self.TWILIO_WHATSAPP_FROM = f"whatsapp:{self.TWILIO_WHATSAPP_NUMBER}"

        self.twilio_client = Client(
            self.TWILIO_ACCOUNT_SID, self.TWILIO_AUTH_TOKEN
        )

    def chunk_text_by_paragraphs(self, text: str, max_length: int) -> list[str]:
        paragraphs = text.split("\n\n")
        chunks = []
        for paragraph in paragraphs:
            if len(paragraph) <= max_length:
                chunks.append(paragraph)
            else:
                for start_index in range(0, len(paragraph), max_length):
                    end_index = start_index + max_length
                    chunk = paragraph[start_index:end_index]
                    chunks.append(chunk)
        return chunks

    def send_whatsapp_message(self, body: str) -> None:
        try:
            queue_message = json.loads(body)
            text = queue_message.get("body")
            conversation_envelope = queue_message.get(
                "conversation_envelope", {}
            )
            phone = conversation_envelope.get(
                "client_phone_number",
                conversation_envelope.get("user_phone_number"),
            )
            chunks = self.chunk_text_by_paragraphs(
                text, MAX_WHATSAPP_MESSAGE_LENGTH
            )
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
                time.sleep(0.5)
            logger.info(f"Message sent to WhatsApp: {text}")

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
            formatted_number = phonenumbers.format_number(
                parsed_number, phonenumbers.PhoneNumberFormat.E164
            )
            PhoneValidationModel(phone=formatted_number)
            return formatted_number
        except phonenumbers.phonenumberutil.NumberParseException as e:
            raise ValueError(f"Phone number parsing error: {e}")
        except ValidationError as e:
            raise ValidationError(f"Phone number validation error: {e}")

    def format_to_queue_message(self, values: dict) -> str:
        try:
            iso_timestamp = datetime.now(timezone.utc).isoformat()
            # Validate and format the phone number
            phone_number = values.get("From").split(":")[1]
            formatted_phone = self.validate_and_format_phone_number(
                phone_number=phone_number
            )
            # Add media files if present
            media = []
            num_media = values.get("NumMedia", 0)
            for i in range(num_media):
                media_url = values.get(f"MediaUrl{i}", "")
                if media_url:
                    media.append(media_url)
            queue_message = queue_message_util.create_queue_message(
                message_id=values["MessageSid"],
                conversation_id="__CHANGEME__",
                client_phone_number=formatted_phone,
                sender_role=Chat_Sender.CLIENT,
                sender_role_enum=Chat_Sender,
                platform=PlatformEnum.WHATSAPP,
                platform_enum=PlatformEnum,
                body=values["Body"],
                media=media,
                timestamp=iso_timestamp,
            )
            return json.dumps(queue_message)
        except ValueError as e:
            logger.error(f"Error formatting message: {e}")
            raise ValueError(f"Error formatting message: {e}")
