import uuid
from importlib import import_module
from importlib.util import find_spec
from typing import Any

from app.config import get_settings

settings = get_settings()


class AsyncPredictionQueue:
    """Celery/RabbitMQ adapter used by the HTTP layer."""

    def enabled(self) -> bool:
        return settings.queue.enabled

    def health(self) -> dict[str, Any]:
        celery_available = find_spec("celery") is not None
        return {
            "status": "healthy" if self.enabled() and celery_available else "disabled",
            "enabled": self.enabled(),
            "broker": settings.queue.broker_url,
            "queue": settings.queue.sentiment_queue,
            "celery_available": celery_available,
        }

    def enqueue_sentiment(self, payload: dict[str, Any]) -> dict[str, Any]:
        task_id = str(uuid.uuid4())
        if not self.enabled():
            return {"queued": False, "task_id": task_id, "reason": "queue disabled"}

        celery_app = import_module("app.workers.celery_app").celery_app
        async_result = celery_app.send_task(
            "app.workers.tasks.analyze_sentiment_task",
            kwargs={"payload": payload},
            queue=settings.queue.sentiment_queue,
            task_id=task_id,
        )
        return {"queued": True, "task_id": async_result.id}


_queue = AsyncPredictionQueue()


def get_prediction_queue() -> AsyncPredictionQueue:
    return _queue
