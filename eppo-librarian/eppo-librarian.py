import os
import io
import nltk
import time
import logging
import requests
import chromadb
import pandas as pd
from lxml import html
from time import sleep
from openai import OpenAI
from lxml.html import HtmlElement
from nltk.tokenize import sent_tokenize
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)


EPPO_COUNTRY_ORGANISM_URL: str = os.getenv('EPPO_COUNTRY_ORGANISM_URL')
assert not EPPO_COUNTRY_ORGANISM_URL is None
assert isinstance(EPPO_COUNTRY_ORGANISM_URL, str)
EPPO_DATASHEET_URL: str = os.getenv('EPPO_DATASHEET_URL')
assert not EPPO_DATASHEET_URL is None
assert isinstance(EPPO_DATASHEET_URL, str)
EPPO_COUNTRIES: list[str] = os.getenv('EPPO_COUNTRIES').replace(' ', '').split(',')
assert not EPPO_COUNTRIES is None
assert len(EPPO_COUNTRIES) > 0

# Here we define the granularity of the chunks, as well as overlap and metadata.
# Our data sets are tiny, so just a few sentences will have to do. Based on gut
# feel, we start with 5 sentences per chunk, with one sentence overlap. We will
# have to fine tune that over time. We simply use all other columns as metadata.

CHUNK_SIZE: int = int(os.getenv('CHUNK_SIZE'))
assert CHUNK_SIZE > 0
OVERLAP_SIZE: int = int(os.getenv('OVERLAP_SIZE'))
assert OVERLAP_SIZE > 0

CHROMADB_HOST: str = os.getenv('CHROMADB_HOST')
assert not CHROMADB_HOST is None
assert isinstance(CHROMADB_HOST, str)
CHROMADB_PORT: int = int(os.getenv('CHROMADB_PORT'))
assert not CHROMADB_PORT is None
assert isinstance(CHROMADB_PORT, int)

CHROMADB_COLLECTION_TEMPLATE: str = os.getenv('CHROMADB_COLLECTION_TEMPLATE')
assert not CHROMADB_COLLECTION_TEMPLATE is None
assert isinstance(CHROMADB_COLLECTION_TEMPLATE, str)
ASSISTANT_LANGUAGES: list[str] = os.getenv('ASSISTANT_LANGUAGES').replace(' ', '').split(',')
assert not ASSISTANT_LANGUAGES is None
assert len(ASSISTANT_LANGUAGES) > 0

OPENAI_CHAT_MODEL: str = os.getenv('OPENAI_CHAT_MODEL')
assert not OPENAI_CHAT_MODEL is None
assert isinstance(OPENAI_CHAT_MODEL, str)

PLAIN_TEXT_SYSTEM_PROMPT: str = os.getenv('PLAIN_TEXT_SYSTEM_PROMPT')
assert not PLAIN_TEXT_SYSTEM_PROMPT is None
assert isinstance(PLAIN_TEXT_SYSTEM_PROMPT, str)
PLAIN_TEXT_PROMPT: str = os.getenv('PLAIN_TEXT_PROMPT')
assert not PLAIN_TEXT_PROMPT is None
assert isinstance(PLAIN_TEXT_PROMPT, str)


COL_EPPO_CODE: str  = 'EPPOCode'
COL_COUNTRY: str    = 'country code (ISO 3166-1)'
COL_URL: str        = 'EPPO datasheet url'
COL_TEXT_EN: str    = 'datasheet (en)'
COL_TEXT_PLAIN: str = 'datasheet (plain en)'
COL_CHUNK: str      = 'chunk (en)'


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
    return url, html.fromstring(response.content)


def clean_datasheet(tree: HtmlElement) -> HtmlElement:
    '''
        The HTML tree comes with a bunch of navigation and styling that we do
        not want in the knowledge base. This function prunes such useless
        elements from the tree, as well as comments.
    '''
    for xpath in ['//head', '//header', '//footer', '//script', '//noscript', '//style', '//div[contains(@class, "quicksearch")]', '//div[contains(@class, "navbar")]', '//*[contains(@class, "btn")]', '//div[contains(@class, "modal")]', '//*[contains(@class, "hidden-print")]']:
        elements = tree.xpath(xpath)
        for element in elements:
            element.getparent().remove(element)

    comments = tree.xpath('//comment()')
    for comment in comments:
        comment.getparent().remove(comment)

    return tree


