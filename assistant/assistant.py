import os
import json
import asyncio
import logging
import chromadb
from time import sleep
from openai import OpenAI
from Akvo_rabbitmq_client import rabbitmq_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
CHROMADB_DISTANCE_CUTOFF: float = float(os.getenv("CHROMADB_DISTANCE_CUTOFF"))

def connect_to_chromadb(host: str, port: int, collection_name: str) -> chromadb.Collection:
    '''
        Connect to ChromaDB. The ChromaDB service takes a second or so to start,
        so we have a crude retry loop. Once connected, we look up or create the
        collection.
    '''
    chromadb_client = None
    while chromadb_client == None:
        try:
            logger.info(f"trying http://{host}:{port}/{collection_name}...")
            chromadb_client = chromadb.HttpClient(host=host, port=port, settings=chromadb.Settings(anonymized_telemetry=False))
            return chromadb_client.get_or_create_collection(collection_name)
        except Exception as e:
            logger.warning(f"unable to connect to http://{host}:{port}/{collection_name}, retrying...: {type(e)}: {e}")
            chromadb_client = None
            sleep(1)


def query_collection(collection: chromadb.Collection, prompt: str) -> list[str]:
    logger.info(f"    -> will query: {collection} for {prompt}, with cut-off {CHROMADB_DISTANCE_CUTOFF}")

    query_result = collection.query(
        query_texts=[prompt],
        n_results=5,
        include=["documents", "distances"]
    )
    filtered_documents = [
        doc for doc, dist in zip(query_result["documents"][0], query_result["distances"][0])
        if dist < CHROMADB_DISTANCE_CUTOFF
    ]

    logger.info(f"    -> accepted {len(filtered_documents)} of {len(query_result["documents"][0])} query results: distances: {query_result["distances"][0]}, cut-off: {CHROMADB_DISTANCE_CUTOFF}")
    return filtered_documents


chromadb_collection = connect_to_chromadb(CHROMADB_HOST, CHROMADB_PORT, CHROMADB_COLLECTION)

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
        logger.info(f"OPENAI RESPONSE: {response}")
        message = response.choices[0].message
        self.append_message(message.role, message.content)
        return message.content

    def append_message(self, role, content):
        self.messages.append({MSG_ROLE: role, MSG_CONTENT: str(content)})


llm = LLM(os.getenv("OPENAI_CHAT_MODEL"))


# --- RabbitMQ Section

RABBITMQ_QUEUE_USER_CHATS = os.getenv("RABBITMQ_QUEUE_USER_CHATS")
RABBITMQ_QUEUE_USER_CHAT_REPLIES = os.getenv("RABBITMQ_QUEUE_USER_CHAT_REPLIES")


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
            logger.warning(f"{type(e)}: {e}")

        sleep(5)
        user_chat_reply_queue = connect_and_create_queue(
            RABBITMQ_QUEUE_USER_CHAT_REPLIES
        )


async def on_message(body: str) -> None:
    from_client = json.loads(body)
    logger.info(f"    -> parsed JSON: {from_client}")

    collection_query_result = query_collection(chromadb_collection, from_client["body"])
    logger.info(f"Collection query result: {collection_query_result}")

    prompt = f"{from_client['body']}. In your answer, use the following information if it is related: {collection_query_result}"

    llm_response = llm.chat(prompt)
    logger.info(f"LLM replied: {llm_response}")

    publish_reliably(
        queue_message_and_llm_response_to_reply(from_client, llm_response)
    )


async def main():
    await rabbitmq_client.initialize()

    await rabbitmq_client.consume(
        queue_name=RABBITMQ_QUEUE_USER_CHATS,
        routing_key=RABBITMQ_QUEUE_USER_CHATS,
        callback=on_message,
    )

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await rabbitmq_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())

