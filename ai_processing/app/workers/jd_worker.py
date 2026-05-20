"""
JD Worker — AI Processing Service
Lắng nghe hàng đợi RabbitMQ `jd_ingestion_queue`, nhận dữ liệu thô từ Crawler,
chạy toàn bộ pipeline NER → Knowledge Graph → Embedding → lưu vào PostgreSQL.
"""
import asyncio
import json
import logging
import threading
from typing import Any

import pika

from app.common.config import settings
from app.features.jd_ingestion.input_adapter import JDInputAdapter
from app.features.jd_ingestion.schemas import IngestJobRequest
from app.features.jd_ingestion.service import JDProcessingService

logger = logging.getLogger(__name__)

# Queue chuyên dụng cho JD — đọc từ settings hoặc dùng default
JD_INGESTION_QUEUE = "jd_ingestion_queue"


class JDWorker:
    """
    Worker chạy trên một thread riêng, túc trực lắng nghe RabbitMQ.
    Tự động reconnect khi mất kết nối.
    Xử lý từng message tuần tự (prefetch_count=1) để tránh quá tải Gemini API.
    """

    def __init__(self):
        self.queue_name = JD_INGESTION_QUEUE
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._connection: pika.BlockingConnection | None = None

    def start(self):
        if self._thread and self._thread.is_alive():
            logger.warning("[JDWorker] Already running, skip start.")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._consume_forever, daemon=True, name="jd-worker")
        self._thread.start()
        logger.info("[JDWorker] Started, listening on queue: %s", self.queue_name)

    def stop(self):
        logger.info("[JDWorker] Stopping...")
        self._stop_event.set()
        if self._connection and self._connection.is_open:
            self._connection.add_callback_threadsafe(self._connection.close)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=15)
        logger.info("[JDWorker] Stopped.")

    def _connect(self) -> pika.BlockingConnection:
        if settings.RABBITMQ_URL:
            return pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
        return pika.BlockingConnection(pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            heartbeat=600,
            blocked_connection_timeout=300,
        ))

    def _consume_forever(self):
        """Vòng lặp chính: kết nối → consume → nếu lỗi thì đợi 5s và reconnect."""
        while not self._stop_event.is_set():
            try:
                self._connection = self._connect()
                channel = self._connection.channel()
                channel.queue_declare(queue=self.queue_name, durable=True)

                # prefetch_count=1: chỉ nhận 1 message tại một thời điểm,
                # xử lý xong mới nhận cái tiếp theo — tránh overload Gemini API rate limit
                channel.basic_qos(prefetch_count=1)

                logger.info("[JDWorker] Connected to RabbitMQ, waiting for messages...")

                for method_frame, _, body in channel.consume(queue=self.queue_name, inactivity_timeout=1):
                    if self._stop_event.is_set():
                        break
                    if method_frame is None:
                        # inactivity timeout — không có message mới, tiếp tục vòng lặp
                        continue

                    try:
                        payload = json.loads(body.decode("utf-8"))
                        msg_type = payload.get("type", "unknown")
                        logger.info(
                            "[JDWorker] Processing message type=%s, title=%s",
                            msg_type,
                            payload.get("title") or payload.get("post_id", "N/A"),
                        )
                        asyncio.run(_process_jd_message(payload))
                        channel.basic_ack(method_frame.delivery_tag)
                        logger.info("[JDWorker] Message ACK'd successfully.")
                    except Exception as exc:
                        logger.error("[JDWorker] Message processing failed: %s", exc, exc_info=True)
                        # requeue=False: message thất bại không đưa trở lại queue
                        # tránh vòng lặp vô hạn với message lỗi
                        channel.basic_nack(method_frame.delivery_tag, requeue=False)

                channel.cancel()
                if self._connection and self._connection.is_open:
                    self._connection.close()

            except Exception as exc:
                if not self._stop_event.is_set():
                    logger.error("[JDWorker] Connection lost, reconnecting in 5s: %s", exc)
                    self._stop_event.wait(5)


async def _process_jd_message(payload: dict[str, Any]) -> None:
    """
    Xử lý một message từ RabbitMQ:
    1. Map payload thô → IngestJobRequest (schema chung cho mọi nguồn)
    2. Gọi JDProcessingService.ingest_jobs() để chạy pipeline đầy đủ:
       NER → Knowledge Graph → Embedding → INSERT vào PostgreSQL
    """
    msg_type = payload.get("type", "")

    # Bỏ qua smoke test messages nếu có
    if payload.get("smoke_test"):
        logger.info("[JDWorker] Smoke-test message, skipping.")
        return

    # Ánh xạ payload thô về IngestJobRequest — schema chung để JDInputAdapter xử lý
    try:
        request = _map_payload_to_request(payload, msg_type)
    except ValueError as exc:
        logger.warning("[JDWorker] Skipping message — cannot map payload: %s", exc)
        return

    # Gọi service xử lý: NER → KnowledgeGraph → Embedding → DB
    result = await JDProcessingService.ingest_jobs([request])

    summary = result.summary
    logger.info(
        "[JDWorker] Ingest done: total=%d success=%d skipped=%d errors=%d",
        summary.total,
        summary.success,
        summary.skipped,
        summary.errors,
    )

    if result.results:
        for item in result.results:
            if item.status == "success":
                logger.info("[JDWorker] ✅ Inserted job: %s (id=%s)", item.title, item.job_id)
            elif item.status == "skipped":
                logger.info("[JDWorker] ⏭ Skipped (duplicate): %s", item.title)
            elif item.status == "failed":
                logger.error("[JDWorker] ❌ Failed: %s — %s", item.title, item.detail)


def _map_payload_to_request(payload: dict[str, Any], msg_type: str) -> IngestJobRequest:
    """
    Chuyển đổi payload thô từ Crawler thành IngestJobRequest.

    Crawler gửi các field tuỳ thuộc vào nguồn:
    - LinkedIn/ITviec/TopCV: title, description, company, location, post_time, link
    - Facebook: post_id, text, author, timestamp, url, likes, comments_count, shares
    """
    if msg_type == "scraped_facebook_post":
        # Facebook post: nội dung nằm trong field 'text'
        text = payload.get("text") or payload.get("content") or ""
        if not text:
            raise ValueError("Facebook post has no text content.")
        return IngestJobRequest(
            text=text,
            post_id=payload.get("post_id"),
            author=payload.get("author"),
            url=payload.get("url") or payload.get("link"),
            timestamp=payload.get("timestamp"),
            scraped_at=payload.get("scraped_at"),
            likes=payload.get("likes"),
            comments_count=payload.get("comments_count"),
            shares=payload.get("shares"),
            comments=payload.get("comments", []),
        )
    else:
        # Job từ LinkedIn / ITviec / TopCV: nội dung nằm trong 'description'
        description = payload.get("description") or payload.get("text") or ""
        if not description:
            raise ValueError(f"Job payload has no description or text. Keys: {list(payload.keys())}")
        return IngestJobRequest(
            title=payload.get("title"),
            company=payload.get("company"),
            location=payload.get("location"),
            post_time=payload.get("post_time") or payload.get("posted_at"),
            link=payload.get("link") or payload.get("url"),
            description=description,
        )


# Singleton instance — được start/stop bởi FastAPI lifespan trong main.py
jd_worker = JDWorker()
