"""
Celery application configuration for background tasks.
"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "webwork",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 min hard limit
    task_soft_time_limit=240,  # 4 min soft limit
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
    task_routes={
        "app.tasks.screenshot_tasks.*": {"queue": "screenshots"},
        "app.tasks.report_tasks.*": {"queue": "reports"},
        "app.tasks.notification_tasks.*": {"queue": "notifications"},
    },
)

# Auto-discover tasks from these modules
celery_app.autodiscover_tasks([
    "app.tasks.screenshot_tasks",
    "app.tasks.report_tasks",
    "app.tasks.notification_tasks",
])
