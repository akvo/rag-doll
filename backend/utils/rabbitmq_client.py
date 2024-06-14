import os
import aio_pika
import logging

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
        queue_name: str,
        consumer_type: str
    ):
        try:
            async with message.process():
                body = message.body.decode()
                reply_to = message.headers.get("reply_to")
                log = f"Received {consumer_type} message: {body}"
                logger.info(
                    f"{log}, Reply To: {reply_to}"
                )
                # Handle the message based on reply_to value
                if (
                    queue_name == RABBITMQ_QUEUE_USER_CHAT_REPLIES and
                    reply_to == RABBITMQ_QUEUE_TWILIOBOT_REPLIES
                ):
                    # Process message intended for TwilioBot
                    await self.producer(
                        body=body,
                        routing_key=RABBITMQ_QUEUE_USER_CHAT_REPLIES,
                        reply_to=reply_to
                    )
                if (
                    queue_name == RABBITMQ_QUEUE_USER_CHAT_REPLIES and
                    reply_to == RABBITMQ_QUEUE_SLACKBOT_REPLIES
                ):
                    # Process message intended for SlackBot
                    pass
        except Exception as e:
            logger.error(f"Error processing {consumer_type} message: {e}")

    async def consume(
        self,
        queue_name: str,
        routing_key: str,
    ):
        try:
            await self.connect()
            queue = await self.channel.declare_queue(queue_name, durable=True)
            await queue.bind(self.exchange, routing_key=routing_key)
            await queue.consume(lambda msg: self.consumer_callback(
                message=msg,
                queue_name=queue_name,
                consumer_type=routing_key
            ))
            logger.info(f"Consume Q:{queue_name} | RK:{routing_key}")
        except Exception as e:
            logger.error(f"Error consuming {routing_key}: {e}")

    async def consume_user_chats(self):
        await self.consume(
            queue_name=RABBITMQ_QUEUE_USER_CHATS,
            routing_key=RABBITMQ_QUEUE_USER_CHATS,
        )

    async def consume_user_chat_replies(self):
        await self.consume(
            queue_name=RABBITMQ_QUEUE_USER_CHAT_REPLIES,
            routing_key=RABBITMQ_QUEUE_USER_CHAT_REPLIES,
        )

    async def consume_twiliobot(self):
        await self.consume(
            queue_name=RABBITMQ_QUEUE_TWILIOBOT_REPLIES,
            routing_key=f"*.{RABBITMQ_QUEUE_TWILIOBOT_REPLIES}",
        )

    async def consume_chat_history(self):
        await self.consume(
            queue_name=RABBITMQ_QUEUE_HISTORIES,
            routing_key="#",
        )


rabbitmq_client = RabbitMQClient()
