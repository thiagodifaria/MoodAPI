import logging
import time
from collections.abc import Callable
from typing import Any

import psutil
from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

HTTP_REQUESTS = Counter(
    "moodapi_http_requests_total",
    "Total de requests HTTP",
    ["method", "path", "status"],
)
HTTP_REQUEST_DURATION = Histogram(
    "moodapi_http_request_duration_seconds",
    "Duracao dos requests HTTP",
    ["method", "path"],
)
SENTIMENT_INFERENCES = Counter(
    "moodapi_sentiment_inferences_total",
    "Total de inferencias de sentimento",
    ["sentiment", "cached"],
)
SENTIMENT_INFERENCE_DURATION = Histogram(
    "moodapi_sentiment_inference_duration_seconds",
    "Duracao da inferencia de sentimento",
)
CACHE_OPERATIONS = Counter(
    "moodapi_cache_operations_total",
    "Operacoes de cache",
    ["operation", "result"],
)
PROCESS_MEMORY = Gauge(
    "moodapi_process_memory_bytes",
    "Memoria residente do processo",
)
MODEL_LOADED = Gauge(
    "moodapi_model_loaded",
    "Indica se o modelo foi carregado",
)


def canonical_path(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    return path or request.url.path


async def prometheus_middleware(request: Request, call_next: Callable[..., Any]) -> Response:
    start = time.perf_counter()
    path = canonical_path(request)
    try:
        response = await call_next(request)
        return response
    finally:
        duration = time.perf_counter() - start
        status = str(getattr(locals().get("response", None), "status_code", 500))
        HTTP_REQUESTS.labels(request.method, path, status).inc()
        HTTP_REQUEST_DURATION.labels(request.method, path).observe(duration)
        PROCESS_MEMORY.set(psutil.Process().memory_info().rss)


def record_sentiment_inference(sentiment: str, cached: bool, duration_seconds: float) -> None:
    SENTIMENT_INFERENCES.labels(sentiment, str(cached).lower()).inc()
    SENTIMENT_INFERENCE_DURATION.observe(duration_seconds)


def record_cache_operation(operation: str, result: str) -> None:
    CACHE_OPERATIONS.labels(operation, result).inc()


def set_model_loaded(loaded: bool) -> None:
    MODEL_LOADED.set(1 if loaded else 0)


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def setup_observability(app: FastAPI) -> None:
    app.middleware("http")(prometheus_middleware)

    if not settings.otel.enabled:
        logger.info("OpenTelemetry desabilitado")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({"service.name": settings.otel.service_name})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=settings.otel.exporter_otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        FastAPIInstrumentor.instrument_app(app)
        SQLAlchemyInstrumentor().instrument()
        RedisInstrumentor().instrument()
        logger.info("OpenTelemetry habilitado")
    except Exception as exc:
        logger.warning("Falha ao inicializar OpenTelemetry: %s", exc)
