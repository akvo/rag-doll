import os
import io
import time
import zipfile
import sqlite3
import requests
import chromadb
from tempfile import TemporaryDirectory
from typing import List, Tuple, Optional

import logging
logging.basicConfig(level=logging.INFO)

EPPO_SQLITE_DATABASE_ZIP = os.getenv('EPPO_SQLITE_DATABASE_ZIP')
EPPO_COUNTRIES = os.getenv('EPPO_COUNTRIES').replace(' ', '').split(',')

# Here we define the granularity of the chunks, as well as overlap and metadata.
# Our data sets are tiny, so just a few sentences will have to do. Based on gut
# feel, we start with 5 sentences per chunk, with one sentence overlap. We will
# have to fine tune that over time. We simply use all other columns as metadata.

CHUNK_SIZE=5 # XXX move to .env
OVERLAP_SIZE=1

CHROMADB_HOST = os.getenv('CHROMADB_HOST')
CHROMADB_PORT = os.getenv('CHROMADB_PORT')
CHROMADB_COLLECTION = os.getenv('CHROMADB_COLLECTION')


# The EPPO codes registry is available asa zipped SQLite 3 database. Download
# that ZIP file, but keep it in memory. We don't need persistence since we want
# to use the latest version every time.

def download_zip_to_memory(url: str) -> io.BytesIO:
    """Download a ZIP file from a URL and keep it in memory."""
    response = requests.get(url)
    response.raise_for_status()
    return io.BytesIO(response.content)



# Find the actual database file in the ZIP archive and extract that. Here we
# store it as a temporary file, because SQLite expects an actual database file.

def extract_sqlite_and_connect(zip_bytes: io.BytesIO) -> sqlite3.Connection:
    with TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_bytes) as zip_ref:
            for file in zip_ref.namelist():
                if file.endswith('.sqlite'):
                    zip_ref.extract(file, tmpdir)
                    db_path = os.path.join(tmpdir, file)
                    return sqlite3.connect(db_path)
        raise FileNotFoundError("SQLite database file not found in the ZIP archive")


# Filter the full list of country codes down to the ones that are interesting to our users.

def fetch_eppocode_relevant_to_countries(eppo_db: sqlite3.Connection, country_codes: List[str]) -> List[Tuple[str, str]]:
    countries = "', '".join(country_codes)
    query = f"""
        SELECT tc.eppocode, tn.isocountry
        FROM t_codes tc
        JOIN t_names tn ON tc.codeid = tn.codeid
        WHERE tc.dtcode IN ('GAF', 'GAI', 'PFL')
          AND tn.isocountry IN ('{countries}');
    """ # XXX this query is not correct
    cursor = eppo_db.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    return results


# Connect to ChromaDB. ChromaDB takes a second or so to start, so we have a
# crude retry loop. Once connected. we clear the collection and recreate it from
# the Apache Parquet file provided.

chromadb_client = None
knowledgebase_id = 0

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
        logging.warn(f"unable to connect to http://{CHROMADB_HOST}:{CHROMADB_PORT}, retrying...: {e}")
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


zip_bytes = download_zip_to_memory(EPPO_SQLITE_DATABASE_ZIP)
logging.info(f"Downloaded {len(zip_bytes.getvalue())} bytes from {EPPO_SQLITE_DATABASE_ZIP}")

eppo_db = extract_sqlite_and_connect(zip_bytes)
eppocodes = fetch_eppocode_relevant_to_countries(eppo_db, EPPO_COUNTRIES)
logging.info(f"Found {len(eppocodes)} EPPO codes relevant to {EPPO_COUNTRIES}")

for code in eppocodes:
    logging.info(code)



# And with that, the librarian is done. The searchable text has been updated and
# is ready to be queried.

