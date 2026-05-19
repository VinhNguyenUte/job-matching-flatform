import json
import os
from datetime import datetime, timezone
from typing import Any, Optional

import pika


class RabbitMQService:
    def __init__(self):
        self.url = os.getenv("RABBITMQ_URL")
        self.host = os.getenv("RABBITMQ_HOST", "localhost")
        self.queue_name = os.getenv("CV_PROCESSING_QUEUE", "cv_processing_queue")

    def _connection(self):
        if self.url:
            return pika.BlockingConnection(pika.URLParameters(self.url))
        return pika.BlockingConnection(pika.ConnectionParameters(host=self.host))

    def publish_task(self, payload: dict[str, Any], queue_name: Optional[str] = None) -> bool:
        try:
            queue = queue_name or self.queue_name
            message = {
                **payload,
                "published_at": datetime.now(timezone.utc).isoformat(),
            }

            connection = self._connection()
            channel = connection.channel()
            channel.queue_declare(queue=queue, durable=True)
            channel.basic_publish(
                exchange="",
                routing_key=queue,
                body=json.dumps(message, ensure_ascii=False, default=str),
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2,
                ),
            )
            connection.close()
            return True
        except Exception as exc:
            print(f"[RabbitMQ] publish failed: {exc}")
            return False

    def publish_cv_uploaded(self, cv_id: int, user_id: str, storage_path: str) -> bool:
        return self.publish_task(
            {
                "type": "cv_uploaded",
                "cv_id": cv_id,
                "user_id": str(user_id),
                "cv_urls": [storage_path],
            }
        )


rabbitmq_service = RabbitMQService()
