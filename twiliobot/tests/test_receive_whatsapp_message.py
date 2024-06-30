import pytest
import os

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
async def test_receive_whatsapp_message(app):
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
        assert response.status_code == 204
        response_json = await response.get_json()
        assert response_json["message"] == "Ok"


@pytest.mark.asyncio
async def test_receive_whatsapp_message_error(app):
    async with QuartClient(app) as test_client:
        # Mocking form data
        form_data = {
            'sid': 'test_sid',
            'from': 'whatsapp:+1234567890',
            'body': 'Test message'
        }
        # Sending a POST request to /whatsapp endpoint
        response = await test_client.post("/whatsapp", form=form_data)
        # Assertions
        assert response.status_code == 500
