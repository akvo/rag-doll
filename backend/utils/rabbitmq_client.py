import os
import aio_pika
import logging

# Configuration
RABBITMQ_USER = os.getenv('RABBITMQ_DEFAULT_USER')
RABBITMQ_PASS = os.getenv('RABBITMQ_DEFAULT_PASS')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT'))
RABBITMQ_EXCHANGE_USER_CHATS = os.getenv('RABBITMQ_EXCHANGE_USER_CHATS')
RABBITMQ_QUEUE_USER_CHATS = os.getenv('RABBITMQ_QUEUE_USER_CHATS')
RABBITMQ_QUEUE_USER_CHAT_REPLIES = os.getenv('RABBITMQ_QUEUE_USER_CHAT_REPLIES')
RABBITMQ_ROUTE_USER_CHAT = os.getenv('RABBITMQ_ROUTE_USER_CHAT')
RABBITMQ_ROUTE_USER_CHAT_REPLY = os.getenv('RABBITMQ_ROUTE_USER_CHAT_REPLY')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RabbitMQClient:
    def __init__(self):
        self.connection = None
        self.channel = None

    async def connect(self):
        if not self.connection or self.connection.is_closed:
            self.connection = await aio_pika.connect_robust(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                login=RABBITMQ_USER,
                password=RABBITMQ_PASS
            )

    async def initialize(self):
        try:
            await self.connect()
            self.channel = await self.connection.channel()
            self.exchange = await self.channel.declare_exchange(
                RABBITMQ_EXCHANGE_USER_CHATS,
                aio_pika.ExchangeType.TOPIC
            )
            await self.declare_queues()
        except Exception as e:
            logger.error(f"Error initializing RabbitMQ client: {e}")

    async def declare_queues(self):
        try:
            # Declare and bind user chats queue
            user_chats_queue = await self.channel.declare_queue(
                RABBITMQ_QUEUE_USER_CHATS,
                durable=True
            )
            await user_chats_queue.bind(
                self.exchange,
                routing_key=RABBITMQ_ROUTE_USER_CHAT
            )

            # Declare and bind user chat replies queue
            user_chat_replies_queue = await self.channel.declare_queue(
                RABBITMQ_QUEUE_USER_CHAT_REPLIES,
                durable=True
            )
            await user_chat_replies_queue.bind(
                self.exchange,
                routing_key=RABBITMQ_ROUTE_USER_CHAT_REPLY
            )
        except Exception as e:
            logger.error(f"Error declaring or binding queues: {e}")

    async def producer(self, body: str):
        try:
            await self.connect()
            message = aio_pika.Message(
                body=body.encode('utf-8'),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )
            await self.exchange.publish(
                message,
                routing_key=RABBITMQ_ROUTE_USER_CHAT_REPLY
            )
            logger.info(f"Message sent: {body}")
        except Exception as e:
            logger.error(f"Error publishing message: {e}")

    async def consumer_callback(
        self,
        message: aio_pika.IncomingMessage,
        consumer_type: str
    ):
        try:
            async with message.process():
                logger.info(
                    f"Received {consumer_type} message: {message.body.decode()}"
                )
        except Exception as e:
            logger.error(f"Error processing {consumer_type} message: {e}")

    async def consume_user_chats(self):
        await self.consume(
            RABBITMQ_QUEUE_USER_CHATS,
            RABBITMQ_ROUTE_USER_CHAT,
            "user chat"
        )

    async def consume_user_chat_replies(self):
        await self.consume(
            RABBITMQ_QUEUE_USER_CHAT_REPLIES,
            RABBITMQ_ROUTE_USER_CHAT_REPLY,
            "user chat reply"
        )

    async def consume(self, queue_name: str, routing_key: str, consumer_type: str):
        try:
            await self.connect()
            queue = await self.channel.declare_queue(queue_name, durable=True)
            await queue.bind(self.exchange, routing_key=routing_key)
            await queue.consume(lambda msg: self.consumer_callback(
                msg, consumer_type
            ))
        except Exception as e:
            logger.error(f"Error consuming {consumer_type}: {e}")

    async def consume_chat_history(self):
        try:
            await self.connect()
            queue = await self.channel.declare_queue(exclusive=True)
            await queue.bind(self.exchange, routing_key="#")
            await queue.consume(
                lambda msg: self.consumer_callback(msg, "chat history")
            )
        except Exception as e:
            logger.error(f"Error consuming chat history: {e}")

    async def send_magic_link(self, body: str):
        try:
            await self.channel.default_exchange.publish(
                aio_pika.Message(body=body.encode('utf-8')),
                routing_key=RABBITMQ_ROUTE_USER_CHAT_REPLY
            )
        except Exception as e:
            logger.error(f"Error sending magic link: {e}")


rabbitmq_client = RabbitMQClient()
