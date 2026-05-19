import asyncio
import json
import threading
from typing import Any
from uuid import UUID

import pika

from app.common.config import settings
from app.common.database.sql_db import connect_sql_db
from app.features.cv_processing.repository import CVRepository
from app.features.cv_processing.service import CVProcessingService


class CVWorker:
    def __init__(self):
        self.queue_name = settings.CV_PROCESSING_QUEUE
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._connection: pika.BlockingConnection | None = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._consume_forever, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._connection and self._connection.is_open:
            self._connection.add_callback_threadsafe(self._connection.close)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)

    def _connect(self):
        if settings.RABBITMQ_URL:
            return pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
        return pika.BlockingConnection(pika.ConnectionParameters(host=settings.RABBITMQ_HOST))

    def _consume_forever(self):
        while not self._stop_event.is_set():
            try:
                self._connection = self._connect()
                channel = self._connection.channel()
                channel.queue_declare(queue=self.queue_name, durable=True)
                channel.basic_qos(prefetch_count=1)

                for method_frame, _, body in channel.consume(queue=self.queue_name, inactivity_timeout=1):
                    if self._stop_event.is_set():
                        break
                    if method_frame is None:
                        continue

                    try:
                        payload = json.loads(body.decode("utf-8"))
                        asyncio.run(process_cv_message(payload))
                        channel.basic_ack(method_frame.delivery_tag)
                    except Exception as exc:
                        print(f"[CVWorker] message failed: {exc}")
                        channel.basic_nack(method_frame.delivery_tag, requeue=False)

                channel.cancel()
                if self._connection and self._connection.is_open:
                    self._connection.close()
            except Exception as exc:
                if not self._stop_event.is_set():
                    print(f"[CVWorker] consumer reconnecting after error: {exc}")
                    self._stop_event.wait(5)


async def process_cv_message(payload: dict[str, Any]):
    if payload.get("smoke_test"):
        print(f"[CVWorker] smoke-test message received for user_id={payload.get('user_id')}")
        return

    cv_id = UUID(str(payload["cv_id"]))
    cv_urls = payload.get("cv_urls") or []
    if not cv_urls and payload.get("image_url"):
        cv_urls = [payload["image_url"]]

    conn = await connect_sql_db()
    try:
        await CVRepository.mark_processing(conn, cv_id=cv_id, cv_urls=cv_urls)
        parsed = await CVProcessingService.parse_cv_images(cv_urls)
        embedding = await CVProcessingService.generate_embedding(parsed)
        recommended_jobs = await CVRepository.find_matching_jobs(conn, embedding)
        parsed_data = {
            **parsed.model_dump(),
            "status": "completed",
            "cv_urls": cv_urls,
            "recommended_jobs": recommended_jobs,
        }
        raw_text = json.dumps(parsed.model_dump(), ensure_ascii=False)
        await CVRepository.update_processed(
            conn=conn,
            cv_id=cv_id,
            raw_text=raw_text,
            parsed_data=parsed_data,
            embedding=embedding,
        )
    except Exception as exc:
        await CVRepository.mark_failed(conn, cv_id=cv_id, cv_urls=cv_urls, error=str(exc))
        raise
    finally:
        await conn.close()


cv_worker = CVWorker()