def download_datasheets(df: pd.DataFrame) -> pd.DataFrame:
    '''
        Download all datasheets specified, clean their text and provide the URL
        for the datasheet, for reference.
    '''

    def download_and_extract_text(row):
        eppo_code = row[COL_EPPO_CODE]
        datasheet_url, datasheet_html = download_datasheet_as_html(eppo_code)
        cleaned_html = clean_datasheet(datasheet_html)
        datasheet_text = ' '.join(cleaned_html.xpath('//body//text()'))
        datasheet_text = ' '.join(datasheet_text.split()) # weed out superfluous whitespace
        return pd.Series({
            COL_EPPO_CODE: eppo_code,
            COL_COUNTRY: row[COL_COUNTRY],
            COL_URL: datasheet_url,
            COL_TEXT_EN: datasheet_text,
        })

    return df.apply(download_and_extract_text, axis=1)


def translate_to_plain_text(df: pd.DataFrame,
                        llm_client: OpenAI, model: str,
                        system_prompt: str, prompt_template: str,
                        col_from: str, col_to: str) -> pd.DataFrame:

    def to_plain(llm_client: OpenAI, model: str, system_prompt: str, prompt_template: str, text: str) -> str:
        llm_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": prompt_template.format(text=text)}
        ]
        response = llm_client.chat.completions.create(
            model=model,
            messages=llm_messages,
        )
        return response.choices[0].message.content.strip()

    df[col_to] = df.apply(lambda row: to_plain(llm_client, model, system_prompt, prompt_template, row[col_from]), axis=1)
    return df


def make_chunks(df: pd.DataFrame, from_column: str, chunk_size: int, overlap_size: int, to_column: str) -> pd.DataFrame:
    """
    Splits the text into chunks of sentences using a roof tiling method. By
    splitting the datasheets into chunks we expect that the RAG queries
    will return more useful data.
    """
    def create_chunks(text: str) -> list[str]:
        sentences = sent_tokenize(text)
        chunks = []
        num_sentences = len(sentences)
        for start_idx in range(0, num_sentences, chunk_size - overlap_size):
            end_idx = min(start_idx + chunk_size, num_sentences)
            chunk = ' '.join(sentences[start_idx:end_idx])
            chunks.append(chunk)
            if end_idx == num_sentences:
                break
        return chunks

    all_chunks = []
    for index, row in df.iterrows():
        eppo_code = row[COL_EPPO_CODE]
        chunks = create_chunks(row[from_column])
        for chunk in chunks:
            all_chunks.append({COL_EPPO_CODE: eppo_code, to_column: chunk})

    return pd.DataFrame(all_chunks)


def connect_to_chromadb(host: str, port: int, collection_name: str, recreate_collection: bool = False) -> chromadb.Collection:
    '''
        Connect to ChromaDB. The ChromaDB service takes a second or so to start,
        so we have a crude retry loop. Once connected, we look up or create the
        collection.
    '''
    chromadb_client = None
    while chromadb_client == None:
        try:
            chromadb_client = chromadb.HttpClient(host=host, port=port, settings=chromadb.Settings(anonymized_telemetry=False))

            if recreate_collection:
                try:
                    chromadb_client.delete_collection(collection_name)
                    logger.info(f"deleted collection {collection_name}...")
                except Exception:
                    pass

            chromadb_collection = chromadb_client.get_or_create_collection(collection_name)
            logger.info(f"Connected to http://{host}:{port}/{chromadb_collection.name}, which has {chromadb_collection.count()} records.")
            return chromadb_collection
        except Exception as e:
            logger.warning(f"unable to connect to http://{host}:{port}/{collection_name}, retrying...: {type(e).__name__}: {e}")
            chromadb_client = None
            sleep(1)


