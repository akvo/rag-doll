import os
import aio_pika
import logging
import asyncio
from typing import Callable
from aiormq.exceptions import AMQPConnectionError, ConnectionClosed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingEnvironmentVariableError(Exception):
    def __init__(self, variable_name):
        self.variable_name = variable_name
        self.message = (
            f"Missing required environment variable: {variable_name}"
        )
        super().__init__(self.message)


class RabbitMQClient:
    def __init__(self):
        self.RABBITMQ_USER = os.getenv("RABBITMQ_USER")
        self.RABBITMQ_PASS = os.getenv("RABBITMQ_PASS")
        self.RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
        self.RABBITMQ_PORT = os.getenv("RABBITMQ_PORT")
        self.RABBITMQ_EXCHANGE_USER_CHATS = os.getenv(
            "RABBITMQ_EXCHANGE_USER_CHATS"
        )
        self.validate_environment_variables()
        self.RABBITMQ_PORT = int(self.RABBITMQ_PORT)
        self.connection = None
        self.channel = None
        self.exchange = None

    def validate_environment_variables(self):
        required_variables = [
            "RABBITMQ_USER",
            "RABBITMQ_PASS",
            "RABBITMQ_HOST",
            "RABBITMQ_PORT",
            "RABBITMQ_EXCHANGE_USER_CHATS",
        ]
        for var in required_variables:
            if getattr(self, var) is None:
                raise MissingEnvironmentVariableError(var)

    async def connect(self, max_retries=5):
        retries = 0
        while retries < max_retries:
            try:
                self.connection = await aio_pika.connect(
                    host=self.RABBITMQ_HOST,
                    port=self.RABBITMQ_PORT,
                    login=self.RABBITMQ_USER,
                    password=self.RABBITMQ_PASS,
                    timeout=60,
                )
                break
            except (ConnectionClosed, AMQPConnectionError) as e:
                logger.error(f"RabbitMQ connection error: {e}")
                retries += 1
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error connecting to RabbitMQ: {e}")
                retries += 1
                await asyncio.sleep(5)
        if retries >= max_retries:
            raise Exception("Maximum retries exceeded")

    async def disconnect(self):
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("RabbitMQ connection closed.")

    async def initialize(self):
        try:
            await self.connect()
            self.channel = await self.connection.channel()
            self.exchange = await self.channel.declare_exchange(
                self.RABBITMQ_EXCHANGE_USER_CHATS,
                aio_pika.ExchangeType.DIRECT,
                durable=True,
            )
        except (ConnectionClosed, AMQPConnectionError) as e:
            logger.error(f"RabbitMQ initialization error: {e}")
            self.initialize()
        except Exception as e:
            logger.error(f"Unexpected error initializing RabbitMQ client: {e}")

    async def producer(self, body: str, routing_key: str):
        try:
            await self.initialize()
            message = aio_pika.Message(
                body=body.encode("utf-8"),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )
            await self.exchange.publish(message, routing_key=routing_key)
            logger.info(f"Message sent: {body}, routing_key: {routing_key}")
        except (ConnectionClosed, AMQPConnectionError) as e:
            logger.error(f"RabbitMQ publish error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error publishing message: {e}")

    async def consumer_callback(
        self,
        message: aio_pika.IncomingMessage,
        routing_key: str,
        callback: Callable,
    ):
        try:
            async with message.process():
                body = message.body.decode()
                logger.info(f"Received message from {routing_key}: {body}")
                if callback:
                    await callback(body=body)
        except Exception as e:
            logger.error(f"Error processing {routing_key} message: {e}")

    async def consume(
        self,
        queue_name: str,
        routing_key: str,
        callback: Callable = None,
        sleepTime=25,
    ):
        while True:
            try:
                await self.initialize()
                queue = await self.channel.declare_queue(
                    queue_name, durable=True
                )
                await queue.bind(self.exchange, routing_key=routing_key)
                await queue.consume(
                    lambda msg: self.consumer_callback(
                        message=msg, routing_key=routing_key, callback=callback
                    )
                )
                logger.info(
                    f"Consuming from Q:{queue_name} | RK:{routing_key}"
                )
                await asyncio.sleep(sleepTime)
            except (ConnectionClosed, AMQPConnectionError) as e:
                logger.error(f"RabbitMQ consume error: {e}")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error consuming {routing_key}: {e}")
                await asyncio.sleep(5)


try:
    rabbitmq_client = RabbitMQClient()
except MissingEnvironmentVariableError as e:
    logger.error(f"MissingEnvironmentVariableError: {e}")
