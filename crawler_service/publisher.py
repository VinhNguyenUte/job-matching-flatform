"""
Publisher module cho Crawler Service.
Chịu trách nhiệm publish dữ liệu cào được lên RabbitMQ để AI Worker xử lý.
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import pika

logger = logging.getLogger(__name__)

# Tên queue riêng dành cho job/post cào từ web — khác với queue xử lý CV của người dùng
JD_INGESTION_QUEUE = os.getenv("JD_INGESTION_QUEUE", "jd_ingestion_queue")
RABBITMQ_URL = os.getenv("RABBITMQ_URL")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")

# Số lượng messages tối đa trong mỗi batch publish (tránh tạo/đóng connection quá nhiều lần)
PUBLISH_BATCH_SIZE = int(os.getenv("PUBLISH_BATCH_SIZE", "50"))


def _get_connection() -> pika.BlockingConnection:
    """Tạo kết nối BlockingConnection tới RabbitMQ."""
    if RABBITMQ_URL:
        return pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    return pika.BlockingConnection(pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        heartbeat=600,
        blocked_connection_timeout=300,
    ))


def _publish_batch(items: list[dict[str, Any]], queue_name: str) -> tuple[int, int]:
    """
    Publish một batch messages lên RabbitMQ.
    Trả về (success_count, failed_count).
    """
    if not items:
        return 0, 0

    success_count = 0
    failed_count = 0

    try:
        connection = _get_connection()
        channel = connection.channel()
        channel.queue_declare(queue=queue_name, durable=True)

        for item in items:
            try:
                message = {
                    **item,
                    "published_at": datetime.now(timezone.utc).isoformat(),
                }
                channel.basic_publish(
                    exchange="",
                    routing_key=queue_name,
                    body=json.dumps(message, ensure_ascii=False, default=str),
                    properties=pika.BasicProperties(
                        content_type="application/json",
                        delivery_mode=2,  # persistent — không mất khi RabbitMQ restart
                    ),
                )
                success_count += 1
            except Exception as exc:
                logger.error("[Publisher] Failed to publish item: %s — %s", item.get("title") or item.get("post_id"), exc)
                failed_count += 1

        connection.close()
    except Exception as exc:
        logger.error("[Publisher] RabbitMQ connection error: %s", exc)
        failed_count += len(items) - success_count

    return success_count, failed_count


def publish_jobs(jobs: list[dict[str, Any]]) -> None:
    """
    Publish danh sách job (từ LinkedIn/ITviec/TopCV) lên RabbitMQ.
    Mỗi job được wrap với type='scraped_job' để JD Worker nhận biết.
    """
    if not jobs:
        logger.info("[Publisher] No jobs to publish.")
        return

    # Wrap mỗi job với metadata type để JD Worker xử lý đúng
    messages = [
        {"type": "scraped_job", **job}
        for job in jobs
    ]

    total = len(messages)
    total_success = 0
    total_failed = 0

    # Chia thành các batch nhỏ để tránh timeout connection
    for i in range(0, total, PUBLISH_BATCH_SIZE):
        batch = messages[i: i + PUBLISH_BATCH_SIZE]
        success, failed = _publish_batch(batch, JD_INGESTION_QUEUE)
        total_success += success
        total_failed += failed
        logger.info(
            "[Publisher] Batch %d/%d published: %d success, %d failed",
            i // PUBLISH_BATCH_SIZE + 1,
            (total + PUBLISH_BATCH_SIZE - 1) // PUBLISH_BATCH_SIZE,
            success,
            failed,
        )

    logger.info(
        "[Publisher] Jobs publish complete: %d/%d success, queue=%s",
        total_success, total, JD_INGESTION_QUEUE,
    )


def publish_facebook_posts(posts: list[dict[str, Any]]) -> None:
    """
    Publish danh sách Facebook post lên RabbitMQ.
    Mỗi post được wrap với type='scraped_facebook_post' để JD Worker nhận biết.
    """
    if not posts:
        logger.info("[Publisher] No Facebook posts to publish.")
        return

    messages = [
        {"type": "scraped_facebook_post", **post}
        for post in posts
    ]

    total = len(messages)
    total_success = 0
    total_failed = 0

    for i in range(0, total, PUBLISH_BATCH_SIZE):
        batch = messages[i: i + PUBLISH_BATCH_SIZE]
        success, failed = _publish_batch(batch, JD_INGESTION_QUEUE)
        total_success += success
        total_failed += failed

    logger.info(
        "[Publisher] Facebook posts publish complete: %d/%d success, queue=%s",
        total_success, total, JD_INGESTION_QUEUE,
    )
