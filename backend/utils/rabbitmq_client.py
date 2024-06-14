import os
import aio_pika
import logging

from typing import Callable

# Configuration
RABBITMQ_USER = os.getenv('RABBITMQ_USER')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT'))
RABBITMQ_EXCHANGE_USER_CHATS = os.getenv('RABBITMQ_EXCHANGE_USER_CHATS')
RABBITMQ_QUEUE_USER_CHATS = os.getenv('RABBITMQ_QUEUE_USER_CHATS')
RABBITMQ_QUEUE_USER_CHAT_REPLIES = os.getenv('RABBITMQ_QUEUE_USER_CHAT_REPLIES')
RABBITMQ_QUEUE_TWILIOBOT_REPLIES = os.getenv('RABBITMQ_QUEUE_TWILIOBOT_REPLIES')
RABBITMQ_QUEUE_SLACKBOT_REPLIES = os.getenv('RABBITMQ_QUEUE_SLACKBOT_REPLIES')
RABBITMQ_QUEUE_HISTORIES = os.getenv('RABBITMQ_QUEUE_HISTORIES')


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
                # use callback function
                if callback:
                    callback(body=body)
                else:
                    # Handle the message based on reply_to value
                    if (
                        routing_key == RABBITMQ_QUEUE_USER_CHAT_REPLIES and
                        reply_to == RABBITMQ_QUEUE_TWILIOBOT_REPLIES
                    ):
                        # Process message intended for TwilioBot
                        await self.producer(
                            body=body,
                            routing_key=RABBITMQ_QUEUE_USER_CHAT_REPLIES,
                            reply_to=reply_to
                        )
                    elif (
                        routing_key == RABBITMQ_QUEUE_USER_CHAT_REPLIES and
                        reply_to == RABBITMQ_QUEUE_SLACKBOT_REPLIES
                    ):
                        # Process message intended for SlackBot
                        await self.producer(
                            body=body,
                            routing_key=RABBITMQ_QUEUE_USER_CHAT_REPLIES,
                            reply_to=reply_to
                        )
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

    async def consume_user_chats(self, callback: Callable = None):
        await self.consume(
            queue_name=RABBITMQ_QUEUE_USER_CHATS,
            routing_key=RABBITMQ_QUEUE_USER_CHATS,
            callback=callback
        )

    async def consume_user_chat_replies(self, callback: Callable = None):
        await self.consume(
            queue_name=RABBITMQ_QUEUE_USER_CHAT_REPLIES,
            routing_key=RABBITMQ_QUEUE_USER_CHAT_REPLIES,
            callback=callback
        )

    async def consume_twiliobot(self, callback: Callable = None):
        await self.consume(
            queue_name=RABBITMQ_QUEUE_TWILIOBOT_REPLIES,
            routing_key=f"*.{RABBITMQ_QUEUE_TWILIOBOT_REPLIES}",
            callback=callback
        )

    async def consume_slackbot(self, callback: Callable = None):
        await self.consume(
            queue_name=RABBITMQ_QUEUE_SLACKBOT_REPLIES,
            routing_key=f"*.{RABBITMQ_QUEUE_SLACKBOT_REPLIES}",
            callback=callback
        )

    async def consume_chat_history(self, callback: Callable = None):
        await self.consume(
            queue_name=RABBITMQ_QUEUE_HISTORIES,
            routing_key="#",
            callback=callback
        )


rabbitmq_client = RabbitMQClient()
