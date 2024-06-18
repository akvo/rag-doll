import os
import aio_pika
import logging

from typing import Callable


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RabbitMQClient:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.RABBITMQ_USER = os.getenv('RABBITMQ_USER')
        self.RABBITMQ_PASS = os.getenv('RABBITMQ_PASS')
        self.RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
        self.RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT'))
        self.RABBITMQ_EXCHANGE_USER_CHATS = os.getenv(
            'RABBITMQ_EXCHANGE_USER_CHATS')

    async def connect(self):
        if not self.connection or self.connection.is_closed:
            self.connection = await aio_pika.connect_robust(
                host=self.RABBITMQ_HOST,
                port=self.RABBITMQ_PORT,
                login=self.RABBITMQ_USER,
                password=self.RABBITMQ_PASS
            )

    async def close_connection(self):
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("RabbitMQ connection closed.")

    async def initialize(self):
        try:
            await self.connect()
            self.channel = await self.connection.channel()
            self.exchange = await self.channel.declare_exchange(
                self.RABBITMQ_EXCHANGE_USER_CHATS,
                aio_pika.ExchangeType.TOPIC
            )
        except Exception as e:
            logger.error(f"Error initializing RabbitMQ client: {e}")

    async def producer(
        self,
        body: str,
        routing_key: str,
        reply_to: str = None
    ):
        try:
            await self.connect()
            if reply_to:
                routing_key = f"{routing_key}.{reply_to}"
            message = aio_pika.Message(
                body=body.encode('utf-8'),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                headers={"reply_to": reply_to}
            )
            await self.exchange.publish(
                message,
                routing_key=routing_key
            )
            logger.info(f"Message sent: {body}, routing_key: {routing_key}")
        except Exception as e:
            logger.error(f"Error publishing message: {e}")

    async def consumer_callback(
        self,
        message: aio_pika.IncomingMessage,
        routing_key: str,
        callback: Callable = None
    ):
        try:
            async with message.process():
                body = message.body.decode()
                reply_to = message.headers.get("reply_to")
                log = f"Received {routing_key} message: {body}"
                logger.info(
                    f"{log}, Reply To: {reply_to}"
                )
                if callback:
                    callback(body=body)
        except Exception as e:
            logger.error(f"Error processing {routing_key} message: {e}")

    async def consume(
        self,
        queue_name: str,
        routing_key: str,
        callback: Callable = None
    ):
        if callback and not callable(callback):
            raise TypeError(f"The argument {callback} is not callable")
        try:
            await self.connect()
            queue = await self.channel.declare_queue(queue_name, durable=True)
            await queue.bind(self.exchange, routing_key=routing_key)
            await queue.consume(lambda msg: self.consumer_callback(
                message=msg,
                routing_key=routing_key,
                callback=callback
            ))
            logger.info(f"Consume Q:{queue_name} | RK:{routing_key}")
        except Exception as e:
            logger.error(f"Error consuming {routing_key}: {e}")


rabbitmq_client = RabbitMQClient()
