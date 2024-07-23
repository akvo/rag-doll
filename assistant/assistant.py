import os
import json
import pika
import logging
import chromadb
from time import sleep
from openai import OpenAI

logging.basicConfig(level=logging.INFO)

ROLE_USER = "user"
ROLE_SYSTEM = "system"
ROLE_ASSISTANT = "assistant"
MSG_MESSAGE = "message"
MSG_ROLE = "role"
MSG_CONTENT = "content"
MSG_RESPONSE = "response"
MSG_STATUS = "status"
MSG_SUCCESS = "success"


# ChromaDB section

CHROMADB_HOST: str = os.getenv('CHROMADB_HOST')
CHROMADB_PORT: int = os.getenv('CHROMADB_PORT')
CHROMADB_COLLECTION: str = os.getenv('CHROMADB_COLLECTION')

def connect_to_chromadb() -> chromadb.Collection:
    '''
        Connect to ChromaDB. The ChromaDB service takes a second or so to start,
        so we have a crude retry loop. Once connected. we clear the collection
        and recreate it. This ensures the collection is always completely up to
        date.
    '''
    chromadb_client = None
    while chromadb_client == None:
        try:
            logger.info(f"trying http://{CHROMADB_HOST}:{CHROMADB_PORT}/{CHROMADB_COLLECTION}...")
            chromadb_client = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT, settings=chromadb.Settings(anonymized_telemetry=False))
            return chromadb_client.get_collection(name=CHROMADB_COLLECTION)
        except Exception as e:
            logger.warn(f"unable to connect to http://{CHROMADB_HOST}:{CHROMADB_PORT}, retrying...: {type(e)}: {e}")
            chromadb_client = None
            time.sleep(1)


def query_collection(collection: chromadb.Collection, prompt: str) -> str:
    # Assuming we query by text for simplicity
    query_result = collection.query(
        query_texts=[prompt],
        n_results=5,
        include=["documents"]
    )
    return json.dumps(query_result["documents"])

chromadb_collection: chromadb.Collection = connect_to_chromadb()

# --- LLM section

class LLM:
    def __init__(self, chat_model: str):
        self.chat_model = chat_model
        self.llm_client = OpenAI()
        self.messages = []
        self.append_message(ROLE_SYSTEM, os.getenv("ASSISTANT_ROLE"))

    def chat(self, content: str) -> dict:
        self.append_message(ROLE_USER, content)
        response = self.llm_client.chat.completions.create(
            model=self.chat_model, messages=self.messages
        )
        logging.info(f"OPENAI RESPONSE: {response.choices[0].message.content}")
        message = response.choices[0].message
        self.append_message(message.role, message.content)
        return message.content

    def append_message(self, role, content):
        self.messages.append({MSG_ROLE: role, MSG_CONTENT: str(content)})


llm = LLM(os.getenv("OPENAI_CHAT_MODEL"))


# --- RabbitMQ Section

def connect_and_create_queue(queue: str):
    pika_credentials = pika.PlainCredentials(
        os.getenv("RABBITMQ_USER"), os.getenv("RABBITMQ_PASS")
    )
    pika_parameters = pika.ConnectionParameters(
        os.getenv("RABBITMQ_HOST"),
        int(os.getenv("RABBITMQ_PORT")),
        "/",
        pika_credentials,
    )
    pika_connection = pika.BlockingConnection(pika_parameters)
    q = pika_connection.channel()
    q.queue_declare(queue=queue)
    return q


RABBITMQ_QUEUE_USER_CHATS = os.getenv("RABBITMQ_QUEUE_USER_CHATS")
user_chat_queue = connect_and_create_queue(RABBITMQ_QUEUE_USER_CHATS)
RABBITMQ_QUEUE_USER_CHAT_REPLIES = os.getenv("RABBITMQ_QUEUE_USER_CHAT_REPLIES")
user_chat_reply_queue = connect_and_create_queue(
    RABBITMQ_QUEUE_USER_CHAT_REPLIES
)


def queue_message_and_llm_response_to_reply(
    queue_message: dict, llm_response: dict
) -> str:
    reply = {
        "id": f"{queue_message['id']}-reply",
        "timestamp": f"{llm_response['created_at'][:-1]}+00:00",  # noqa replace 'Z' with +00:00
        "platform": queue_message["platform"],
        "to": queue_message["from"],
        "text": llm_response[MSG_MESSAGE][MSG_CONTENT],
    }
    return json.dumps(reply)


def publish_reliably(queue_message: str) -> None:
    global user_chat_reply_queue

    retries = 5
    while retries > 0:
        retries = retries - 1

        try:
            user_chat_reply_queue.basic_publish(
                exchange="",
                routing_key=RABBITMQ_QUEUE_USER_CHAT_REPLIES,
                body=queue_message,
            )
            return
        except Exception as e:
            logging.warning(f"{type(e)}: {e}")

        sleep(5)
        user_chat_reply_queue = connect_and_create_queue(
            RABBITMQ_QUEUE_USER_CHAT_REPLIES
        )


def on_message(ch, method, properties, body) -> None:
    logging.info(
        f"Message received: ch: {ch}, method: {method}, properties: {properties}, body: {body}"
    )
    queue_message = json.loads(body.decode("utf8"))

    collection_query_result = query_collection(queue_message["text"])
    logging.info(f"Collection query result: {collection_query_result}")

    prompt = f"{queue_message["text"]}. In your answer, use the following information if it is related: {collection_query_result}"

    llm_response = llm.chat(prompt)
    logging.info(f"LLM replied: {llm_response}")

    publish_reliably(
        queue_message_and_llm_response_to_reply(queue_message, llm_response)
    )


while True:
    try:
        user_chat_queue.basic_consume(
            queue=RABBITMQ_QUEUE_USER_CHATS,
            auto_ack=True,
            on_message_callback=on_message,
        )
        user_chat_queue.start_consuming()
    except Exception as e:
        logging.warning(
            "reconnecting {}: {}: {}".format(
                RABBITMQ_QUEUE_USER_CHATS, type(e), e
            )
        )
        sleep(5)
        user_chat_queue = connect_and_create_queue(RABBITMQ_QUEUE_USER_CHATS)
