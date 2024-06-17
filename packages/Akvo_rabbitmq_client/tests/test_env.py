import unittest
from Akvo_rabbitmq_client.rabbitmq_client import (
    RABBITMQ_USER,
    RABBITMQ_PASS,
    RABBITMQ_EXCHANGE_USER_CHATS,
    RABBITMQ_QUEUE_USER_CHATS,
    RABBITMQ_QUEUE_USER_CHAT_REPLIES,
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_QUEUE_TWILIOBOT_REPLIES,
    RABBITMQ_QUEUE_SLACKBOT_REPLIES,
    RABBITMQ_QUEUE_HISTORIES,
)


class TestRabbitMQClientEnv(unittest.TestCase):
    def test_env_available(self):
        self.assertTrue(RABBITMQ_USER)
        self.assertTrue(RABBITMQ_PASS)
        self.assertTrue(RABBITMQ_EXCHANGE_USER_CHATS)
        self.assertTrue(RABBITMQ_QUEUE_USER_CHATS)
        self.assertTrue(RABBITMQ_QUEUE_USER_CHAT_REPLIES)
        self.assertTrue(RABBITMQ_HOST)
        self.assertTrue(RABBITMQ_PORT)
        self.assertTrue(RABBITMQ_QUEUE_TWILIOBOT_REPLIES)
        self.assertTrue(RABBITMQ_QUEUE_SLACKBOT_REPLIES)
        self.assertTrue(RABBITMQ_QUEUE_HISTORIES)


if __name__ == '__main__':
    unittest.main()
