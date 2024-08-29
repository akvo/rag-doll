import os
import json
import asyncio
import logging
import chromadb
from time import sleep
from openai import OpenAI
from Akvo_rabbitmq_client import rabbitmq_client
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


CHROMADB_COLLECTION: str = os.getenv("CHROMADB_COLLECTION") # XXX

# ChromaDB section

CHROMADB_HOST: str = os.getenv("CHROMADB_HOST")
CHROMADB_PORT: int = os.getenv("CHROMADB_PORT")
CHROMADB_DISTANCE_CUTOFF: float = float(os.getenv("CHROMADB_DISTANCE_CUTOFF"))

CHROMADB_COLLECTION_TEMPLATE: str = os.getenv('CHROMADB_COLLECTION_TEMPLATE')
ASSISTANT_LANGUAGES: list[str] = os.getenv('ASSISTANT_LANGUAGES').replace(' ', '').split(',')

# XXX dictionary of prompts and chroma collections, indexed by language

def connect_to_chromadb(
    host: str, port: int, collection_name: str
) -> chromadb.Collection:
    """
    Connect to ChromaDB. The ChromaDB service takes a
    second or so to start, so we have a crude retry loop.
    Once connected, we look up or create the collection.
    """
    chromadb_client = None
    while chromadb_client is None:
        url = f"http://{host}:{port}/{collection_name}"
        try:
            logger.info(f"trying {url}...")
            chromadb_client = chromadb.HttpClient(
                host=host,
                port=port,
                settings=chromadb.Settings(anonymized_telemetry=False),
            )
            return chromadb_client.get_or_create_collection(collection_name)
        except Exception as e:
            logger.warning(
                f"unable to connect to {url}, retrying...: {type(e)}: {e}"
            )
            chromadb_client = None
            sleep(1)


def query_collection(collection: chromadb.Collection, prompt: str, cutoff: float = None) -> tuple[list[str], list[float]]:
    """
    Queries the collection with the provided prompt and returns documents and
    their corresponding distances if they have a lower distance than on the
    cutoff value. The idea is that the cutoff value helps suppress irrelevant
    documents.

    Parameters:
    collection (chromadb.Collection): The collection to query.
    prompt (str): The prompt to query with.
    cutoff (int, optional): The distance cutoff for filtering documents. 
                            If `None`, the default, all documents are returned.
    
    Returns:
    tuple[list[str], list[float]]: A tuple containing a list of filtered documents 
                                   and a list of their corresponding distances.
    """
    logger.info(
        f"[ASSISTANT] -> will query: {collection} for '{prompt}'"
        f" with cut-off {cutoff}"
    )

    query_result = collection.query(
        query_texts=[prompt], n_results=5, include=["documents", "distances", "uris", "metadatas"]
    )

    if cutoff is not None:
        filtered_documents = [
            doc for doc, dist in zip(query_result["documents"][0], query_result["distances"][0]) if dist < cutoff
        ]
        filtered_distances = [
            dist for dist in query_result["distances"][0] if dist < cutoff
        ]
        filtered_uris = [
            uri for uri, dist in zip(query_result["uris"][0], query_result["distances"][0]) if dist < cutoff
        ]
        filtered_countries = [
            metadata["countries"] for metadata, dist in zip(query_result["metadatas"][0], query_result["distances"][0]) if dist < cutoff
        ]
    else:
        filtered_documents = query_result["documents"][0]
        filtered_distances = query_result["distances"][0]
        filtered_uris = query_result["uris"][0]
        filtered_countries = [metadata["countries"] for metadata in query_result["metadatas"][0]]

    logger.info(
        f"[ASSISTANT] -> accepted {len(filtered_documents)} of "
        f"{len(query_result['documents'][0])} query results: distances:"
        f"{query_result['distances'][0]}, cut-off: {cutoff}"
    )
    return filtered_documents, filtered_distances, filtered_uris, filtered_countries


chromadb_collection = connect_to_chromadb(
    CHROMADB_HOST, CHROMADB_PORT, CHROMADB_COLLECTION
)

