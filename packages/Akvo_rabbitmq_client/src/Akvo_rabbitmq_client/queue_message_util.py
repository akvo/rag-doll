from typing import List, Dict, Optional
from uuid import uuid4


class QueueMessageUtil:

    @staticmethod
    def create_queue_message(
        client_id: str,
        user_id: str,
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
                "message_id": str(uuid4()),
                "conversation_id": str(uuid4()),
                "client_id": client_id,
                "user_id": user_id
            },
            "body": body,
            "media": media,
            "context": context,
            "transformation_log": transformation_log
        }
        return message


queue_message_util = QueueMessageUtil()
