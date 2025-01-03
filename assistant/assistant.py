import os
import json
import asyncio
import logging
import chromadb
import nltk
import threading

from time import sleep
from openai import OpenAI

from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
from datetime import datetime, timezone
from Akvo_rabbitmq_client import rabbitmq_client
from typing import Optional
from db import connect_to_sqlite, get_stable_prompt
from nltk.corpus import words, stopwords
from health_check_handler import run


logger = logging.getLogger(__name__)

# Ensure reproducibility
DetectorFactory.seed = 0

# Ensure the NLTK resources are downloaded
nltk.download("punkt_tab")
nltk.download("words")
nltk.download("stopwords")

# Get English stopwords and the set of English words
english_stopwords = set(stopwords.words("english"))
english_words = set(w.lower() for w in words.words())

openai = OpenAI()

CHROMADB_HOST: str = os.getenv("CHROMADB_HOST")
CHROMADB_PORT: int = os.getenv("CHROMADB_PORT")
CHROMADB_DISTANCE_CUTOFF: float = float(os.getenv("CHROMADB_DISTANCE_CUTOFF"))

ASSISTANT_PORT = os.getenv("ASSISTANT_PORT")
ASSISTANT_LANGUAGES: list[str] = (
    os.getenv("ASSISTANT_LANGUAGES").replace(" ", "").split(",")
)
assert ASSISTANT_LANGUAGES is not None
assert len(ASSISTANT_LANGUAGES) > 0
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL")
assert OPENAI_CHAT_MODEL is not None
assert isinstance(OPENAI_CHAT_MODEL, str)
assert len(OPENAI_CHAT_MODEL) > 0
CHROMADB_COLLECTION_TEMPLATE: str = os.getenv("CHROMADB_COLLECTION_TEMPLATE")
assert CHROMADB_COLLECTION_TEMPLATE is not None
assert isinstance(CHROMADB_COLLECTION_TEMPLATE, str)
assert len(CHROMADB_COLLECTION_TEMPLATE) > 0

RABBITMQ_QUEUE_USER_CHATS = os.getenv("RABBITMQ_QUEUE_USER_CHATS")
RABBITMQ_QUEUE_USER_CHAT_REPLIES = os.getenv(
    "RABBITMQ_QUEUE_USER_CHAT_REPLIES"
)


# the collection of knowledge base connections and prompts,
# indexed by question language.
assistant_data = {}


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


