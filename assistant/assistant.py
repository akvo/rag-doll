import os
import json
import logging

import pika

from ollama import Client
ROLE_USER='user'
ROLE_SYSTEM='system'
ROLE_ASSISTANT='assistant'
MSG_MESSAGE='message'
MSG_ROLE='role'
MSG_CONTENT='content'
MSG_RESPONSE='response'
MSG_STATUS='status'
MSG_SUCCESS='success'

logging.basicConfig(level=logging.INFO)

# --- Ollama section

class LLM:
    def __init__(self, chat_model: str):
        self.llm_client = Client(host=f"http://{os.getenv("OLLAMA_HOST")}:{os.getenv("OLLAMA_PORT")}")
        self.chat_model = chat_model
        pull_response = self.llm_client.pull(self.chat_model)
        if pull_response[MSG_STATUS] != MSG_SUCCESS:
            raise Exception(f"failed to pull {self.chat_model}: {pull_response}")

        self.messages = []
        self.append_message(ROLE_SYSTEM, "You are a Kenyan Extension Officer, specialised in agriculture. You cannot answer questions that are not about agriculture.") # XXX externalise...

    def chat(self, content: str) -> dict:
        self.append_message(ROLE_USER, content)
        response = self.llm_client.chat(model=self.chat_model, messages=self.messages)
        message = response[MSG_MESSAGE]
        self.append_message(message[MSG_ROLE], message[MSG_CONTENT])
        return response

    def append_message(self, role, content):
        self.messages.append({MSG_ROLE: role, MSG_CONTENT: content})
        # print(f"------- {self.messages}")

llm = LLM('mistral')

# --- RabbitMQ Section

RABBITMQ_QUEUE_USER_CHATS=os.getenv("RABBITMQ_QUEUE_USER_CHATS")
RABBITMQ_QUEUE_USER_CHAT_REPLIES=os.getenv("RABBITMQ_QUEUE_USER_CHAT_REPLIES")

def connect_and_create_queue():
    pika_credentials = pika.PlainCredentials(os.getenv("RABBITMQ_DEFAULT_USER"), os.getenv("RABBITMQ_DEFAULT_PASS"))
    pika_parameters = pika.ConnectionParameters(os.getenv("RABBITMQ_HOST"),
                                                int(os.getenv("RABBITMQ_PORT")),
                                                '/', pika_credentials)
    pika_connection = pika.BlockingConnection(pika_parameters)
    return pika_connection.channel()

user_chat_queue = connect_and_create_queue()
user_chat_queue.queue_declare(queue=RABBITMQ_QUEUE_USER_CHATS)

user_chat_reply_queue = connect_and_create_queue()
user_chat_reply_queue.queue_declare(queue=RABBITMQ_QUEUE_USER_CHAT_REPLIES)

def queue_message_and_llm_response_to_reply(queue_message: dict, llm_response: dict) -> str:
    reply = {
      'id': f"{queue_message['id']}-reply",
      'timestamp': f"{llm_response['created_at'][:-1]}+00:00", # replace 'Z' with +00:00
      'platform': queue_message['platform'],
      'to': queue_message['from'],
      'text': llm_response[MSG_MESSAGE][MSG_CONTENT]
    }
    return json.dumps(reply)


def publish_reliably(queue_message: str) -> None:
    global user_chat_reply_queue

    retries = 5
    while retries > 0:
        retries = retries - 1

        try:
            user_chat_reply_queue.basic_publish(exchange='', routing_key=RABBITMQ_QUEUE_USER_CHAT_REPLIES, body=queue_message)
            return
        except Exception as e:
            logger.warning(f"{type(e)}: {e}")

        sleep(5)
        user_chat_reply_queue = connect_and_create_queue()


def ask_llm_and_reply(ch, method, properties, body):
    logging.debug(f"Message received: ch: {ch}, method: {method}, properties: {properties}, body: {body}")
    queue_message = json.loads(body.decode('utf8'))

    llm_response = llm.chat(queue_message['text'])
    logging.debug(f"LLM replied: {llm_response}")

    publish_reliably(queue_message_and_llm_response_to_reply(queue_message, llm_response))


user_chat_queue.basic_consume(queue=os.getenv("RABBITMQ_QUEUE_USER_CHATS"),
                                 auto_ack=True,
                                 on_message_callback=ask_llm_and_reply)

user_chat_queue.start_consuming()

