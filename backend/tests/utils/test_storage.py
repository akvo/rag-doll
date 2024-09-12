import os
import utils.storage as storage


def test_upload_local(setup_local_storage):
    test_file = setup_local_storage["test_file"]
    test_folder = setup_local_storage["test_folder"]
    test_file_content = setup_local_storage["test_file_content"]

    storage.upload(file=test_file, folder="test_folder", public=False)
    expected_result = f"{test_folder}/{os.path.basename(test_file)}"

    assert os.path.isfile(expected_result)
    with open(expected_result, "r") as f:
        content = f.read()
    assert content == test_file_content


def test_delete_local(setup_local_storage):
    test_file = setup_local_storage["test_file"]
    test_folder = setup_local_storage["test_folder"]

    storage.upload(file=test_file, folder="test_folder", public=False)
    file_url = f"{test_folder}/{os.path.basename(test_file)}"

    storage.delete(url=file_url)

    assert not os.path.isfile(file_url)


def test_check_local(setup_local_storage):
    test_file = setup_local_storage["test_file"]
    test_folder = setup_local_storage["test_folder"]

    storage.upload(file=test_file, folder="test_folder", public=False)
    file_url = f"{test_folder}/{os.path.basename(test_file)}"

    assert storage.check(url=file_url)


def test_download_local(setup_local_storage):
    test_file = setup_local_storage["test_file"]
    test_folder = setup_local_storage["test_folder"]
    test_file_content = setup_local_storage["test_file_content"]

    storage.upload(file=test_file, folder="test_folder", public=False)
    file_url = f"{test_folder}/{os.path.basename(test_file)}"

    downloaded_file = storage.download(url=file_url)

    with open(downloaded_file, "r") as f:
        content = f.read()
    assert content == test_file_content
