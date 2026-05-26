from typing import Any

from sqlalchemy.orm import Session

from app.core.cache import CacheService
from app.core.database import get_session_factory
from app.sentiment.service import SentimentService
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.analyze_sentiment_task")
def analyze_sentiment_task(payload: dict[str, Any]) -> dict[str, Any]:
    db: Session = get_session_factory()()
    try:
        import asyncio

        service = SentimentService(cache_service=CacheService(fallback_mode=True))
        return asyncio.run(
            service.analyze_text(
                text=payload["text"],
                db=db,
                use_cache=True,
                save_to_db=True,
                request_id=payload.get("request_id"),
                actor_id=payload.get("actor_id"),
            )
        )
    finally:
        db.close()
