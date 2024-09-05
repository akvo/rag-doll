import os
from pathlib import Path
from google.cloud import storage
import shutil

BUCKET_NAME = os.environ["BUCKET_NAME"]
STORAGE_LOCATION = os.environ.get("STORAGE_LOCATION")


def upload(file: str, folder: str, filename: str = None, public: bool = False):
    """Uploads a file to Google Cloud Storage or local storage."""
    if not filename:
        filename = os.path.basename(file)

    TESTING = os.environ.get("TESTING")
    if TESTING:
        fake_location = f"./tmp/fake-storage/{filename}"
        shutil.copy2(file, fake_location)
        return fake_location

    if STORAGE_LOCATION:
        location = f"{STORAGE_LOCATION}/{filename}"
        shutil.copy2(file, location)
        return location

    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    destination_blob_name = f"{folder}/{filename}"
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(file)
    os.remove(file)

    if public:
        blob.make_public()
        return blob.public_url

    return blob.name


def delete(url: str):
    """Deletes a file from Google Cloud Storage or local storage."""
    file = os.path.basename(url)
    folder = os.path.dirname(url).split("/")[-1]

    TESTING = os.environ.get("TESTING")
    if TESTING or STORAGE_LOCATION:
        os.remove(url)
        return url

    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"{folder}/{file}")
    blob.delete()
    return blob.name


def check(url: str):
    """Checks if a file exists in Google Cloud Storage or local storage."""
    TESTING = os.environ.get("TESTING")
    if TESTING or STORAGE_LOCATION:
        return Path(url).is_file()

    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    return storage.Blob(name=url, bucket=bucket).exists(storage_client)


def download(url: str):
    """Downloads a file from Google Cloud Storage or local storage."""
    TESTING = os.environ.get("TESTING")
    if TESTING:
        tmp_file = os.path.basename(url)
        tmp_file = f"./tmp/{tmp_file}"
        return tmp_file

    if STORAGE_LOCATION:
        original_filename = os.path.basename(url)
        return f"{STORAGE_LOCATION}/{original_filename}"

    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(url)
    tmp_file = os.path.basename(url)
    tmp_file = f"./tmp/{tmp_file}"
    blob.download_to_filename(tmp_file)
    return tmp_file
