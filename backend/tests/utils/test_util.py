import os
import pytest
import json

from utils.util import (
    TextConverter,
    generate_message_template_lang_by_phone_number,
    get_template_content_from_json,
)


@pytest.fixture
def sample_text():
    """Sample text for testing."""
    return (
        "# Header 1\n"
        "## Header 2\n"
        "### Header 3\n"
        "* Bullet point 1\n"
        "* Bullet point 2\n"
        "This is _italic_ text.\n"
        "This is **bold** text."
        "This is `code block` text."
        "This is hypen-between-words."
        "Check this [link](https://example.com/verify/unique-uuid)."
    )


@pytest.fixture
def expected_whatsapp_output():
    """Expected WhatsApp-formatted output."""
    return (
        "*HEADER 1*\n\n"
        "*HEADER 2*\n"
        "*HEADER 3*\n"
        "* Bullet point 1\n"
        "* Bullet point 2\n"
        "This is _italic_ text.\n"
        "This is *bold* text."
        "This is `code block` text."
        "This is hypen-between-words."
        "Check this link (https://example.com/verify/unique-uuid)."
    )


def test_format_whatsapp(sample_text, expected_whatsapp_output):
    """Test the format_whatsapp method."""
    converter = TextConverter(sample_text)
    whatsapp_output = converter.format_whatsapp()
    assert whatsapp_output == expected_whatsapp_output


def test_convert_headers_to_uppercase():
    """Test the header conversion to uppercase."""
    sample_text = "# header\n## subheader"
    expected_output = "*HEADER*\n\n*SUBHEADER*"
    converter = TextConverter(sample_text)
    output = converter._convert_headers_to_uppercase_bold(converter.text)
    assert output == expected_output


def test_convert_italics_to_whatsapp():
    """Test the conversion of italics to WhatsApp format."""
    sample_text = "This is _italic_ text."
    expected_output = "This is _italic_ text."
    converter = TextConverter(sample_text)
    output = converter._convert_italics_to_whatsapp(converter.text)
    assert output == expected_output


def test_convert_bold_to_whatsapp():
    """Test the conversion of bold text to WhatsApp format."""
    sample_text = "This is **bold** text."
    expected_output = "This is *bold* text."
    converter = TextConverter(sample_text)
    output = converter._convert_bold_to_whatsapp(converter.text)
    assert output == expected_output


def test_not_to_convert_hypen_between_words():
    """Test the conversion of hypen between words."""
    sample_text = "This is word-hypenbold-word text."
    converter = TextConverter(sample_text)
    output = converter._convert_bold_to_whatsapp(converter.text)
    assert output == sample_text


def test_not_to_convert_hypen_inside_urls():
    """Test the conversion of hypen inside URLs."""
    sample_text = (
        "This is http://localhost:3001/verification/unique-uuid-here text."
    )
    converter = TextConverter(sample_text)
    output = converter._convert_bold_to_whatsapp(converter.text)
    assert output == sample_text


def test_generate_message_template_lang_by_phone_number():
    # expected sw
    lang = generate_message_template_lang_by_phone_number(
        phone_number="+254712345678"
    )
    assert lang == "sw"
    # expected fr
    lang = generate_message_template_lang_by_phone_number(
        phone_number="+22678123456"
    )
    assert lang == "fr"
    # expected en
    lang = generate_message_template_lang_by_phone_number(
        phone_number="+6281999123456"
    )
    assert lang == "en"
    # expected en
    lang = generate_message_template_lang_by_phone_number(
        phone_number="+2348031234567"  # Nigeria
    )
    assert lang == "en"


def test_get_template_content_from_json_file_not_exist():
    file_path = "./twilio_message_template_notfound.json"
    res = get_template_content_from_json(
        content_sid="HX123456", testing_file_path=file_path
    )
    assert res is False


def test_get_template_content_from_json_success():
    file_path = "./tests/utils/twilio_message_template_testing.json"
    # create file for testing
    content_data = {
        "HX123456": "Template 1",
        "HX223456": "Template 2",
        "HX323456": "Template 3",
    }
    with open(file_path, "w") as json_file:
        json.dump(content_data, json_file, indent=2)
    res = get_template_content_from_json(
        content_sid="HX223456", testing_file_path=file_path
    )
    assert res == "Template 2"
    # remove file after testing
    if os.path.exists(file_path):
        os.remove(file_path)
