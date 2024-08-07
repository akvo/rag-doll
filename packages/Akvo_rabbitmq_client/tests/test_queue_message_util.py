import unittest

from uuid import UUID, uuid4
from Akvo_rabbitmq_client import queue_message_util
from enum import Enum
from datetime import datetime, timezone


class ChatRoleEnum(Enum):
    USER = "user"
    CLIENT = "client"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Platform_Enum(Enum):
    WHATSAPP = "WHATSAPP"
    SLACK = "SLACK"


class TestQueueMessageUtil(unittest.TestCase):

    def test_create_queue_message_invalid_sender_role(self):
        with self.assertRaises(ValueError) as context:
            queue_message_util.create_queue_message(
                message_id="123",
                client_phone_number="9876543210",
                user_phone_number="1234567890",
                sender_role="invalid_sender_role",
                sender_role_enum=ChatRoleEnum,
                platform=Platform_Enum.SLACK,
                platform_enum=Platform_Enum,
                body="Hello, world!",
            )
        self.assertTrue(
            "Invalid sender_role value: invalid_sender_role. Must be one of:"
            in str(context.exception)
        )

    def test_create_queue_message_invalid_platform(self):
        with self.assertRaises(ValueError) as context:
            queue_message_util.create_queue_message(
                message_id="123",
                client_phone_number="9876543210",
                user_phone_number="1234567890",
                sender_role=ChatRoleEnum.SYSTEM,
                sender_role_enum=ChatRoleEnum,
                platform="invalid_platform",
                platform_enum=Platform_Enum,
                body="Hello, world!",
            )
        self.assertTrue(
            "Invalid platform value: invalid_platform. Must be one of:"
            in str(context.exception)
        )

    def test_create_queue_message_with_minimal_data(self):
        timestamp = datetime.now(timezone.utc).isoformat()

        message = queue_message_util.create_queue_message(
            message_id=str(uuid4()),
            client_phone_number="+6281234567890",
            user_phone_number="+6282234567899",
            sender_role=ChatRoleEnum.USER,
            sender_role_enum=ChatRoleEnum,
            platform=Platform_Enum.WHATSAPP,
            platform_enum=Platform_Enum,
            body="This is the original message text typed by the client.",
            timestamp=timestamp,
        )
        self.assertEqual(
            message["conversation_envelope"]["client_phone_number"],
            "+6281234567890",
        )
        self.assertEqual(
            message["conversation_envelope"]["user_phone_number"],
            "+6282234567899",
        )
        self.assertEqual(
            message["conversation_envelope"]["sender_role"],
            ChatRoleEnum.USER.value,
        )
        self.assertEqual(
            message["conversation_envelope"]["platform"],
            Platform_Enum.WHATSAPP.value,
        )
        self.assertEqual(
            message["conversation_envelope"]["timestamp"], timestamp
        )
        self.assertEqual(
            message["body"],
            "This is the original message text typed by the client.",
        )
        self.assertEqual(message["media"], [])
        self.assertEqual(message["context"], [])
        self.assertEqual(
            message["transformation_log"],
            ["This is the original message text typed by the client."],
        )

        # Check UUIDs
        self.assertTrue(UUID(message["conversation_envelope"]["message_id"]))

    def test_create_queue_message_with_media_and_context(self):
        media_items = [
            {
                "type": "image",
                "url": "https://storage.service/path/to/image.jpg",
            },
            {
                "type": "voice",
                "url": "https://storage.service/path/to/voice.mp3",
            },
        ]
        context_items = [
            {
                "type": "image_description",
                "description": "A description of the image.",
            }
        ]
        message = queue_message_util.create_queue_message(
            message_id=str(uuid4()),
            client_phone_number="+6281234567890",
            user_phone_number="+6282234567899",
            sender_role=ChatRoleEnum.USER,
            sender_role_enum=ChatRoleEnum,
            platform=Platform_Enum.WHATSAPP,
            platform_enum=Platform_Enum,
            body="This is the original message text typed by the client.",
            media=media_items,
            context=context_items,
        )
        self.assertEqual(len(message["media"]), 2)
        self.assertEqual(len(message["context"]), 1)
        self.assertEqual(message["media"][0]["type"], "image")
        self.assertEqual(
            message["media"][0]["url"],
            "https://storage.service/path/to/image.jpg",
        )
        self.assertEqual(message["context"][0]["type"], "image_description")
        self.assertEqual(
            message["context"][0]["description"], "A description of the image."
        )


if __name__ == "__main__":
    unittest.main()
