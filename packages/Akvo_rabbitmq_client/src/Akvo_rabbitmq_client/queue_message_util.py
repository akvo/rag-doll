from typing import List, Dict, Optional


class QueueMessageUtil:

    @staticmethod
    def create_queue_message(
        message_id: str,
        conversation_id: str,
        client_phone_number: str,
        user_phone_number: str,
        body: str,
        media: Optional[List[Dict[str, str]]] = None,
        context: Optional[List[Dict[str, str]]] = None,
        transformation_log: Optional[List[str]] = None
    ) -> Dict[str, any]:
        if media is None:
            media = []
        if context is None:
            context = []
        if transformation_log is None:
            transformation_log = [body]

        message = {
            "conversation_envelope": {
                "message_id": message_id,
                "conversation_id": conversation_id,
                "client_phone_number": client_phone_number,
                "user_phone_number": user_phone_number
            },
            "body": body,
            "media": media,
            "context": context,
            "transformation_log": transformation_log
        }
        return message


queue_message_util = QueueMessageUtil()
