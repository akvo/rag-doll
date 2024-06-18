import os
import json
import logging
import time
from json.decoder import JSONDecodeError
from twilio.base.exceptions import TwilioRestException

from twilio.rest import Client


class TwiliobotClient:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        self.TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
        self.TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
        self.TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"

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

    def send_whatsapp_message(self, message_body: bytes) -> None:
        """
        Consume messages from the RabbitMQ queue and send them via Twilio.
        """
        try:
            self.logger.info(f"Message received: {message_body}")
            queue_message = json.loads(message_body.decode("utf8"))
            text = queue_message["text"]
            phone = queue_message["to"]["phone"]

            chunks = self.chunk_text_by_paragraphs(text, 1500)
            self.logger.info(f"sending '{text}' to WhatsApp number {phone}")
            for chunk in chunks:
                self.logger.info(f"sending '{chunk}' to WhatsApp")
                self.logger.info(f"number {phone}")
                response = self.twilio_client.messages.create(
                    from_=self.TWILIO_WHATSAPP_FROM,
                    body=chunk,
                    to=f"whatsapp:{phone}",
                )
                if response.error_code is not None:
                    self.logger.error(
                        f"Failed to send message to WhatsApp number "
                        f"{phone}: {response.error_message}"
                    )
                time.sleep(0.5)  # 500ms delay

        except JSONDecodeError as e:
            self.logger.error(f"Error decoding JSON message: {e}")
        except TwilioRestException as e:
            self.logger.error(f"Error sending message to Twilio: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")


twiliobot_client = TwiliobotClient()
