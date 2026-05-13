from celery import Celery
from app.core.config import settings

# Khởi tạo Celery
celery_app = Celery(
    "jobmatch",
    broker=settings.RABBITMQ_URL,
    backend="redis://redis:6379/0",   # Dùng Redis làm result backend
    include=["app.tasks.cv_tasks"]    # Import tasks
)

# Cấu hình Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,           # 1 giờ
    task_soft_time_limit=3300,
    worker_prefetch_multiplier=1,   # Quan trọng khi dùng GPU/LLM
)

# Optional: Beat scheduler (chạy task định kỳ)
celery_app.conf.beat_schedule = {
    # Ví dụ: Crawl job mỗi 6 tiếng
    # 'crawl-jobs-every-6-hours': {
    #     'task': 'app.tasks.crawler_tasks.crawl_all_jobs',
    #     'schedule': 21600.0,  # 6 hours
    # },
}