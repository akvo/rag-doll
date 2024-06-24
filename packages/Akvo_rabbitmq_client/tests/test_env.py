import unittest
from Akvo_rabbitmq_client import rabbitmq_client


class TestRabbitMQClientEnv(unittest.TestCase):
    def test_env_available(self):
        self.assertTrue(rabbitmq_client.RABBITMQ_USER)
        self.assertTrue(rabbitmq_client.RABBITMQ_PASS)
        self.assertTrue(rabbitmq_client.RABBITMQ_HOST)
        self.assertTrue(rabbitmq_client.RABBITMQ_PORT)
        self.assertTrue(rabbitmq_client.RABBITMQ_EXCHANGE_USER_CHATS)


if __name__ == '__main__':
    unittest.main()
