import os
import io
import time
import requests
import chromadb
import pandas as pd

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


EPPO_COUNTRY_ORGANISM_URL: str = os.getenv('EPPO_COUNTRY_ORGANISM_URL')
EPPO_COUNTRIES: list[str] = os.getenv('EPPO_COUNTRIES').replace(' ', '').split(',')

# Here we define the granularity of the chunks, as well as overlap and metadata.
# Our data sets are tiny, so just a few sentences will have to do. Based on gut
# feel, we start with 5 sentences per chunk, with one sentence overlap. We will
# have to fine tune that over time. We simply use all other columns as metadata.

CHUNK_SIZE=5 # XXX move to .env
OVERLAP_SIZE: int = 1

CHROMADB_HOST: str = os.getenv('CHROMADB_HOST')
CHROMADB_PORT: int = os.getenv('CHROMADB_PORT')
CHROMADB_COLLECTION: str = os.getenv('CHROMADB_COLLECTION')


COL_EPPO_CODE: str = 'EPPOCode'
COL_COUNTRY: str = 'ISO 3166-1 2-character country code'


# Download the list of EPPO codes relevant to each country and merge the data
# sets into a single set where we have the list of countries for each EPPO code.

def download_eppo_code_registry(url: str, countries: list[str]) -> pd.DataFrame:
    merged_df: pd.DataFrame = None
    for country in countries:
        country_df = download_country_organisms(url, country)
        if merged_df is None:
            merged_df = country_df
        else:
            merged_df = pd.concat([merged_df, country_df], ignore_index=True)

    return merged_df.groupby(COL_EPPO_CODE).agg({
        COL_EPPO_CODE: 'first',
        COL_COUNTRY: lambda x: ', '.join(x.unique())
    }).reset_index(drop=True)


# Download the EPPO code list for a given country.

def download_country_organisms(url: str, country: str) -> pd.DataFrame:
    request_url = url.format(country=country)
    response = requests.get(request_url)
    response.raise_for_status()
    csv_content = io.StringIO(response.content.decode('utf-8'))

    df: pd.DataFrame = pd.read_csv(csv_content)
    df[COL_COUNTRY] = country

    logger.info(f"found {len(df)} EPPO codes for {request_url}")
    return df[[COL_EPPO_CODE, COL_COUNTRY]]


# Connect to ChromaDB. ChromaDB takes a second or so to start, so we have a
# crude retry loop. Once connected. we clear the collection and recreate it from
# the Apache Parquet file provided.

chromadb_client = None
knowledgebase_id: int = 0

while chromadb_client == None:
    try:
        logging.info(f"trying http://{CHROMADB_HOST}:{CHROMADB_PORT}/{CHROMADB_COLLECTION}...")
        chromadb_client = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT, settings=chromadb.Settings(anonymized_telemetry=False))
        collections = chromadb_client.list_collections()
        for coll in collections:
            if CHROMADB_COLLECTION == coll.name:
                chromadb_client.delete_collection(CHROMADB_COLLECTION)
        knowledgebase = chromadb_client.create_collection(name=CHROMADB_COLLECTION)
    except Exception as e:
        logging.warn(f"unable to connect to http://{CHROMADB_HOST}:{CHROMADB_PORT}, retrying...: {type(e)}: {e}")
        chromadb_client = None
        time.sleep(1)

def add_chunk_to_chroma(chunk, country):
    global knowledgebase_id

    logging.info(f"=== country: {country}, length: {len(chunk)}, id: {knowledgebase_id} ==================")
    # logging.info('.'.join(chunk))
    knowledgebase.add(
        documents=['.'.join(chunk)],
        metadatas=[{COL_COUNTRY: country}],
        ids=[f"{knowledgebase_id}"]
    )
    knowledgebase_id = knowledgebase_id + 1


def build_chunks_from_sentences(row):
    this_chunk = []
    next_chunk = []
    for sentence in row[COL_TEXT_AS_WRITTEN].split('.'):
        if len(this_chunk) >= CHUNK_SIZE:
            # done with the first chunk, add to overlap?
            if len(next_chunk) == OVERLAP_SIZE:
                # overlap was full, so push this chunk into the database
                add_chunk_to_chroma(this_chunk, row[COL_COUNTRY])
                this_chunk = next_chunk
                next_chunk = []
            else:
                # this chunk is full, but we still need more overlap
                this_chunk.append(sentence)
                next_chunk.append(sentence)
        else:
            # not enough in this chunk just yet
            this_chunk.append(sentence)

    if len(this_chunk) > 0:
        add_chunk_to_chroma(this_chunk, row[COL_COUNTRY])
    if len(next_chunk) > 0:
        add_chunk_to_chroma(next_chunk, row[COL_COUNTRY])


eppo_code_df = download_eppo_code_registry(EPPO_COUNTRY_ORGANISM_URL, EPPO_COUNTRIES)
logger.info(eppo_code_df.info())
logger.info(eppo_code_df)

# And with that, the librarian is done. The searchable text has been updated and
# is ready to be queried.

