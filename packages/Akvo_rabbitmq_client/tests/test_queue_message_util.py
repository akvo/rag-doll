import unittest
from uuid import UUID, uuid4
from Akvo_rabbitmq_client import queue_message_util


class TestQueueMessageUtil(unittest.TestCase):

    def test_create_queue_message_with_minimal_data(self):
        message = queue_message_util.create_queue_message(
            message_id=str(uuid4()),
            conversation_id=str(uuid4()),
            client_phone_number="+6281234567890",
            user_phone_number="+6282234567899",
            body="This is the original message text typed by the client."
        )
        self.assertEqual(
            message["conversation_envelope"]["client_phone_number"],
            "+6281234567890")
        self.assertEqual(
            message["conversation_envelope"]["user_phone_number"],
            "+6282234567899")
        self.assertEqual(
            message["body"],
            "This is the original message text typed by the client.")
        self.assertEqual(message["media"], [])
        self.assertEqual(message["context"], [])
        self.assertEqual(
            message["transformation_log"],
            ["This is the original message text typed by the client."])

        # Check UUIDs
        self.assertTrue(
            UUID(message["conversation_envelope"]["message_id"]))
        self.assertTrue(
            UUID(message["conversation_envelope"]["conversation_id"]))

    def test_create_queue_message_with_media_and_context(self):
        media_items = [{
            "type": "image",
            "url": "https://storage.service/path/to/image.jpg"
        }, {
            "type": "voice",
            "url": "https://storage.service/path/to/voice.mp3"
        }]
        context_items = [{
            "type": "image_description",
            "description": "A description of the image."
        }]
        message = queue_message_util.create_queue_message(
            message_id=str(uuid4()),
            conversation_id=str(uuid4()),
            client_phone_number="+6281234567890",
            user_phone_number="+6282234567899",
            body="This is the original message text typed by the client.",
            media=media_items,
            context=context_items
        )
        self.assertEqual(len(message["media"]), 2)
        self.assertEqual(len(message["context"]), 1)
        self.assertEqual(message["media"][0]["type"], "image")
        self.assertEqual(
            message["media"][0]["url"],
            "https://storage.service/path/to/image.jpg")
        self.assertEqual(message["context"][0]["type"], "image_description")
        self.assertEqual(
            message["context"][0]["description"], "A description of the image.")


if __name__ == "__main__":
    unittest.main()
