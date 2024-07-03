import os
import pytest

from quart.testing import QuartClient

from main import app as quart_app


# Mocked rabbitmq_client and twiliobot_client for testing
class MockRabbitMQClient:
    async def initialize(self):
        pass

    async def disconnect(self):
        pass

    async def consume(self, queue_name, routing_key, callback):
        pass

    async def producer(self, body, routing_key, reply_to):
        pass


class MockTwilioBotClient:
    async def send_whatsapp_message(self, message):
        pass


@pytest.fixture
def app():
    os.environ["TESTING"] = "1"
    quart_app.config["TESTING"] = True
    quart_app.rabbitmq_client = MockRabbitMQClient()
    quart_app.twiliobot_client = MockTwilioBotClient()
    return quart_app


@pytest.mark.asyncio
async def test_receive_whatsapp_message_from_wrong_phone_number(app):
    async with QuartClient(app) as test_client:
        # Mocking form data
        form_data = {
            'MessageSid': 'test_sid',
            'From': 'whatsapp:+1234567890',
            'Body': 'Test message'
        }
        # Sending a POST request to /whatsapp endpoint
        response = await test_client.post("/whatsapp", form=form_data)
        # Assertions
        assert response.status_code == 400
        assert "Invalid phone number" in (await response.get_json())["error"]


@pytest.mark.asyncio
async def test_receive_whatsapp_message(app):
    async with QuartClient(app) as test_client:
        # Mocking form data
        form_data = {
            'MessageSid': 'test_sid',
            'From': 'whatsapp:+6281234567890',
            'Body': 'Test message'
        }
        # Sending a POST request to /whatsapp endpoint
        response = await test_client.post("/whatsapp", form=form_data)
        # Assertions
        assert response.status_code == 204


@pytest.mark.asyncio
async def test_receive_whatsapp_message_format_error(app):
    async with QuartClient(app) as test_client:
        # Mocking form data
        form_data = {
            'sid': 'test_sid',
            'from': 'whatsapp:+6281234567890',
            'body': 'Test message'
        }
        # Sending a POST request to /whatsapp endpoint
        response = await test_client.post("/whatsapp", form=form_data)
        # Assertions
        assert response.status_code == 400
        assert "Validation error" in (await response.get_json())["error"]


@pytest.mark.asyncio
async def test_receive_whatsapp_message_parsing_error(app):
    async with QuartClient(app) as test_client:
        # Mocking form data with an unparsable phone number
        form_data = {
            'MessageSid': 'test_sid',
            'From': 'whatsapp:abcd',
            'Body': 'Test message'
        }
        # Sending a POST request to /whatsapp endpoint
        response = await test_client.post("/whatsapp", form=form_data)
        # Assertions
        assert response.status_code == 400
        assert "Phone number parsing error" in (
            await response.get_json())["error"]


@pytest.mark.asyncio
async def test_receive_whatsapp_message_invalid_phone_number(app):
    async with QuartClient(app) as test_client:
        # Mocking form data with an invalid phone number
        form_data = {
            'MessageSid': 'test_sid',
            'From': 'whatsapp:+6281234567',
            'Body': 'Test message'
        }
        # Sending a POST request to /whatsapp endpoint
        response = await test_client.post("/whatsapp", form=form_data)
        # Assertions
        assert response.status_code == 400
        assert "Invalid phone number" in (
            await response.get_json())["error"]


@pytest.mark.asyncio
async def test_receive_whatsapp_message_missing_field(app):
    async with QuartClient(app) as test_client:
        # Mocking form data with a missing field (MessageSid)
        form_data = {
            'From': 'whatsapp:+6281234567890',
            'Body': 'Test message'
        }
        # Sending a POST request to /whatsapp endpoint
        response = await test_client.post("/whatsapp", form=form_data)
        # Assertions
        assert response.status_code == 400
        assert "Validation error" in (await response.get_json())["error"]
