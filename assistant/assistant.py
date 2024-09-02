import os
import json
import asyncio
import logging
import chromadb
from time import sleep
from openai import OpenAI
from datetime import datetime, timezone
from Akvo_rabbitmq_client import rabbitmq_client

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


def query_llm(llm_client: OpenAI, model: str,
    system_prompt: str,
    ragless_prompt_template: str,
    rag_prompt_template: str, context: list[str],
    prompt: str) -> tuple[str, datetime]:
    """
    Queries the LLM with the given model and prompts, building the final prompt
    from the user's prompt and the knowledge base context. Depending on the
    value of `CHROMADB_DISTANCE_CUTOFF` the number of context chunks may be
    higher or lower. If no context was deemed relevant, we use the simpler
    RAGless prompt. Returns the first answer from the LLM.

    Parameters:
    llm_client (OpenAI): The LLM client to call.
    model (str): The name of the model to use.
    system_prompt (str): The system prompt for the LLM.
    ragless_prompt_template (str): The template for the prompt _without_
                                   RAG context.
    rag_prompt_template (str): The template for the prompt _with_ RAG context.
    context (list[str]): The list of knowledge base chunks to include in the
                         RAG prompt.
    prompt (str): The user's prompt.

    Returns:
    str: The LLM response.
    """
    if context:
        final_prompt = rag_prompt_template.format(prompt=prompt, context="\n".join(context))
    else:
        final_prompt = ragless_prompt_template.format(prompt=prompt)
    logger.info(f"[ASSISTANT] -> final prompt: {final_prompt}")

    response = llm_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": final_prompt}
        ]
    )
    iso_timestamp = datetime.fromtimestamp(
        int(response.created), tz=timezone.utc
    )
    return response.choices[0].message.content.strip(), iso_timestamp

openai = OpenAI()

# --- RabbitMQ Section

RABBITMQ_QUEUE_USER_CHATS = os.getenv("RABBITMQ_QUEUE_USER_CHATS")
RABBITMQ_QUEUE_USER_CHAT_REPLIES = os.getenv(
    "RABBITMQ_QUEUE_USER_CHAT_REPLIES"
)


def queue_message_and_llm_response_to_reply(
    queue_message: dict, llm_response: str, timestamp: datetime
) -> str:
    try:
        logger.info(f"[ASSISTANT] -> Formatting message: {queue_message}")
        conversation_envelope = queue_message.get("conversation_envelope", {})
        iso_timestamp = timestamp.isoformat()
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
            "body": llm_response,
            "media": [],
            "context": [],
            "transformation_log": [llm_response],
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

    # send the user's prompt and context to the LLM
    llm_response, timestamp = query_llm(
            openai, OPENAI_CHAT_MODEL,
            ASSISTANT_ROLE,
            RAGLESS_PROMPT,
            RAG_PROMPT, rag_context,
            from_client["body"],
        )
    logger.info(f"[ASSISTANT] -> LLM replied: {llm_response}")

    # finally post the reply onto the message queue
    reply_message = queue_message_and_llm_response_to_reply(
        queue_message=from_client,
        llm_response=llm_response, timestamp=timestamp
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
