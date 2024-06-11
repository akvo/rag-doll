import os
import aio_pika
import asyncio

RABBITMQ_USER = os.getenv('RABBITMQ_DEFAULT_USER')
RABBITMQ_PASS = os.getenv('RABBITMQ_DEFAULT_PASS')
RABBITMQ_HOST = str(os.getenv('RABBITMQ_HOST'))
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT'))
RABBITMQ_QUEUE_USER_CHATS = os.getenv('RABBITMQ_QUEUE_USER_CHATS')
RABBITMQ_QUEUE_USER_CHAT_REPLIES = os.getenv('RABBITMQ_QUEUE_USER_CHAT_REPLIES')
RABBITMQ_QUEUE_MAGIC_LINKS = os.getenv('RABBITMQ_QUEUE_MAGIC_LINKS')


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
        await self.connect()
        self.channel = await self.connection.channel()
        await self.channel.declare_queue(
            RABBITMQ_QUEUE_USER_CHATS, durable=True)
        await self.channel.declare_queue(
            RABBITMQ_QUEUE_USER_CHAT_REPLIES, durable=True)

    async def consumer_callback(self, message: aio_pika.IncomingMessage):
        async with message.process():
            print(f"[x] Received {message.body.decode()}")

    async def producer(self, body: str):
        await self.channel.default_exchange.publish(
            aio_pika.Message(body=body.encode()),
            routing_key=RABBITMQ_QUEUE_USER_CHAT_REPLIES
        )

    async def consumer(self):
        queue = await self.channel.declare_queue(
            RABBITMQ_QUEUE_USER_CHATS, durable=True)
        async with queue.iterator() as queue_iter:
            print("[x] Consumer started")
            async for message in queue_iter:
                await self.consumer_callback(message)
                # Breaking out of the loop if a specific condition is met
                if RABBITMQ_QUEUE_USER_CHATS in message.body.decode():
                    break


rabbitmq_client = RabbitMQClient()
