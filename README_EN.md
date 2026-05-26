# MoodAPI

![MoodAPI](https://img.shields.io/badge/MoodAPI-API-111827?style=for-the-badge&logo=fastapi&logoColor=white)

**Sentiment intelligence API with FastAPI, React, Transformer inference, prediction audit, async queues, event streaming, semantic search and local observability**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-core%20api-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-client%20web-61DAFB?style=flat&logo=react&logoColor=111827)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-audit%20history-4169E1?style=flat&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-cache%20%2B%20rate%20limit-DC382D?style=flat&logo=redis&logoColor=white)](https://redis.io)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-Celery%20jobs-FF6600?style=flat&logo=rabbitmq&logoColor=white)](https://rabbitmq.com)
[![Qdrant](https://img.shields.io/badge/Qdrant-vector%20search-DC244C?style=flat)](https://qdrant.tech)
[![Docker](https://img.shields.io/badge/Docker-local%20stack-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-success?style=flat)](LICENSE)

---

## Documentation

**Repository:** [thiagodifaria/MoodAPI](https://github.com/thiagodifaria/MoodAPI)  
**Short overview:** [README.md](README.md)  
**Leia em Portugues:** [README_PT.md](README_PT.md)  
**Architecture Reference:** [docs/ARQUITETURA.md](docs/ARQUITETURA.md)

---

## Screenshots

### Single Analysis

![MoodAPI single analysis](client-web/public/images/screenshots/single-analysis.png)

### Batch Analysis

![MoodAPI batch analysis](client-web/public/images/screenshots/batch-analysis.png)

### Prediction History

![MoodAPI prediction history](client-web/public/images/screenshots/history.png)

### Semantic Search

![MoodAPI semantic search](client-web/public/images/screenshots/semantic-search.png)

### Health Check

![MoodAPI health check](client-web/public/images/screenshots/health.png)

---

## What is MoodAPI?

MoodAPI is a backend-first AI service for sentiment analysis. It exposes a versioned HTTP API, executes multilingual Transformer inference, stores each prediction for audit/history, indexes prediction records in a vector database and provides a React client web for operating and validating the system.

The project is not a one-endpoint demo. It is a compact service designed to show mature engineering decisions in a proportional scope: strict request validation, predictable runtime, separated backend/frontend boundaries, database migrations, cache, rate limiting, asynchronous jobs, event streaming, semantic retrieval, metrics, health checks and local observability.

The frontend is a technical console. It is meant to exercise the real API: single inference, batch inference, persisted history, semantic search and component health inspection. The backend remains the primary product surface.

---

## Implemented Capabilities

The project includes:

- HTTP API under `/api/v1`.
- Swagger/OpenAPI available at `/docs`.
- Public health, readiness, details and metrics endpoints.
- Single-text sentiment analysis.
- Batch sentiment analysis.
- RabbitMQ/Celery asynchronous analysis submission.
- Redpanda/Kafka-compatible streaming consumer.
- PostgreSQL persistence for prediction history and audit metadata.
- Redis cache for inference results.
- Redis-backed rate limiting with local fallback.
- Qdrant vector database integration.
- Multilingual sentence embeddings for semantic search.
- Semantic result thresholding to avoid weak matches.
- Backfill from prediction history into Qdrant when the vector collection is empty.
- JWT authentication endpoints.
- React client web for real endpoint testing.
- Prometheus metrics endpoint.
- Grafana provisioning.
- OpenTelemetry Collector integration.
- Bash scripts for build and test workflows.

---

## Why this project exists

MoodAPI exists as a technical reference for evolving AI inference into a complete application surface. The core idea is that a useful AI service needs more than a model call: it needs validation, auditability, persistence, observability, operational feedback, cache behavior, batch paths, asynchronous paths and a way to inspect historical predictions.

The architecture is organized around clear engineering boundaries:

- request schemas are explicit;
- runtime configuration is centralized;
- database migrations are versioned;
- predictions are persisted with model metadata;
- cached results are keyed by input and model identity;
- semantic search is backed by Qdrant rather than in-memory filtering;
- queue and streaming paths are separated from synchronous HTTP;
- local observability is available through Prometheus/Grafana/OTel.

---

## High-level Architecture

```text
React client-web
    |
    | HTTP through Nginx proxy
    v
FastAPI
    |
    +--> Sentiment service -> Transformer pipeline
    +--> History service   -> PostgreSQL
    +--> Cache/rate limit  -> Redis
    +--> Vector indexing   -> Qdrant
    +--> Metrics/traces    -> Prometheus / OpenTelemetry

Async flow:
FastAPI -> RabbitMQ -> Celery worker -> Sentiment service -> PostgreSQL/Qdrant

Event flow:
Redpanda topic -> stream worker -> Sentiment service -> Redpanda output topic

Semantic flow:
History record -> multilingual embedding -> Qdrant -> score-filtered results
```

---

## Repository Layout

| Area | Path | Responsibility |
|------|------|----------------|
| API service | `service-api/service-python` | FastAPI app, domain modules, inference, tests and Python config |
| Database | `service-api/service-postgresql` | Alembic migrations and database assets |
| Client Web | `client-web` | React/Vite technical console and public screenshots |
| Infra | `infra` | Docker Compose, Prometheus, Grafana and OpenTelemetry config |
| Scripts | `scripts` | Bash entrypoints for build, runtime and tests |
| Docs | `docs` | Focused architecture reference |

The root is intentionally reserved for entry files: READMEs, license, environment example and top-level directories. Backend implementation stays under `service-api`, while `client-web` is the frontend root.

---

## Stack and rationale

| Technology | Usage | Rationale |
|------------|-------|-----------|
| Python | Core API | Mature AI/ML ecosystem and direct Hugging Face integration |
| FastAPI | HTTP layer | Typed request/response handling, OpenAPI and dependency injection |
| Pydantic v2 | Validation/settings | Strict schemas and predictable configuration loading |
| Transformers | Sentiment inference | Multilingual Transformer pipeline for sentiment classification |
| PostgreSQL | Audit/history | Durable prediction storage, filters and analytics |
| Alembic | Migrations | Versioned schema evolution |
| Redis | Cache/rate limit | Fast result cache and distributed request throttling |
| RabbitMQ | Async jobs | Queue-based processing outside the request path |
| Celery | Workers | Simple Python worker model for queued analysis |
| Redpanda | Streaming | Kafka-compatible local event pipeline |
| Qdrant | Vector search | Semantic retrieval over persisted predictions |
| React/Vite | Client web | Fast technical console for API operation |
| Prometheus | Metrics | Operational counters, latencies and health signals |
| Grafana | Dashboards | Local visualization for API/runtime status |
| OpenTelemetry | Tracing | Request and component correlation |
| Docker Compose | Runtime | Reproducible local stack for all dependencies |

---

## Backend Modules

| Module | Responsibility |
|--------|----------------|
| `app/main.py` | FastAPI bootstrap, lifecycle, routers, health and metrics |
| `app/config.py` | Pydantic settings for database, cache, model, queues, streaming, vectors and telemetry |
| `app/sentiment` | inference orchestration, schemas, routes, persistence and vector indexing hooks |
| `app/history` | prediction history, analytics, filters, stats and detail retrieval |
| `app/auth` | user model, password hashing, login and JWT access |
| `app/core` | database engine, Redis cache, exception mapping, security and observability |
| `app/shared` | middleware, correlation ids, error handlers and rate limiting |
| `app/queue` | RabbitMQ/Celery submission adapter |
| `app/workers` | Celery app and background analysis tasks |
| `app/streaming` | Redpanda/Kafka consumer for event-driven analysis |
| `app/vector` | Qdrant adapter, multilingual embeddings, search threshold and vector health |

---

## Sentiment Inference

The configured default sentiment model is:

```text
lxyuan/distilbert-base-multilingual-cased-sentiments-student
```

This model was chosen because the application needs practical Portuguese and multilingual behavior. The API persists the model name with every prediction, so historical results can be audited after model changes.

Cache keys include both the normalized text and model identity. That prevents stale classifications from older models being reused after a model upgrade.

---

## Semantic Search

Semantic search is backed by Qdrant and multilingual sentence embeddings:

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

The vector collection stores prediction text, sentiment, confidence, language and model metadata. Searches use cosine similarity and a configurable relevance threshold:

```env
MOODAPI_VECTOR__SEARCH_SCORE_THRESHOLD=0.35
```

This threshold keeps the API from returning weak matches just because they are part of the top-k result set. For example, a query about late delivery should not return an unrelated positive product sentence with a very low similarity score.

---

## Public API snapshot

Sentiment:

- `POST /api/v1/sentiment/analyze`
- `POST /api/v1/sentiment/analyze-async`
- `POST /api/v1/sentiment/analyze-batch`
- `GET /api/v1/sentiment/health`
- `GET /api/v1/sentiment/stats`

History and analytics:

- `GET /api/v1/history`
- `GET /api/v1/history/{analysis_id}`
- `DELETE /api/v1/history/{analysis_id}`
- `GET /api/v1/history/analytics`
- `GET /api/v1/history/stats`
- `GET /api/v1/analytics`
- `GET /api/v1/stats`

Auth:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

Vector search:

- `GET /api/v1/vector/health`
- `POST /api/v1/vector/search`
- `GET /api/v1/vector/search?text=...`

Health and observability:

- `GET /health`
- `GET /health/live`
- `GET /health/ready`
- `GET /health/details`
- `GET /metrics`
- `GET /metrics/app`

---

## Request examples

### Single analysis

```bash
curl -X POST "http://localhost:8000/api/v1/sentiment/analyze" \
  -H "Content-Type: application/json" \
  -d '{"text":"I really liked the experience, the support was excellent."}'
```

Example response:

```json
{
  "id": "980f2deb-6869-478b-a9e0-0921c49d203f",
  "text": "I really liked the experience, the support was excellent.",
  "sentiment": "positive",
  "confidence": 0.9827,
  "language": "en",
  "all_scores": [
    { "label": "positive", "score": 0.9827 },
    { "label": "neutral", "score": 0.0123 },
    { "label": "negative", "score": 0.0050 }
  ],
  "processing_time_ms": 128.3,
  "cached": false
}
```

### Batch analysis

```bash
curl -X POST "http://localhost:8000/api/v1/sentiment/analyze-batch" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "Excellent product.",
      "Delivery was late and support was poor.",
      "The experience was average."
    ]
  }'
```

### Async job

```bash
curl -X POST "http://localhost:8000/api/v1/sentiment/analyze-async" \
  -H "Content-Type: application/json" \
  -d '{"text":"This text should be processed outside the request cycle."}'
```

### History and analytics

```bash
curl "http://localhost:8000/api/v1/history?sentiment=positive&language=en&min_confidence=0.8"
curl "http://localhost:8000/api/v1/history/stats?period=30d&group_by=day"
curl "http://localhost:8000/api/v1/history/analytics?days=30"
```

### Semantic search

```bash
curl -X POST "http://localhost:8000/api/v1/vector/search" \
  -H "Content-Type: application/json" \
  -d '{"text":"late delivery and support problems","limit":5}'
```

---

## Prediction Audit

Each persisted prediction stores investigation context:

| Field | Meaning |
|-------|---------|
| `request_id` | request correlation identifier |
| `actor_id` | associated user or system actor |
| `model_name` | configured model used during inference |
| `model_version` | application/model version marker |
| `text_hash` | hash of the input text |
| `processing_time_ms` | service-measured latency |
| `cache_hit` | whether the result came from cache |
| `error_code` | structured error code |
| `error_message` | technical error detail |

---

## Local startup

```bash
./scripts/build.sh up
```

Surfaces:

- Client Web: `http://localhost:3000`
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Metrics: `http://localhost:8000/metrics`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001`
- RabbitMQ UI: `http://localhost:15672`
- Qdrant: `http://localhost:6333`

Development credentials:

```text
PostgreSQL: moodapi / moodapi
RabbitMQ: moodapi / moodapi
Grafana: admin / admin
```

---

## Configuration

Settings use the `MOODAPI_` prefix and `__` delimiter for nested objects.

```env
MOODAPI_DEBUG=true
MOODAPI_ENVIRONMENT=development
MOODAPI_LOG_LEVEL=INFO
MOODAPI_ML__MODEL_NAME=lxyuan/distilbert-base-multilingual-cased-sentiments-student
MOODAPI_DATABASE__URL=postgresql+psycopg2://moodapi:moodapi@localhost:5432/moodapi
MOODAPI_CACHE__URL=redis://localhost:6379/0
MOODAPI_RATE_LIMIT__ENABLED=true
MOODAPI_JWT_SECRET_KEY=change-this-local-development-secret
MOODAPI_AUTH_ENABLED=true
MOODAPI_QUEUE__ENABLED=false
MOODAPI_QUEUE__BROKER_URL=amqp://moodapi:moodapi@localhost:5672//
MOODAPI_STREAMING__ENABLED=false
MOODAPI_STREAMING__BOOTSTRAP_SERVERS=localhost:9092
MOODAPI_VECTOR__ENABLED=false
MOODAPI_VECTOR__URL=http://localhost:6333
MOODAPI_VECTOR__COLLECTION_NAME=moodapi_sentiments_v2
MOODAPI_VECTOR__EMBEDDING_MODEL_NAME=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
MOODAPI_VECTOR__SEARCH_SCORE_THRESHOLD=0.35
MOODAPI_OTEL__ENABLED=false
MOODAPI_OTEL__EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

The Docker Compose development stack enables queue, streaming, vector search and observability services.

---

## Local validation

Backend:

```bash
cd service-api/service-python
python -m ruff check app tests
python -m mypy app
python -m pytest -q
```

Client Web:

```bash
cd client-web
npm run lint
npm run build
```

Repository and infra:

```bash
./scripts/build.sh check
./scripts/test.sh all
docker compose -p moodapi -f infra/docker-compose.yml config --quiet
docker compose -p moodapi -f infra/docker-compose.prod.yml config --quiet
```

## License

MIT. See [LICENSE](LICENSE).

---

## Contact

**Thiago DI Faria** - thiagodifaria@gmail.com

[GitHub](https://github.com/thiagodifaria)  
[LinkedIn](https://linkedin.com/in/thiagodifaria)
