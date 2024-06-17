import os
import json
import logging

from twilio.rest import Client


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_FROM = 'whatsapp:+14155238886'  # Consider externalizing

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def chunk_text_by_paragraphs(text, max_length):
    """
    Split text into chunks by paragraphs,
    ensuring each chunk is within the max_length.
    """
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        # +2 for the \n\n
        if len(current_chunk) + len(paragraph) + 2 <= max_length:
            if current_chunk:
                current_chunk += "\n\n"
            current_chunk += paragraph
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = paragraph

    if current_chunk:
        chunks.append(current_chunk)
    return chunks


def twilio_send_runner(ch, method, properties, body) -> None:
    """
    Consume messages from the RabbitMQ queue and send them via Twilio.
    """
    try:
        logger.info(f"Message received: {body}")
        queue_message = json.loads(body.decode('utf8'))
        text = queue_message['text']
        phone = queue_message['to']['phone']
        if '+' not in str(phone):
            phone = f"+{phone}"

        # Chunk the text by paragraphs
        chunks = chunk_text_by_paragraphs(text, 1500)
        logger.info(f"sending '{text}' to WhatsApp number {phone}")
        for chunk in chunks:
            logger.info(f"sending '{chunk}' to WhatsApp number {phone}")
            response = twilio_client.messages.create(
                from_=TWILIO_WHATSAPP_FROM,
                body=chunk,
                to=f"whatsapp:{phone}"
            )
            if response.error_code is not None:
                logger.error(
                    f"Failed to send message to WhatsApp number {phone}: {
                        response.error_message}")

    except Exception as e:
        logger.error(f"Error while sending message to Twilio: {e}")
