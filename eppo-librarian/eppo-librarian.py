import os
import io
import time
import nltk
import requests
import chromadb
import pandas as pd
from lxml import html
from lxml.html import HtmlElement
from nltk.tokenize import sent_tokenize

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


EPPO_COUNTRY_ORGANISM_URL: str = os.getenv('EPPO_COUNTRY_ORGANISM_URL')
EPPO_DATASHEET_URL: str = os.getenv('EPPO_DATASHEET_URL')
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


def download_eppo_code_registry(url: str, countries: list[str]) -> pd.DataFrame:
    '''
        Download the list of EPPO codes relevant to each country and merge the
        data sets into a single set where we have the list of countries for each
        EPPO code. We use the web site "explore-by" -> "country" endpoint to
        find the organisms relevant to the given countries.
    '''
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


def download_country_organisms(url: str, country: str) -> pd.DataFrame:
    request_url = url.format(country=country)
    response = requests.get(request_url)
    response.raise_for_status()
    csv_content = io.StringIO(response.content.decode('utf-8'))

    df: pd.DataFrame = pd.read_csv(csv_content)
    df[COL_COUNTRY] = country

    logger.info(f"found {len(df)} EPPO codes for {request_url}")
    return df[[COL_EPPO_CODE, COL_COUNTRY]]


def download_datasheet_as_html(eppo_code: str) -> HtmlElement:
    '''
        Download the datasheet for a given organism. The format of these data
        sheets is quite strict, which we use to our advantage.
    '''
    url = EPPO_DATASHEET_URL.format(eppo_code=eppo_code)
    logger.info(f"downloading datasheet for {eppo_code} from {url}")
    response = requests.get(url)
    response.raise_for_status()
    return html.fromstring(response.content)
    

def clean_datasheet(tree: HtmlElement) -> HtmlElement:
    '''
        The HTML tree comes with a bunch of navigation and styling that we do
        not want in the knowledge base. This function prunes such useless
        elements from the tree, as well as comments.
    '''
    for xpath in ['//head', '//header', '//footer', '//script', '//noscript', '//style', '//div[contains(@class, "quicksearch")]', '//div[contains(@class, "navbar")]', '//div[contains(@class, "btn")]', '//div[contains(@class, "modal")]']:
        elements = tree.xpath(xpath)
        for element in elements:
            element.getparent().remove(element)

    comments = tree.xpath('//comment()')
    for comment in comments:
        comment.getparent().remove(comment)

    return tree


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
            collections = chromadb_client.list_collections()
            for coll in collections:
                if CHROMADB_COLLECTION == coll.name:
                    chromadb_client.delete_collection(CHROMADB_COLLECTION)
            return chromadb_client.create_collection(name=CHROMADB_COLLECTION)
        except Exception as e:
            logger.warn(f"unable to connect to http://{CHROMADB_HOST}:{CHROMADB_PORT}, retrying...: {type(e)}: {e}")
            chromadb_client = None
            time.sleep(1)


def add_chunk_to_chroma(knowledgebase: chromadb.Collection, chunk: str, id: str, country: str):
    logger.info(f"=== country: {country}, length: {len(chunk)}, id: {id} ==================")
    # logger.info('.'.join(chunk))
    knowledgebase.add(
        documents=['. '.join(chunk)],
        metadatas=[{'country': country}],
        ids=[id]
    )


def build_chunks_from_sentences(knowledgebase: chromadb.Collection, text: str, eppo_code: str, country: str):
    '''
        Break the text up into chunks and push the chunks into ChromaDB.
        ChromaDB handles the vectorisation using its default embedding model.
        That is good enough to get started. We rooftile the chunks based on
        `CHUNK_SIZE` and `OVERLAP_SIZE`.

        Here we also construct the unique identifier for each chunk, using the
        EPPO code, the country and a numeric uniquefier.
    '''
    sentences:  list[str] = sent_tokenize(text)
    this_chunk: list[str] = []
    next_chunk: list[str] = []

    id = f"{eppo_code}/{country}"
    uniquefier: int = 0

    for sentence in sentences:
        if len(this_chunk) >= CHUNK_SIZE:
            # done with the first chunk, add to overlap?
            if len(next_chunk) == OVERLAP_SIZE:
                add_chunk_to_chroma(knowledgebase, this_chunk, f"{id}/{uniquefier}", country)
                uniquefier = uniquefier + 1
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
        add_chunk_to_chroma(knowledgebase, this_chunk, f"{id}/{uniquefier}", country)
        uniquefier = uniquefier + 1
    if len(next_chunk) > 0:
        add_chunk_to_chroma(knowledgebase, next_chunk, f"{id}/{uniquefier}", country)
        uniquefier = uniquefier + 1


# Download the NLTK sentence splitter
nltk.download('punkt')

eppo_code_df = download_eppo_code_registry(EPPO_COUNTRY_ORGANISM_URL, EPPO_COUNTRIES)
logger.info(eppo_code_df.info())
logger.info(eppo_code_df)

knowledgebase: chromadb.Collection = connect_to_chromadb()

for index, row in eppo_code_df.iterrows():
    eppo_code: str = row[COL_EPPO_CODE]
    countries: list[str] = row[COL_COUNTRY].split(', ')

    datasheet_html = download_datasheet_as_html(eppo_code)
    datasheet_html = clean_datasheet(datasheet_html)

    logger.info(html.tostring(datasheet_html, pretty_print=True).decode('utf-8'))

    datasheet_text = datasheet_html.xpath('//body//text()')
    datasheet_text = ' '.join(datasheet_text)

    logger.info(datasheet_text)

    for country in countries:
        build_chunks_from_sentences(knowledgebase, datasheet_text, eppo_code, country)


# And with that, the librarian is done. The searchable text has been updated and
# is ready to be queried.

