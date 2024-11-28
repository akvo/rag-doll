import os
import json

from clients.twilio_client import TwilioClient

JSON_FILE_PATH = "./sources/twilio_message_template.json"


def fetch_templates_and_save_json():
    twilio_client = TwilioClient()

    # Retrieve the environment variables for the template IDs
    VERIFICATION_TEMPLATE_ID_en = os.getenv("VERIFICATION_TEMPLATE_ID_en")
    VERIFICATION_TEMPLATE_ID_sw = os.getenv("VERIFICATION_TEMPLATE_ID_sw")
    VERIFICATION_TEMPLATE_ID_fr = os.getenv("VERIFICATION_TEMPLATE_ID_fr")
    BROADCAST_TEMPLATE_ID_en = os.getenv("BROADCAST_TEMPLATE_ID_en")
    BROADCAST_TEMPLATE_ID_sw = os.getenv("BROADCAST_TEMPLATE_ID_sw")
    BROADCAST_TEMPLATE_ID_fr = os.getenv("BROADCAST_TEMPLATE_ID_fr")
    INTRO_TEMPLATE_ID_en = os.getenv("INTRO_TEMPLATE_ID_en")
    INTRO_TEMPLATE_ID_sw = os.getenv("INTRO_TEMPLATE_ID_sw")
    INTRO_TEMPLATE_ID_fr = os.getenv("INTRO_TEMPLATE_ID_fr")
    CONVERSATION_RECONNECT_TEMPLATE_en = os.getenv(
        "CONVERSATION_RECONNECT_TEMPLATE_en"
    )
    CONVERSATION_RECONNECT_TEMPLATE_sw = os.getenv(
        "CONVERSATION_RECONNECT_TEMPLATE_sw"
    )
    CONVERSATION_RECONNECT_TEMPLATE_fr = os.getenv(
        "CONVERSATION_RECONNECT_TEMPLATE_fr"
    )

    # List of all template IDs
    content_sids = [
        VERIFICATION_TEMPLATE_ID_en,
        VERIFICATION_TEMPLATE_ID_sw,
        VERIFICATION_TEMPLATE_ID_fr,
        BROADCAST_TEMPLATE_ID_en,
        BROADCAST_TEMPLATE_ID_sw,
        BROADCAST_TEMPLATE_ID_fr,
        INTRO_TEMPLATE_ID_en,
        INTRO_TEMPLATE_ID_sw,
        INTRO_TEMPLATE_ID_fr,
        CONVERSATION_RECONNECT_TEMPLATE_en,
        CONVERSATION_RECONNECT_TEMPLATE_sw,
        CONVERSATION_RECONNECT_TEMPLATE_fr,
    ]

    # List to store the template content
    content_data = {}

    # Fetch and structure the template data
    for content_sid in content_sids:
        if not content_sid:
            continue
        template_content = twilio_client.get_message_template(
            content_sid=content_sid
        )
        content = None if not template_content else template_content
        content_data.update({content_sid: content})

    # Write the content data to a JSON file
    with open(JSON_FILE_PATH, "w") as json_file:
        json.dump(content_data, json_file, indent=2)

    print(f"JSON file saved at {JSON_FILE_PATH}")


if __name__ == "__main__":
    # Run the function to fetch templates and save to a JSON file
    fetch_templates_and_save_json()