# --- LLM section

ASSISTANT_ROLE = os.getenv("ASSISTANT_ROLE")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL")
RAG_PROMPT = os.getenv("RAG_PROMPT")
RAGLESS_PROMPT = os.getenv("RAGLESS_PROMPT")

class LLM:
    def __init__(self, chat_model: str):
        self.chat_model = chat_model
        self.llm_client = OpenAI()
        self.messages = []
        self.append_message("system", ASSISTANT_ROLE)

    def chat(self, content: str) -> dict:
        self.append_message("user", content)
        response = self.llm_client.chat.completions.create(
            model=self.chat_model, messages=self.messages
        )
        logger.info(f"[ASSISTANT] -> OPENAI RESPONSE: {response}")
        message = response.choices[0].message
        self.append_message(message.role, message.content)
        return {"message": message.content, "created_at": response.created}

    def append_message(self, role, content):
        self.messages.append({"role": role, "content": str(content)})


llm = LLM(OPENAI_CHAT_MODEL)


# --- RabbitMQ Section

RABBITMQ_QUEUE_USER_CHATS = os.getenv("RABBITMQ_QUEUE_USER_CHATS")
RABBITMQ_QUEUE_USER_CHAT_REPLIES = os.getenv(
    "RABBITMQ_QUEUE_USER_CHAT_REPLIES"
)


def queue_message_and_llm_response_to_reply(
    queue_message: dict, llm_response: dict
) -> str:
    try:
        logger.info(f"[ASSISTANT] -> Formatting message: {queue_message}")
        conversation_envelope = queue_message.get("conversation_envelope", {})
        timestamp = float(llm_response["created_at"])
        iso_timestamp = datetime.fromtimestamp(
            timestamp, tz=timezone.utc
        ).isoformat()
        reply = {
            "conversation_envelope": {
                "message_id": conversation_envelope.get("message_id"),
                "client_phone_number": conversation_envelope.get(
                    "client_phone_number"
                ),
                "user_phone_number": conversation_envelope.get(
                    "user_phone_number"
                ),
                "sender_role": "assistant",
                "platform": conversation_envelope.get("platform"),
                "timestamp": iso_timestamp,
            },
            "body": llm_response["message"],
            "media": [],
            "context": [],
            "transformation_log": [llm_response["message"]],
        }
        logger.info(f"[ASSISTANT] -> Message ready: {reply}")
        return json.dumps(reply)

    except Exception as e:
        logger.error(f"[ASSISTANT] -> Error formatting message {type(e)}: {e}")


async def publish_reliably(queue_message: str) -> None:
    try:
        logger.info(f"[ASSISTANT] -> Sending message: {queue_message}")
        await rabbitmq_client.producer(
            body=queue_message,
            routing_key=RABBITMQ_QUEUE_USER_CHAT_REPLIES,
        )
    except Exception as e:
        logger.error(f"[ASSISTANT] -> Error send to queue {type(e)}: {e}")


async def on_message(body: str) -> None:
    logger.info(f"[ASSISTANT] -> message received: {body}")
    from_client = json.loads(body)

    # query the knowledge base for RAG context
    rag_context, _, _, _ = query_collection(
        chromadb_collection, from_client["body"],
        CHROMADB_DISTANCE_CUTOFF
    )

    # if there is context, add it to the prompt
    if len(rag_context) > 0:
        prompt = RAG_PROMPT.format(from_client["body"], rag_context)
    else:
        prompt = RAGLESS_PROMPT.format(from_client["body"])

    # then send that prompt over to the LLM
    llm_response = llm.chat(prompt)
    logger.info(f"[ASSISTANT] -> LLM replied: {llm_response}")
    reply_message = queue_message_and_llm_response_to_reply(
        queue_message=from_client, llm_response=llm_response
    )
    await publish_reliably(queue_message=reply_message)


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
        logger.info("[ASSISTANT] -> RabbitMQ Shutting down...")
        await rabbitmq_client.disconnect()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    asyncio.run(main())