def query_collection(
    collection: chromadb.Collection, prompt: str, cutoff: float = None
) -> tuple[list[str], list[float]]:
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
    tuple[list[str], list[float]]: A tuple containing a list of filtered
    documents and a list of their corresponding distances.
    """
    logger.info(
        f"[ASSISTANT] -> will query: {collection} for '{prompt}'"
        f" with cut-off {cutoff}"
    )

    query_result = collection.query(
        query_texts=[prompt],
        n_results=5,
        include=["documents", "distances", "uris", "metadatas"],
    )

    if cutoff is not None:
        filtered_documents = [
            doc
            for doc, dist in zip(
                query_result["documents"][0], query_result["distances"][0]
            )
            if dist < cutoff
        ]
        filtered_distances = [
            dist for dist in query_result["distances"][0] if dist < cutoff
        ]
        filtered_uris = [
            uri
            for uri, dist in zip(
                query_result["uris"][0], query_result["distances"][0]
            )
            if dist < cutoff
        ]
        filtered_countries = [
            metadata["countries"]
            for metadata, dist in zip(
                query_result["metadatas"][0], query_result["distances"][0]
            )
            if dist < cutoff
        ]
    else:
        filtered_documents = query_result["documents"][0]
        filtered_distances = query_result["distances"][0]
        filtered_uris = query_result["uris"][0]
        filtered_countries = [
            metadata["countries"] for metadata in query_result["metadatas"][0]
        ]

    logger.info(
        f"[ASSISTANT] -> accepted {len(filtered_documents)} of "
        f"{len(query_result['documents'][0])} query results: distances:"
        f"{query_result['distances'][0]}, cut-off: {cutoff}"
    )
    return (
        filtered_documents,
        filtered_distances,
        filtered_uris,
        filtered_countries,
    )


def query_llm(
    llm_client: OpenAI,
    model: str,
    system_prompt: str,
    ragless_prompt_template: str,
    rag_prompt_template: str,
    context: list[str],
    prompt: str,
    history: Optional[list[dict]] = [],
) -> tuple[str, datetime]:
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
        final_prompt = rag_prompt_template.format(
            prompt=prompt, context="\n".join(context)
        )
    else:
        final_prompt = ragless_prompt_template.format(prompt=prompt)
    logger.info(f"[ASSISTANT] -> final prompt: {final_prompt}")

    llm_messages = [
        {"role": "system", "content": system_prompt},
    ]
    if history:
        llm_messages.extend(history)
    llm_messages.append({"role": "user", "content": final_prompt})

    logger.info(f"[ASSISTANT] -> query_llm with messages: {llm_messages}")

    response = llm_client.chat.completions.create(
        model=model,
        messages=llm_messages,
    )
    iso_timestamp = datetime.fromtimestamp(
        int(response.created), tz=timezone.utc
    )
    return response.choices[0].message.content.strip(), iso_timestamp


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


def get_language(user_prompt) -> str:
    try:
        # Use langdetect to get an initial guess
        detected_language = detect(user_prompt)
    except LangDetectException:
        return "en"

    # Double check with nltk library
    if detected_language == "fr":
        # Tokenize the text to get individual words
        tokens = nltk.word_tokenize(user_prompt.lower())

        # Count the number of English stopwords and valid English words
        stopwords_count = sum(word in english_stopwords for word in tokens)
        valid_word_count = sum(word in english_words for word in tokens)

        # Heuristic: check English stopwords or words, reconsider
        if (
            stopwords_count > len(tokens) / 2
            or valid_word_count > len(tokens) / 2
        ):
            detected_language = "en"

    # check if detected language supported in env settings
    if detected_language not in assistant_data:
        logger.warning(
            f"[ASSISTANT] -> Unsupported lang detected: {detected_language}"
            f" for '{user_prompt}', defaulting to English"
        )
        return "en"
    return detected_language


async def on_message(body: str) -> None:
    """
    Handles incoming messages, detects the language, and processes the message
    using the appropriate knowledge base and prompts.

    Parameters:
    body (str): The incoming message in JSON format.
    """
    logger.info(f"[ASSISTANT] -> message received: {body}")
    from_client = json.loads(body)

    # Handle ignore media message
    media = from_client.get("media")
    if media:
        logger.info("[ASSISTANT] -> skipping whisper because of media message")
        return None
    # EOL handle ignore media message

    history = from_client.get("history", [])
    user_prompt = from_client["body"]

    detected_language = get_language(user_prompt)
    logger.info(f"[ASSISTANT] -> user prompt: {user_prompt}")
    logger.info(f"[ASSISTANT] -> detected lang: {detected_language}")
    logger.info(
        f"[ASSISTANT] -> assistant_data: {assistant_data[detected_language]}"
    )

    knowledge_base = assistant_data[detected_language]["knowledge_base"]
    system_prompt = assistant_data[detected_language]["system_prompt"]
    rag_prompt = assistant_data[detected_language]["rag_prompt"]
    ragless_prompt = assistant_data[detected_language]["ragless_prompt"]

    # Query the knowledge base for RAG context
    rag_context, _, _, _ = query_collection(
        knowledge_base, from_client["body"], CHROMADB_DISTANCE_CUTOFF
    )

    # Send the user's prompt and context to the LLM
    llm_response, timestamp = query_llm(
        openai,
        OPENAI_CHAT_MODEL,
        system_prompt,
        ragless_prompt,
        rag_prompt,
        rag_context,
        user_prompt,
        history,
    )
    logger.info(f"[ASSISTANT] -> LLM replied: {llm_response}")

    # finally post the reply onto the message queue
    reply_message = queue_message_and_llm_response_to_reply(
        queue_message=from_client,
        llm_response=llm_response,
        timestamp=timestamp,
    )
    await publish_reliably(queue_message=reply_message)


def main():
    # Connect to all knowledge bases and store the language-specific connections
    # and prompts in the assistant data dictionary.
    sqlite_conn = connect_to_sqlite()
    assert sqlite_conn is not None

    for language in ASSISTANT_LANGUAGES:
        collection_name = CHROMADB_COLLECTION_TEMPLATE.format(language)
        knowledge_base = connect_to_chromadb(
            CHROMADB_HOST, CHROMADB_PORT, collection_name
        )

        prompt = get_stable_prompt(
            conn=sqlite_conn,
            language=language,
        )
        assert prompt is not None

        system_prompt = prompt["system_prompt"]
        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 0

        rag_prompt = prompt["rag_prompt"]
        assert isinstance(rag_prompt, str)
        assert len(rag_prompt) > 0

        ragless_prompt = prompt["ragless_prompt"]
        assert isinstance(ragless_prompt, str)
        assert len(ragless_prompt) > 0

        assistant_data[language] = {
            "knowledge_base": knowledge_base,
            "system_prompt": system_prompt,
            "rag_prompt": rag_prompt,
            "ragless_prompt": ragless_prompt,
        }
    sqlite_conn.close()


async def consumer():
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
    main()

    # Start the HTTP server in a separate thread
    server_thread = threading.Thread(
        target=run, kwargs={"port": int(ASSISTANT_PORT)}
    )
    server_thread.start()

    asyncio.run(consumer())
