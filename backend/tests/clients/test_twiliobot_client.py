import json
import pytest
from unittest.mock import patch, MagicMock
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client
from clients.twilio_client import TwilioClient


@pytest.fixture
def twilio_client():
    return TwilioClient()


def test_chunk_text_by_paragraphs(twilio_client):
    text = "This is a test paragraph.\n\nThis is another test paragraph that is"
    text += " longer than the previous one to check chunking functionality."
    max_length = 50
    chunks = twilio_client.chunk_text_by_paragraphs(text, max_length)
    assert len(chunks) == 3
    assert chunks[0] == "This is a test paragraph."
    assert chunks[1] == "This is another test paragraph that is longer than"
    assert chunks[2] == " the previous one to check chunking functionality."


def test_validate_and_format_phone_number_valid(twilio_client):
    phone_number = "+6281234567890"
    formatted_phone = twilio_client.validate_and_format_phone_number(
        phone_number)
    assert formatted_phone == "+6281234567890"


def test_validate_and_format_phone_number_invalid(twilio_client):
    phone_number = "1234567890"  # Invalid format
    with pytest.raises(ValueError):
        twilio_client.validate_and_format_phone_number(phone_number)


def test_validate_and_format_phone_number_parse_error(twilio_client):
    phone_number = "invalid_number"  # Invalid number format
    with pytest.raises(ValueError):
        twilio_client.validate_and_format_phone_number(phone_number)


def test_format_to_queue_message_valid(twilio_client):
    values = {
        'MessageSid': '1234567890',
        'From': 'whatsapp:+6281234567890',
        'Body': 'Test message',
        'NumMedia': 1,
        'MediaUrl0': 'http://example.com/image.jpg'
    }
    formatted_message = twilio_client.format_to_queue_message(values)
    assert isinstance(formatted_message, str)
    queue_message = json.loads(formatted_message)
    assert queue_message['id'] == '1234567890'
    assert queue_message['from']['phone'] == '+6281234567890'
    assert queue_message['text'] == 'Test message'
    assert queue_message['media'] == ['http://example.com/image.jpg']
    assert 'timestamp' in queue_message
    assert 'platform' in queue_message


def test_format_to_queue_message_missing_fields(twilio_client):
    values = {
        'From': 'whatsapp:+6281234567890',
        'Body': 'Test message',
    }
    with pytest.raises(KeyError):
        twilio_client.format_to_queue_message(values)


def test_format_to_queue_message_invalid_phone_number(twilio_client):
    values = {
        'MessageSid': '1234567890',
        'From': 'whatsapp:invalid_number',  # Invalid phone number format
        'Body': 'Test message',
        'NumMedia': 0,
    }
    with pytest.raises(ValueError, match="Phone number parsing error: "):
        twilio_client.format_to_queue_message(values)


@patch.object(Client, 'messages', new_callable=MagicMock)
@patch('clients.twilio_client.logger')
def test_send_whatsapp_message_success(
    mock_logger,
    mock_messages,
    twilio_client
):
    message_body = json.dumps({
        "text": "Hello, this is a test message.",
        "to": {"phone": "+1234567890"}
    }).encode()

    mock_messages.create.return_value = MagicMock(error_code=None)

    twilio_client.send_whatsapp_message(message_body)

    assert mock_messages.create.called
    mock_messages.create.assert_called_with(
        from_=twilio_client.TWILIO_WHATSAPP_FROM,
        body="Hello, this is a test message.",
        to="whatsapp:+1234567890",
    )


@patch.object(Client, 'messages', new_callable=MagicMock)
@patch('clients.twilio_client.logger')
def test_send_whatsapp_message_twilio_error(
    mock_logger,
    mock_messages,
    twilio_client
):
    message_body = json.dumps({
        "text": "Hello, this is a test message.",
        "to": {"phone": "+1234567890"}
    }).encode()

    mock_messages.create.side_effect = TwilioRestException(
        status=400, uri='http://test.uri', msg="Twilio error")

    twilio_client.send_whatsapp_message(message_body)

    assert mock_messages.create.called
    mock_messages.create.assert_called_with(
        from_=twilio_client.TWILIO_WHATSAPP_FROM,
        body="Hello, this is a test message.",
        to="whatsapp:+1234567890",
    )

    # Check that the error was logged
    mock_logger.error.assert_any_call(
        "Error sending message to Twilio: HTTP 400 error: Twilio error")


@patch.object(Client, 'messages', new_callable=MagicMock)
@patch('clients.twilio_client.logger')
def test_send_whatsapp_message_json_decode_error(
    mock_logger,
    mock_messages,
    twilio_client
):
    message_body = b"invalid json"

    twilio_client.send_whatsapp_message(message_body)

    assert not mock_messages.create.called

    # Check that the error was logged
    mock_logger.error.assert_any_call(
        "Error decoding JSON message: Expecting value: line 1 column 1 (char 0)"
    )


@patch.object(Client, 'messages', new_callable=MagicMock)
@patch('clients.twilio_client.logger')
def test_send_whatsapp_message_unexpected_error(
    mock_logger,
    mock_messages,
    twilio_client
):
    message_body = json.dumps({
        "text": "Hello, this is a test message.",
        "to": {"phone": "+1234567890"}
    }).encode()

    mock_messages.create.side_effect = Exception("Unexpected error")

    twilio_client.send_whatsapp_message(message_body)

    assert mock_messages.create.called
    mock_messages.create.assert_called_with(
        from_=twilio_client.TWILIO_WHATSAPP_FROM,
        body="Hello, this is a test message.",
        to="whatsapp:+1234567890",
    )

    # Check that the error was logged
    mock_logger.error.assert_any_call("Unexpected error: Unexpected error")
