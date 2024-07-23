import os
import json
import logging
import time
import phonenumbers
import requests
import urllib.request

from datetime import datetime, timezone
from json.decoder import JSONDecodeError
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client
from pydantic import BaseModel, ValidationError
from pydantic_extra_types.phone_numbers import PhoneNumber
from Akvo_rabbitmq_client import queue_message_util
from models.chat import Sender_Role_Enum, Platform_Enum
from typing import Optional
from pydub import AudioSegment
from base64 import b64encode


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_WHATSAPP_MESSAGE_LENGTH = 1500
STORAGE = "./storage"


class IncomingMessage(BaseModel):
    MessageSid: str
    From: str
    Body: str
    NumMedia: Optional[int]


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

    def chunk_text_by_paragraphs(
        self, text: str, max_length: int
    ) -> list[str]:
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
                "client_phone_number"
            ) or conversation_envelope.get("user_phone_number")
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
        logger.info(f"[ABC] {values}")
        try:
            iso_timestamp = datetime.now(timezone.utc).isoformat()
            # Validate and format the phone number
            phone_number = values.get("From").split(":")[1]
            formatted_phone = self.validate_and_format_phone_number(
                phone_number=phone_number
            )
            # Add media files if present
            media = []
            context = []
            num_media = values.get("NumMedia", 0)
            for i in range(num_media):
                media_url = values.get(f"MediaUrl{i}", "")
                media_type = values.get(f"MediaContentType{i}")
                if media_url:
                    media.append(media_url)
                    context.append({"file": media_url, "type": media_type})
                if media_url and media_type == "audio/ogg":
                    mp3_file_path = self.ogg2mp3(
                        audio_url=media_url, message_sid=values["MessageSid"]
                    )
                    logger.info(f"Audio converted {mp3_file_path}")

            queue_message = queue_message_util.create_queue_message(
                message_id=values["MessageSid"],
                client_phone_number=formatted_phone,
                sender_role=Sender_Role_Enum.CLIENT,
                sender_role_enum=Sender_Role_Enum,
                platform=Platform_Enum.WHATSAPP,
                platform_enum=Platform_Enum,
                body=values["Body"],
                media=media,
                context=context,
                timestamp=iso_timestamp,
            )
            return json.dumps(queue_message)
        except ValueError as e:
            logger.error(f"Error formatting message: {e}")
            raise ValueError(f"Error formatting message: {e}")

    def ogg2mp3(self, audio_url: str, message_sid: str):
        try:
            filepath = f"{STORAGE}/audio"
            # create authentication token
            auth_str = f"{self.TWILIO_ACCOUNT_SID}:{self.TWILIO_AUTH_TOKEN}"
            auth_bytes = auth_str.encode("utf-8")
            auth_b64 = b64encode(auth_bytes).decode("utf-8")
            headers = {"Authorization": "Basic " + auth_b64}

            # download and convert the audio file
            response = requests.get(url=audio_url, headers=headers)
            url = response.url
            if not os.path.exists(filepath):
                os.makedirs(filepath)

            audio_filepath = f"{filepath}/{message_sid}.ogg"
            urllib.request.urlretrieve(url, audio_filepath)
            audio_file = AudioSegment.from_ogg(audio_filepath)

            mp3_filepath = f"{filepath}/{message_sid}.mp3"
            audio_file.export(mp3_filepath, format="mp3")

            return os.path.join(os.getcwd(), mp3_filepath)
        except Exception as e:
            logger.error(f"Error downloading audio file: {e}")
