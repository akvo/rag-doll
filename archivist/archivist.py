import os
import time
import chromadb

import logging
logging.basicConfig(level=logging.INFO)

CHROMADB_HOST = os.getenv('CHROMADB_HOST')
CHROMADB_PORT = os.getenv('CHROMADB_PORT')
CHROMADB_COLLECTION = os.getenv('CHROMADB_COLLECTION')

# Connect to ChromaDB. ChromaDB takes a second or so to start, so we have a
# crude retry loop. Once connected. we clear the collection and recreate it from
# the Apache Parquet file provided.

chromadb_client = None

while chromadb_client == None:
    try:
        logging.info(f"trying http://{CHROMADB_HOST}:{CHROMADB_PORT}/{CHROMADB_COLLECTION}...")
        chromadb_client = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT)
        chat_history = chromadb_client.create_collection(name=CHROMADB_COLLECTION)
    except Exception as e:
        logging.warn(f"unable to connect to http://{CHROMADB_HOST}:{CHROMADB_PORT}, retrying...: {e}")
        chromadb_client = None
        time.sleep(1)


def add_message_to_chroma(id, text, medium, from, country, to, language, timestamp):
    chat_history.add(
        documents=[text],
        metadatas=[{COL_MEDOIUM: medium, COL_FROM: from, COL_COUNTRY: country, COL_TO: to, COL_LANGUAGE: language, COL_TIMESTAMP: timestamp}],
        ids=[f"{id}"]
    )


# --- --- filter unwanted: i.e. non-human messages ... Can we reconstruct a complete chat from the database? Does Chroma allow for basic queries or not? If not: where do we put the messages?

# --- --- decide: do we filter on Extension Officer answers only, or is that a
#         job for curators? What is the exact process of collecting, curating
#         and making searchable answers? For now, we err on the side of
#         simplicity: just put everything into the vector database.
# --- --- decide: how do we keep track of what chunks in the vector database
#         have been used / up/downvoted after retrieval?
# --- --- decide: how do we deal with privacy? We are handling messages that are
#         perceived as private.

# --- --- assemble key: reuse message key or just do uuid or incrementing

# --- --- assemble metadata:
#             medium (whatsapp/Slack/SMS/USSD).
#             from channel / from user / from phone
#             country of origin ISO 3166
#             to channel / to user / to phone
#             detected language ISO 3166 (or LOCALE-style?)
#             UTC timestamp

# --- --- put record into vector database

#    add_message_to_chroma(id, text, medium, from, country, to, language, timestamp)


