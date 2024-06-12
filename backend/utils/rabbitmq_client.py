import os
import aio_pika
import logging

RABBITMQ_USER = os.getenv('RABBITMQ_DEFAULT_USER')
RABBITMQ_PASS = os.getenv('RABBITMQ_DEFAULT_PASS')
RABBITMQ_HOST = str(os.getenv('RABBITMQ_HOST'))
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
            # Declare a topic exchange
            exchange = await self.channel.declare_exchange(
                RABBITMQ_EXCHANGE_USER_CHATS,
                aio_pika.ExchangeType.TOPIC
            )
            # Declare a queue for user chats
            user_chats_queue = await self.channel.declare_queue(
                RABBITMQ_QUEUE_USER_CHATS,
                durable=True
            )
            # Bind the user chats queue
            # to the topic exchange with a routing key
            await user_chats_queue.bind(
                exchange, routing_key=RABBITMQ_ROUTE_USER_CHAT)
            # Declare a queue for user chat replies
            user_chat_replies_queue = await self.channel.declare_queue(
                RABBITMQ_QUEUE_USER_CHAT_REPLIES,
                durable=True
            )
            # Bind the user chat replies queue
            # to the topic exchange with a routing key
            await user_chat_replies_queue.bind(
                exchange, routing_key=RABBITMQ_ROUTE_USER_CHAT_REPLY)
        except Exception as e:
            logger.error(f"Error initializing RabbitMQ client: {e}")

    async def user_chats_callback(self, message: aio_pika.IncomingMessage):
        try:
            async with message.process():
                logger.info(f"Received user chat: {message.body.decode()}")
        except Exception as e:
            logger.error(f"Error processing user chat message: {e}")

    async def user_chat_replies_callback(
        self, message: aio_pika.IncomingMessage
    ):
        try:
            async with message.process():
                logger.info(
                    f"Received user chat replies: {message.body.decode()}")
        except Exception as e:
            logger.error(f"Error processing user chat replies message: {e}")

    async def chat_history_callback(self, message: aio_pika.IncomingMessage):
        try:
            async with message.process():
                res = message.body.decode()
                logger.info(f"Received message for chat history: {res}")
        except Exception as e:
            logger.error(f"Error processing chat history message: {e}")

    async def producer(self, body: str):
        try:
            await self.connect()
            # Creating a channel
            channel = await self.connection.channel()
            exchange = await channel.declare_exchange(
                RABBITMQ_EXCHANGE_USER_CHATS,
                aio_pika.ExchangeType.TOPIC,
            )
            # Ensure message is persistent
            message = aio_pika.Message(
                body=body.encode('utf-8'),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )
            # Sending the message with a routing key
            await exchange.publish(
                message, routing_key=RABBITMQ_ROUTE_USER_CHAT_REPLY)
        except Exception as e:
            logger.error(f"Error publishing message: {e}")

    async def consumer_user_chats(self):
        try:
            await self.connect()
            # Creating a channel
            channel = await self.connection.channel()
            await channel.set_qos(prefetch_count=1)
            # declaring exchange
            exchange = await channel.declare_exchange(
                RABBITMQ_EXCHANGE_USER_CHATS,
                aio_pika.ExchangeType.TOPIC
            )
            # Declaring a queue
            queue = await channel.declare_queue(
                RABBITMQ_QUEUE_USER_CHATS, durable=True)
            # Binding the queue to the exchange with a routing key
            await queue.bind(exchange, routing_key=RABBITMQ_ROUTE_USER_CHAT)
            # Start listening to the queue
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    await self.user_chats_callback(message)
        except Exception as e:
            logger.error(f"Error consuming user chats: {e}")

    async def consumer_user_chat_replies(self):
        try:
            # Consumer for user chat replies
            await self.connect()
            # Creating a channel
            channel = await self.connection.channel()
            await channel.set_qos(prefetch_count=1)
            # declaring exchange
            exchange = await channel.declare_exchange(
                RABBITMQ_EXCHANGE_USER_CHATS,
                aio_pika.ExchangeType.TOPIC
            )
            # Declaring a queue
            queue = await channel.declare_queue(
                RABBITMQ_QUEUE_USER_CHAT_REPLIES, durable=True)
            # Binding the queue to the exchange with a routing key
            await queue.bind(
                exchange, routing_key=RABBITMQ_ROUTE_USER_CHAT_REPLY)
            # Start listening to the queue
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    await self.user_chat_replies_callback(message)
        except Exception as e:
            logger.error(f"Error consuming user chat replies: {e}")

    async def consumer_chat_history(self):
        try:
            await self.connect()
            # Creating a channel
            channel = await self.connection.channel()
            await channel.set_qos(prefetch_count=1)
            # declaring exchange
            exchange = await channel.declare_exchange(
                RABBITMQ_EXCHANGE_USER_CHATS,
                aio_pika.ExchangeType.TOPIC
            )
            # Declaring an anonymous exclusive queue
            queue = await channel.declare_queue(exclusive=True)
            # Binding the queue to the exchange with a wildcard routing key
            await queue.bind(exchange, routing_key="#")
            # Start listening to the queue
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    await self.chat_history_callback(message)
        except Exception as e:
            logger.error(f"Error consuming chat history: {e}")

    async def send_magic_link(self, body: str):
        try:
            await self.channel.default_exchange.publish(
                aio_pika.Message(body=body.encode('utf-8')),
                routing_key=RABBITMQ_QUEUE_USER_CHAT_REPLIES
            )
        except Exception as e:
            logger.error(f"Error sending magic link: {e}")


rabbitmq_client = RabbitMQClient()
