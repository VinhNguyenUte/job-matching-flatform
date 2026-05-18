import pika
import json
from app.core.config import settings

class RabbitMQService:
    def __init__(self):
        self.params = pika.URLParameters(settings.RABBITMQ_URL)

    def publish_cv_uploaded(self, cv_id: int, user_id: str, storage_path: str):
        """Bắn message sang Tầng 4 (AI Processing) để tiến hành Parser, NER, Embed"""
        connection = pika.BlockingConnection(self.params)
        channel = connection.channel()
        
        channel.queue_declare(queue=settings.CV_QUEUE_NAME, durable=True)
        
        payload = {
            "cv_id": cv_id,
            "user_id": str(user_id),
            "storage_path": storage_path,
            "action": "PROCESS_CV"
        }
        
        channel.basic_publish(
            exchange='',
            routing_key=settings.CV_QUEUE_NAME,
            body=json.dumps(payload),
            properties=pika.BasicProperties(
                delivery_mode=2, # Đảm bảo message không mất khi crash broker
                content_type='application/json'
            )
        )
        connection.close()

rabbitmq_service = RabbitMQService()