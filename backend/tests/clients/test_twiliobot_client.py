import json
import pytest
from unittest.mock import patch, MagicMock
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client
from clients.twilio_client import TwilioClient


@pytest.fixture
def twilio_client():
    return TwilioClient()


def test_validate_and_format_phone_number_valid(twilio_client):
    phone_number = "+6281234567890"
    formatted_phone = twilio_client.validate_and_format_phone_number(
        phone_number
    )
    assert formatted_phone == "+6281234567890"


def test_validate_and_format_phone_number_invalid(twilio_client):
    phone_number = "1234567890"
    with pytest.raises(ValueError):
        twilio_client.validate_and_format_phone_number(phone_number)


def test_validate_and_format_phone_number_parse_error(twilio_client):
    phone_number = "invalid_number"
    with pytest.raises(ValueError):
        twilio_client.validate_and_format_phone_number(phone_number)


def test_format_to_queue_message_valid(twilio_client):
    values = {
        "MessageSid": "1234567890",
        "From": "whatsapp:+6281234567890",
        "Body": "Test message",
        "NumMedia": 0,
    }
    formatted_message = twilio_client.format_to_queue_message(values)
    queue_message = json.loads(formatted_message)
    conversation_envelope = queue_message.get("conversation_envelope", {})
    timestamp = conversation_envelope.get("timestamp")
    assert queue_message == {
        "conversation_envelope": {
            "message_id": "1234567890",
            "client_phone_number": "+6281234567890",
            "user_phone_number": None,
            "sender_role": "client",
            "platform": "WHATSAPP",
            "timestamp": timestamp,
        },
        "body": "Test message",
        "media": [],
        "context": [],
        "transformation_log": ["Test message"],
    }


def test_format_to_queue_message_valid_with_voice_notes(twilio_client):
    audio_file_link = "https://getsamplefiles.com/download/ogg/sample-3.ogg"
    values = {
        "MessageSid": "1234567890",
        "From": "whatsapp:+6281234567890",
        "Body": "Test message",
        "NumMedia": 1,
        "MediaUrl0": audio_file_link,
        "MediaContentType0": "audio/ogg",
    }
    formatted_message = twilio_client.format_to_queue_message(values)
    queue_message = json.loads(formatted_message)
    conversation_envelope = queue_message.get("conversation_envelope", {})
    timestamp = conversation_envelope.get("timestamp")
    assert queue_message == {
        "conversation_envelope": {
            "message_id": "1234567890",
            "client_phone_number": "+6281234567890",
            "user_phone_number": None,
            "sender_role": "client",
            "platform": "WHATSAPP",
            "timestamp": timestamp,
        },
        "body": "",
        "media": [],
        "context": [],
        "transformation_log": [""],
    }


def test_format_to_queue_message_missing_fields(twilio_client):
    values = {
        "From": "whatsapp:+6281234567890",
        "Body": "Test message",
    }
    with pytest.raises(KeyError):
        twilio_client.format_to_queue_message(values)


def test_format_to_queue_message_invalid_phone_number(twilio_client):
    values = {
        "MessageSid": "1234567890",
        "From": "whatsapp:invalid_number",
        "Body": "Test message",
        "NumMedia": 0,
    }
    with pytest.raises(ValueError, match="Phone number parsing error: "):
        twilio_client.format_to_queue_message(values)


@pytest.mark.asyncio
@patch.object(Client, "messages", new_callable=MagicMock)
@patch("clients.twilio_client.logger")
async def test_send_whatsapp_message_success(
    mock_logger, mock_messages, twilio_client
):
    message_body = json.dumps(
        {
            "conversation_envelope": {
                "message_id": "message_id",
                "client_phone_number": "+1234567899",
                "user_phone_number": "+1234567890",
                "sender_role": "system",
                "platform": "WHATSAPP",
            },
            "body": "Hello, this is a test message.",
            "media": [],
            "context": [],
            "transformation_log": ["Hello, this is a test message."],
        }
    ).encode()

    mock_messages.create.return_value = MagicMock(error_code=None)

    await twilio_client.send_whatsapp_message(message_body)

    mock_messages.create.assert_called_with(
        from_=twilio_client.TWILIO_WHATSAPP_FROM,
        body="Hello, this is a test message.",
        to="whatsapp:+1234567899",
    )


@pytest.mark.asyncio
@patch.object(Client, "messages", new_callable=MagicMock)
@patch("clients.twilio_client.logger")
async def test_send_whatsapp_message_twilio_error(
    mock_logger, mock_messages, twilio_client
):
    message_body = json.dumps(
        {
            "conversation_envelope": {
                "message_id": "message_id",
                "client_phone_number": "+1234567899",
                "user_phone_number": "+1234567890",
                "sender_role": "system",
                "platform": "WHATSAPP",
            },
            "body": "Hello, this is a test message.",
            "media": [],
            "context": [],
            "transformation_log": ["Hello, this is a test message."],
        }
    ).encode()

    mock_messages.create.side_effect = TwilioRestException(
        status=400, uri="http://test.uri", msg="Twilio error"
    )

    await twilio_client.send_whatsapp_message(message_body)

    mock_messages.create.assert_called_with(
        from_=twilio_client.TWILIO_WHATSAPP_FROM,
        body="Hello, this is a test message.",
        to="whatsapp:+1234567899",
    )

    mock_logger.error.assert_any_call(
        "Error sending message to Twilio: HTTP 400 error: Twilio error"
    )


@pytest.mark.asyncio
@patch.object(Client, "messages", new_callable=MagicMock)
@patch("clients.twilio_client.logger")
async def test_send_whatsapp_message_json_decode_error(
    mock_logger, mock_messages, twilio_client
):
    message_body = b"invalid json"

    await twilio_client.send_whatsapp_message(message_body)

    assert not mock_messages.create.called

    mock_logger.error.assert_any_call(
        "Error decoding JSON message: Expecting value: line 1 column 1 (char 0)"
    )


@pytest.mark.asyncio
@patch.object(Client, "messages", new_callable=MagicMock)
@patch("clients.twilio_client.logger")
async def test_send_whatsapp_message_unexpected_error(
    mock_logger, mock_messages, twilio_client
):
    message_body = json.dumps(
        {
            "conversation_envelope": {
                "message_id": "message_id",
                "client_phone_number": "+1234567899",
                "user_phone_number": "+1234567890",
                "sender_role": "system",
                "platform": "WHATSAPP",
            },
            "body": "Hello, this is a test message.",
            "media": [],
            "context": [],
            "transformation_log": ["Hello, this is a test message."],
        }
    ).encode()

    mock_messages.create.side_effect = Exception("Unexpected error")

    await twilio_client.send_whatsapp_message(message_body)

    mock_messages.create.assert_called_with(
        from_=twilio_client.TWILIO_WHATSAPP_FROM,
        body="Hello, this is a test message.",
        to="whatsapp:+1234567899",
    )

    mock_logger.error.assert_any_call("Unexpected error: Unexpected error")