def translate_chunks(df: pd.DataFrame, col_chunk: str, from_language: str, col_translated: str, to_language: str) -> pd.DataFrame:
    """
    Translates the text in the source column of the dataframe from one language
    to another and stores the result into `col_translated`.

    Parameters:
    df (pd.DataFrame): The DataFrame containing the text to translate.
    col_chunk (str): The column name with the text to translate.
    from_language (str): The source language code.
    col_translated (str): The column name where the translated text will be stored.
    to_language (str): The target language code.

    Returns:
    pd.DataFrame: The DataFrame with the translated text in the new column.
    """

    TRANSLATOR_CHAR_LIMIT: int = 4999
    translator = GoogleTranslator(source=from_language, target=to_language)

    def translate_with_retry(text: str) -> str:
        result = ''
        for i in range(0, len(text), TRANSLATOR_CHAR_LIMIT):
            chunk = text[i:i+TRANSLATOR_CHAR_LIMIT]
            while True:
                try:
                    result += translator.translate(chunk)
                    break
                except Exception as e:
                    logger.warning(f"Translation {type(e).__name__}: {str(e)}, retrying in 10 seconds...")
                    time.sleep(10)
        return result

    df[col_translated] = df[col_chunk].apply(translate_with_retry)
    return df


def add_chunks_to_chromadb(df: pd.DataFrame, metadata_df: pd.DataFrame, chunk_column: str, collection: chromadb.Collection) -> None:
    """
    Adds the chunks from the DataFrame to ChromaDB, associating metadata
    from the metadata DataFrame. Ensures unique keys by appending a uniquefier.

    Deletes existing entries for each EPPO code before adding new ones.
    Note: This may introduce a race condition where relevant data is deleted
    just before it could be queried.

    Parameters:
        df (pd.DataFrame): DataFrame containing the chunks and EPPO codes.
        metadata_df (pd.DataFrame): DataFrame containing metadata for each EPPO code.
        chunk_column (str): The column name in `df` that contains the chunks.
        collection (chromadb.Collection): The ChromaDB collection to which the chunks will be added.
    """

    for _, row in metadata_df.iterrows():
        eppo_code = row[COL_EPPO_CODE]
        datasheet_url = row[COL_URL]
        countries = row[COL_COUNTRY]

        eppo_chunks = df[df[COL_EPPO_CODE] == eppo_code][chunk_column].tolist()
        if len(eppo_chunks) > 0:
            collection.delete(where={"eppo_code": eppo_code})
            collection.add(
                ids=[f"{eppo_code}:{i}" for i in range(len(eppo_chunks))],
                uris=[datasheet_url]*len(eppo_chunks),
                metadatas=[{'countries': countries, 'eppo_code': eppo_code}]*len(eppo_chunks),
                documents=eppo_chunks,
            )
        else:
            logger.info(f"skipping {eppo_code}, no chunks. See also {datasheet_url}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # download the NLTK sentence splitter
    nltk.download('punkt_tab')

    logger.info("loading eppo codes...")
    eppo_code_df = download_eppo_code_registry(EPPO_COUNTRY_ORGANISM_URL, EPPO_COUNTRIES)

    logger.info("loading datasheets...")
    datasheets_df = download_datasheets(eppo_code_df)

    logger.info("translating datasheets into plain language...")
    openai = OpenAI()
    datasheets_df = translate_to_plain_text(datasheets_df,
                        openai, OPENAI_CHAT_MODEL,
                        PLAIN_TEXT_SYSTEM_PROMPT, PLAIN_TEXT_PROMPT,
                        COL_TEXT_EN, COL_TEXT_PLAIN)

    datasheets_df = download_datasheets(eppo_code_df)

    logger.info("generating chunks...")
    chunks_df = make_chunks(datasheets_df, COL_TEXT_EN, CHUNK_SIZE, OVERLAP_SIZE, COL_CHUNK)

    for to_language in ASSISTANT_LANGUAGES:
        collection_name = CHROMADB_COLLECTION_TEMPLATE.format(to_language)

        if to_language == 'en':
            logger.info(f"storing {to_language} chunks into {collection_name}...")
            chromadb_collection = connect_to_chromadb(CHROMADB_HOST, CHROMADB_PORT, collection_name)
            add_chunks_to_chromadb(chunks_df, datasheets_df, COL_CHUNK, chromadb_collection)
        else:
            logger.info(f"translating chunks into {to_language}...")
            translated_column = f"translated chunk ({to_language})"
            chunks_df = translate_chunks(chunks_df, COL_CHUNK, 'en', translated_column, to_language)
    
            logger.info(f"storing {to_language} chunks into {collection_name}...")
            chromadb_collection = connect_to_chromadb(CHROMADB_HOST, CHROMADB_PORT, collection_name)
            add_chunks_to_chromadb(chunks_df, datasheets_df, translated_column, chromadb_collection)

    logger.info("all done.")

# And with that, the librarian is done. The searchable text has been updated and
# is ready to be queried.

