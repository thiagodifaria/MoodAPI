import asyncio
import json
import logging
from typing import Any

from app.config import get_settings
from app.core.cache import CacheService
from app.core.database import get_session_factory
from app.sentiment.service import SentimentService

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_sentiment_stream() -> None:
    """Consumes input events and publishes sentiment results to Kafka/Redpanda."""
    if not settings.streaming.enabled:
        logger.info("Streaming desabilitado")
        return

    try:
        from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
    except ImportError as error:
        raise RuntimeError("aiokafka nao instalado") from error

    consumer = AIOKafkaConsumer(
        settings.streaming.input_topic,
        bootstrap_servers=settings.streaming.bootstrap_servers,
        group_id=settings.streaming.consumer_group,
        enable_auto_commit=True,
    )
    producer = AIOKafkaProducer(bootstrap_servers=settings.streaming.bootstrap_servers)

    await consumer.start()
    await producer.start()
    try:
        async for message in consumer:
            payload: dict[str, Any] = json.loads(message.value.decode("utf-8"))
            db = get_session_factory()()
            try:
                service = SentimentService(cache_service=CacheService(fallback_mode=True))
                result = await service.analyze_text(
                    text=payload["text"],
                    db=db,
                    use_cache=True,
                    save_to_db=True,
                    request_id=payload.get("request_id"),
                    actor_id=payload.get("actor_id"),
                )
                await producer.send_and_wait(
                    settings.streaming.output_topic,
                    json.dumps(result, default=str).encode("utf-8"),
                )
            finally:
                db.close()
    finally:
        await consumer.stop()
        await producer.stop()


def main() -> None:
    asyncio.run(run_sentiment_stream())


if __name__ == "__main__":
    main()
