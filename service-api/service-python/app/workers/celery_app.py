from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "moodapi",
    broker=settings.queue.broker_url,
    backend=settings.queue.result_backend,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_default_queue=settings.queue.sentiment_queue,
    task_routes={
        "app.workers.tasks.analyze_sentiment_task": {"queue": settings.queue.sentiment_queue},
    },
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

