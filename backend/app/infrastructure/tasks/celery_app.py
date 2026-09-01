from celery import Celery

from app.core.config import Settings

settings = Settings()

celery_app = Celery(
    "flowforge",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.infrastructure.tasks.email_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
