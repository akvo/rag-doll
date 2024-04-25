import os
import time
import chromadb
import pandas as pd
ROW=1

CORPUS_PARQUET_GZ="/data-sets/corpus.parquet.gz"

COL_FILENAME = 'file name'
COL_TEXT_AS_WRITTEN = 'text as written'
COL_LANGUAGE = 'language'
COL_LEMMATISED_TEXT = 'lemmatised text'
COL_COUNT_TEXT = 'written word count'
COL_COUNT_LEMMATISED = 'lemmatised word count'

COL_COUNTRY = 'country (ISO-3166)'
ISO_3166_KENYA = 'KEN'
ISO_3166_BURKINA_FASO = 'BFA'

# Here we define the granularity of the chunks, as well as overlap and metadata.
# Our data sets are tiny, so just a few sentences will have to do. Based on gut
# feel, we start with 5 sentences per chunk, with one sentence overlap. We will
# have to fine tune that over time. We simply use all other columns as metadata.

CHUNK_SIZE=5
OVERLAP_SIZE=1

CHROMADB_HOST = os.getenv('CHROMADB_HOST')
CHROMADB_PORT = os.getenv('CHROMADB_PORT')
CHROMADB_COLLECTION = os.getenv('CHROMADB_COLLECTION')

# Connect to ChromaDB. ChromaDB takes a second or so to start, so we have a
# crude retry loop. Once connected. we clear the collection and recreate it from
# the Apache Parquet file provided.

chromadb_client = None
knowledgebase_id = 0

while chromadb_client == None:
    try:
        print(f"trying http://{CHROMADB_HOST}:{CHROMADB_PORT}/{CHROMADB_COLLECTION}...")
        chromadb_client = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT)
        collections = chromadb_client.list_collections()
        for coll in collections:
            if CHROMADB_COLLECTION == coll.name:
                chromadb_client.delete_collection(CHROMADB_COLLECTION)
        knowledgebase = chromadb_client.create_collection(name=CHROMADB_COLLECTION)
    except Exception as e:
        print(f"unable to connect to http://{CHROMADB_HOST}:{CHROMADB_PORT}, retrying...: {e}")
        chromadb_client = None
        time.sleep(1)

def add_chunk_to_chroma(chunk, country):
    global knowledgebase_id

    print(f"=== country: {country}, length: {len(chunk)}, id: {knowledgebase_id} ==================")
    # print('.'.join(chunk))
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


corpus = pd.read_parquet(CORPUS_PARQUET_GZ)
print(corpus.info())

corpus.apply(build_chunks_from_sentences, axis=ROW)

# And with that, the librarian is done. The searchable text has been updated and
# is ready to be queried.

