import os
import json
import logging
import phonenumbers
import requests
import urllib.request
import speech_recognition as sr

from uuid import uuid4
from datetime import datetime, timezone
from json.decoder import JSONDecodeError
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client
from pydantic import BaseModel, ValidationError
from pydantic_extra_types.phone_numbers import PhoneNumber
from Akvo_rabbitmq_client import queue_message_util
from models import (
    Sender_Role_Enum,
    Platform_Enum,
)
from typing import Optional
from pydub import AudioSegment
from base64 import b64encode
from utils.util import TextConverter
from utils.storage import upload


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_WHATSAPP_MESSAGE_LENGTH = 1500
STORAGE = "./storage"
ALLOWED_MESSAGE_TYPES = ["text", "image"]


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

    def download_media(self, url: str, folder: str, filename: str):
        # create authentication token
        auth_str = f"{self.TWILIO_ACCOUNT_SID}:{self.TWILIO_AUTH_TOKEN}"
        auth_bytes = auth_str.encode("utf-8")
        auth_b64 = b64encode(auth_bytes).decode("utf-8")
        headers = {"Authorization": "Basic " + auth_b64}

        # download and convert the audio file
        response = requests.get(url=url, headers=headers)
        filepath = f"{STORAGE}/{folder}"
        if not os.path.exists(filepath):
            os.makedirs(filepath)

        filepath = f"{filepath}/{filename}"
        urllib.request.urlretrieve(response.url, filepath)
        return filepath

    async def whatsapp_message_create(self, to: str, body: str):
        try:
            response = self.twilio_client.messages.create(
                from_=self.TWILIO_WHATSAPP_FROM,
                body=TextConverter(body).format_whatsapp(),
                to=f"whatsapp:{to}",
            )
            if response.error_code is not None:
                logger.error(
                    f"Failed to send message to WhatsApp number "
                    f"{to}: {response.error_message}"
                )
            logger.info(f"Message sent to WhatsApp: {body}")
        except TwilioRestException as e:
            logger.error(f"Error sending message to Twilio: {e}")

    async def whatsapp_message_template_create(
        self, to: str, content_variables: dict, content_sid: str
    ):
        try:
            response = self.twilio_client.messages.create(
                content_sid=content_sid,
                to=f"whatsapp:{to}",
                from_=self.TWILIO_WHATSAPP_FROM,
                content_variables=json.dumps(content_variables),
            )
            if response.error_code is not None:
                logger.error(
                    f"Failed to send message to WhatsApp number "
                    f"{to}: {response.error_message}"
                )
            logger.info(
                f"Template message sent to WhatsApp: {content_variables}"
            )
        except TwilioRestException as e:
            logger.error(f"Error sending template message to Twilio: {e}")

    async def send_whatsapp_message(self, body: str) -> None:
        # TODO :: handle send message template here
        try:
            queue_message = json.loads(body)
            text = queue_message.get("body")
            conversation_envelope = queue_message.get(
                "conversation_envelope", {}
            )
            phone = conversation_envelope.get(
                "client_phone_number"
            ) or conversation_envelope.get("user_phone_number")
            await self.whatsapp_message_create(to=phone, body=text)
            logger.info(f"Message sent to WhatsApp: {text}")
        except JSONDecodeError as e:
            logger.error(f"Error decoding JSON message: {e}")
        except TwilioRestException as e:
            # TODO:: If message sent fail,
            # how we want to handle resend message to twilio?
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
            message_body = values["Body"]
            # Add media files if present
            media = []
            context = []
            num_media = values.get("NumMedia", 0)
            for i in range(num_media):
                media_url = values.get(f"MediaUrl{i}", "")
                media_type = values.get(f"MediaContentType{i}")

                # AUDIO
                if media_url and media_type == "audio/ogg":
                    audio_filepath = self.ogg2mp3(
                        audio_url=media_url, message_sid=values["MessageSid"]
                    )
                    logger.info(f"Audio converted {audio_filepath}")
                    transcription = self.transcribe_audio(
                        wav_path=audio_filepath
                    )
                    message_body = transcription if transcription else ""

                # IMAGE
                if media_url and "image" in media_type:
                    uid = uuid4()
                    filetype = media_type.split("/")[1]
                    filename = f"{values["MessageSid"]}-{str(uid)}.{filetype}"
                    filepath = self.download_media(
                        url=media_url, folder="media", filename=filename
                    )
                    bucket_url = upload(
                        file=filepath,
                        folder="media",
                        filename=filename,
                        public=True,
                    )
                    media.append({"url": bucket_url, "type": media_type})
                    context.append(
                        {
                            "url": bucket_url,
                            "type": media_type,
                            "caption": message_body,
                        }
                    )
                    logger.info(f"Image upload: {bucket_url}")

            queue_message = queue_message_util.create_queue_message(
                message_id=values["MessageSid"],
                client_phone_number=formatted_phone,
                sender_role=Sender_Role_Enum.CLIENT,
                sender_role_enum=Sender_Role_Enum,
                platform=Platform_Enum.WHATSAPP,
                platform_enum=Platform_Enum,
                body=message_body,
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
            filepath = self.download_media(
                url=audio_url, folder="media", filename=f"{message_sid}.ogg"
            )
            audio_file = AudioSegment.from_ogg(filepath)
            converted_filepath = f"{filepath}/{message_sid}.wav"
            audio_file.export(converted_filepath, format="wav")
            os.remove(filepath)
            return os.path.join(os.getcwd(), converted_filepath)
        except Exception as e:
            logger.error(f"Error downloading audio file: {e}")
            return None

    def transcribe_audio(self, wav_path: str):
        try:
            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            logger.info("Audio transcription: " + text)
            return text
        except sr.UnknownValueError:
            logger.error(
                "Google Speech Recognition could not understand audio"
            )
            return None
        except sr.RequestError as e:
            logger.error(
                "Could not request results from Google Speech Recognition "
                f"service; {e}"
            )
            return None
        except Exception as e:
            logger.error(f"Exception error: {e}")
            return None
