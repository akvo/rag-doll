import os
import json
import logging
import time
import phonenumbers
import requests
import urllib.request
import speech_recognition as sr

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
    Chat_Session,
    Chat,
    User,
    Client as ClientModel,
)
from typing import Optional
from pydub import AudioSegment
from base64 import b64encode
from sqlmodel import Session, select
from core.database import engine
from utils.util import get_value_or_raise_error


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_WHATSAPP_MESSAGE_LENGTH = 1500
STORAGE = "./storage"


def save_chat_history(
    session: Session, conversation_envelope: dict, message_body=str
):
    try:
        user_phone_number = get_value_or_raise_error(
            conversation_envelope, "user_phone_number"
        )
        client_phone_number = get_value_or_raise_error(
            conversation_envelope, "client_phone_number"
        )

        conversation_exist = session.exec(
            select(Chat_Session)
            .join(User)
            .join(ClientModel)
            .where(
                User.phone_number == user_phone_number,
                ClientModel.phone_number == client_phone_number,
            )
        ).first()

        if not conversation_exist:
            return None

        sender_role = get_value_or_raise_error(
            conversation_envelope, "sender_role"
        )
        new_chat = Chat(
            chat_session_id=conversation_exist.id,
            message=message_body,
            sender_role=(Sender_Role_Enum[sender_role.upper()]),
        )
        session.add(new_chat)
        session.commit()
        session.flush()
        return new_chat.id
    except Exception as e:
        logger.error(f"Save chat history failed: {e}")
        raise e
    finally:
        session.close()


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
            session = Session(engine)

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
            if not os.getenv("TESTING"):
                # save sent message history here
                save_chat_history(
                    session=session,
                    conversation_envelope=conversation_envelope,
                    message_body=text,
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
            message_body = values["Body"]
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
                    audio_file_path = self.ogg2mp3(
                        audio_url=media_url, message_sid=values["MessageSid"]
                    )
                    logger.info(f"Audio converted {audio_file_path}")
                    transcription = self.transcribe_audio(
                        wav_path=audio_file_path
                    )
                    message_body = transcription if transcription else ""

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

            converted_filepath = f"{filepath}/{message_sid}.wav"
            audio_file.export(converted_filepath, format="wav")
            os.remove(audio_filepath)

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
