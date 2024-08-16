import pytest
from utils.util import TextConverter


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
        "Check this [link](https://example.com)."
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
        "Check this link (https://example.com)."
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
    sample_text = "This is *bold* text."
    expected_output = "This is *bold* text."
    converter = TextConverter(sample_text)
    output = converter._convert_bold_to_whatsapp(converter.text)
    assert output == expected_output
