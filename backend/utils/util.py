import os
import re
import phonenumbers
import json

from pydantic_extra_types.phone_numbers import PhoneNumber
from pathlib import Path
from typing import Optional


def sanitize_phone_number(phone_number: PhoneNumber):
    if isinstance(phone_number, int):
        return phone_number
    if not re.match(r"^\+\d+$", phone_number):
        raise ValueError("Phone number contains invalid characters")
    phone_number_digits = re.sub(r"\D", "", phone_number)
    return int(phone_number_digits)


def get_value_or_raise_error(data_dict, key, error_msg=None):
    try:
        value = data_dict[key]
    except KeyError:
        if error_msg is None:
            error_msg = f"Key '{key}' not found in message"
        raise KeyError(error_msg)
    return value


def generate_message_template_lang_by_phone_number(phone_number: PhoneNumber):
    phone_number = phonenumbers.parse(phone_number)
    # get the region code
    phone_number_region = phonenumbers.region_code_for_number(phone_number)
    phone_number_region = phone_number_region.lower()
    message_template_lang = "en"
    if phone_number_region == "ke":
        message_template_lang = "sw"
    if phone_number_region == "bf":
        message_template_lang = "fr"
    return message_template_lang


def get_template_content_from_json(
    content_sid: str, testing_file_path: Optional[str] = None
):
    JSON_FILE_PATH = "./sources/twilio_message_template.json"
    if os.getenv("TESTING") or testing_file_path:
        JSON_FILE_PATH = testing_file_path
    file_path = Path(JSON_FILE_PATH)
    if file_path.exists():
        with file_path.open("r") as json_file:
            content_data = json.load(json_file)
            return content_data.get(content_sid)
    else:
        return False


class TextConverter:
    def __init__(self, text: str):
        self.text = text

    def format_whatsapp(self) -> str:
        content = self.text
        content = self._convert_bold_to_whatsapp(content)
        content = self._convert_headers_to_uppercase_bold(content)
        content = self._convert_italics_to_whatsapp(content)
        content = self._convert_links_to_plaintext(content)
        return content

    def format_slack(self) -> str:
        """Format text for Slack (future implementation)."""
        # Placeholder for future Slack-specific formatting
        pass

    def _convert_headers_to_uppercase_bold(self, content: str) -> str:
        content = re.sub(
            r"#### (.+)", lambda m: f"*{m.group(1).upper()}*", content
        )
        content = re.sub(
            r"### (.+)", lambda m: f"*{m.group(1).upper()}*", content
        )
        content = re.sub(
            r"## (.+)", lambda m: f"*{m.group(1).upper()}*", content
        )
        content = re.sub(
            r"# (.+)",
            lambda m: f"*{m.group(1).upper()}*\n",
            content,
        )
        return content

    def _convert_italics_to_whatsapp(self, content: str) -> str:
        return re.sub(r"_(.+?)_", r"_\1_", content)

    def _convert_bold_to_whatsapp(self, content: str) -> str:
        # Convert bold formatting
        content = re.sub(r"\*\*(.+?)\*\*", r"*\1*", content)
        # Replace standalone hyphens with asterisks
        # ignoring hyphens within URLs or between words
        content = re.sub(r"(?<!\w)-{1}(?!\w)", "*", content)
        return content

    def _convert_links_to_plaintext(self, content: str) -> str:
        return re.sub(r"\[(.+?)\]\((https?://[^\s]+)\)", r"\1 (\2)", content)
