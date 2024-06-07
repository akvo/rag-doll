import pika
import json
import os

def send_test_message_to_queue():
    pika_credentials = pika.PlainCredentials(os.getenv("RABBITMQ_DEFAULT_USER"), os.getenv("RABBITMQ_DEFAULT_PASS"))
    pika_parameters = pika.ConnectionParameters(os.getenv("RABBITMQ_HOST"),
                                                int(os.getenv("RABBITMQ_PORT")),
                                                '/', pika_credentials)
    connection = pika.BlockingConnection(pika_parameters)
    channel = connection.channel()

    test_message = {
        'to': {
            'phone': '+6281999103535',
        },
        'text': 'You can login into APP_NAME by click this link: http://localhost:3001/verify/123456'
    }

    channel.basic_publish(exchange='', routing_key=os.getenv("RABBITMQ_QUEUE_USER_CHAT_REPLIES"), body=json.dumps(test_message))
    connection.close()

send_test_message_to_queue()