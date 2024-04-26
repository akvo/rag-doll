import os
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

logging.basicConfig(level=logging.DEBUG)

# --- Ollama section

class LLM:
    def __init__(self, chat_model, image_model):
        llm_client = Client(host=f"http://{os.getenv("OLLAMA_HOST")}:{os.getenv("OLLAMA_PORT")}")
        self.chat_model = chat_model
        pull_response = llm_client.pull(self.chat_model)
        if pull_response[MSG_STATUS] != MSG_SUCCESS:
            raise Exception(f"failed to pull {self.chat_model}: {pull_response}")

        self.image_model = image_model
        pull_response = llm_client.pull(self.image_model)
        if pull_response[MSG_STATUS] != MSG_SUCCESS:
            raise Exception(f"failed to pull {self.image_model}: {pull_response}")

        self.messages = []
        self.append_message(ROLE_SYSTEM, "You are a Kenyan Extension Officer, specialised in agriculture. You cannot answer questions that are not about agriculture.")

    def chat(self, content):
        self.append_message(ROLE_USER, content)
        response = llm_client.chat(model=self.chat_model, messages=self.messages)
        message = response[MSG_MESSAGE]
        self.append_message(message[MSG_ROLE], message[MSG_CONTENT])
        return message[MSG_CONTENT]

    def check_image(self, image):
        self.append_message(ROLE_USER, f"{IMAGE_PROMPT}: {image}")
        response = llm_client.generate(model=self.image_model, prompt=IMAGE_PROMPT, images=[image])
        message = response[MSG_RESPONSE]
        self.append_message(ROLE_ASSISTANT, message)
        return f"I looked at {image}. {message}"

    def append_message(self, role, content):
        self.messages.append({MSG_ROLE: role, MSG_CONTENT: content})
        # print(f"------- {self.messages}")

llm = LLM('mistral', 'llava')

# --- RabbitMQ Section

pika_credentials = pika.PlainCredentials(os.getenv("RABBITMQ_DEFAULT_USER"), os.getenv("RABBITMQ_DEFAULT_PASS"))
pika_parameters = pika.ConnectionParameters(os.getenv("RABBITMQ_HOST"),
                                            int(os.getenv("RABBITMQ_PORT")),
                                            '/', pika_credentials)
pika_connection = pika.BlockingConnection(pika_parameters)
pika_channel = pika_connection.channel()

queue_name = os.getenv("RABBITMQ_QUEUE_USER_CHATS")
message_queue.queue_declare(queue=queue_name)

