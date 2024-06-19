import json
import pytest
import logging
from unittest.mock import patch, MagicMock
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client
from twiliobot_client import TwiliobotClient


@pytest.fixture
def twilio_client():
    return TwiliobotClient()


def test_chunk_text_by_paragraphs(twilio_client):
    text = "This is a test paragraph.\n\nThis is another test paragraph that is"
    text += " longer than the previous one to check chunking functionality."
    max_length = 50
    chunks = twilio_client.chunk_text_by_paragraphs(text, max_length)
    assert len(chunks) == 3
    assert chunks[0] == "This is a test paragraph."
    assert chunks[1] == "This is another test paragraph that is longer than"
    assert chunks[2] == " the previous one to check chunking functionality."


@patch.object(Client, 'messages', new_callable=MagicMock)
def test_send_whatsapp_message_success(mock_messages, twilio_client):
    message_body = json.dumps({
        "text": "Hello, this is a test message.",
        "to": {"phone": "+1234567890"}
    }).encode()

    mock_messages.create.return_value = MagicMock(error_code=None)

    twilio_client.send_whatsapp_message(message_body)

    assert mock_messages.create.called
    mock_messages.create.assert_called_with(
        from_="whatsapp:+14155238886",
        body="Hello, this is a test message.",
        to="whatsapp:+1234567890",
    )


@patch.object(Client, 'messages', new_callable=MagicMock)
def test_send_whatsapp_message_twilio_error(
    mock_messages,
    twilio_client,
    caplog
):
    message_body = json.dumps({
        "text": "Hello, this is a test message.",
        "to": {"phone": "+1234567890"}
    }).encode()

    mock_messages.create.side_effect = TwilioRestException(
        status=400, uri='http://test.uri', msg="Twilio error")

    with caplog.at_level(logging.ERROR):
        twilio_client.send_whatsapp_message(message_body)
        assert any(
            "Error sending message to Twilio: HTTP 400 error: Twilio error"
            in record.message for record in caplog.records)


@patch.object(Client, 'messages', new_callable=MagicMock)
def test_send_whatsapp_message_json_decode_error(
    mock_messages,
    twilio_client,
    caplog
):
    message_body = b"invalid json"

    with caplog.at_level(logging.ERROR):
        twilio_client.send_whatsapp_message(message_body)
        assert any(
            "Error decoding JSON message"
            in record.message for record in caplog.records)


@patch.object(Client, 'messages', new_callable=MagicMock)
def test_send_whatsapp_message_unexpected_error(
    mock_messages,
    twilio_client,
    caplog
):
    message_body = json.dumps({
        "text": "Hello, this is a test message.",
        "to": {"phone": "+1234567890"}
    }).encode()

    mock_messages.create.side_effect = Exception("Unexpected error")

    with caplog.at_level(logging.ERROR):
        twilio_client.send_whatsapp_message(message_body)
        assert any(
            "Unexpected error: Unexpected error"
            in record.message for record in caplog.records)
