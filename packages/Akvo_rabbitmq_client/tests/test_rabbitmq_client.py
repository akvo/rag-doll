import unittest
import asyncio
from unittest.mock import MagicMock
from Akvo_rabbitmq_client import rabbitmq_client


class TestRabbitMQClient(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.client = rabbitmq_client

    def tearDown(self):
        async def cleanup():
            await self.client.disconnect()

        self.loop.run_until_complete(cleanup())
        self.loop.close()

    def test_producer_and_consumer(self):
        async def test():
            await self.client.initialize()
            # Create a MagicMock object to mock the callback
            callback_mock = MagicMock()
            await self.client.consume(
                queue_name="test_queue",
                routing_key="test_queue",
                callback=callback_mock,
            )
            await self.client.producer(
                body="Test producer and consumer", routing_key="test_queue"
            )
            await asyncio.sleep(1)  # Allow some time for message consumption
            callback_mock.assert_called_once()

        self.loop.run_until_complete(test())


if __name__ == "__main__":
    unittest.main()
