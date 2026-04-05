"""
Celery configuration for async task processing.
"""
from celery import Celery
from app.config import settings

celery_app = Celery(
    "ocr_tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

# Import tasks to register them with Celery
from app.tasks import ocr_tasks  # noqa: E402, F401
