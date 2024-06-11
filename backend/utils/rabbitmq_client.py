import os
import pika
import time
import threading


RABBITMQ_USER = os.getenv('RABBITMQ_USER')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS')
RABBITMQ_HOST = str(os.getenv('RABBITMQ_HOST'))
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT'))
RABBITMQ_QUEUE_USER_CHATS = os.getenv('RABBITMQ_QUEUE_USER_CHATS')
RABBITMQ_QUEUE_USER_CHAT_REPLIES = os.getenv(
    'RABBITMQ_QUEUE_USER_CHAT_REPLIES')


def connect():
    # starting connection
    credentials = pika.PlainCredentials(
        username=RABBITMQ_USER, password=RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST, port=RABBITMQ_PORT,
        virtual_host='/', credentials=credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    return connection, channel


def create_queue(channel, queue: str):
    channel.queue_declare(queue=queue)
    return channel


class RabbitMQClient(threading.Thread):
    def __init__(self):
        # init queue
        self.connection, self.channel = connect()
        self.user_chat_queue = create_queue(
            channel=self.channel,
            queue=RABBITMQ_QUEUE_USER_CHATS)
        self.user_chat_reply_queue = create_queue(
            channel=self.channel,
            queue=RABBITMQ_QUEUE_USER_CHAT_REPLIES)

    def consumer_callback(self, ch, method, properties, body):
        print(f"[x] Received {body}")

    def producer(self, body: str):
        self.channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_QUEUE_USER_CHAT_REPLIES,
            body=body)
        self.connection.close()

    def consumer(self):
        # TODO :: Change the consumer
        self.user_chat_queue.basic_consume(
            queue=RABBITMQ_QUEUE_USER_CHAT_REPLIES,
            on_message_callback=self.consumer_callback,
            auto_ack=True)
        print(' [*] Waiting for messages. To exit press CTRL+C')
        self.user_chat_queue.start_consuming()

    def run(self, *args, **kwargs):
        while True:
            self.consumer()
            time.sleep()


class RabbitMQBackgroundTasks(threading.Thread):
    def run(self, *args, **kwargs):
        while True:
            RabbitMQClient().consumer()
            time.sleep()
