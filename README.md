# MoodAPI

![MoodAPI](https://img.shields.io/badge/MoodAPI-Sentiment%20Intelligence-111827?style=for-the-badge&logo=fastapi&logoColor=white)

**Production-minded sentiment intelligence platform with Transformer inference, auditable prediction history, async processing, event streaming, semantic search and local observability.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-client%20web-61DAFB?style=flat&logo=react&logoColor=111827)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-audit%20storage-4169E1?style=flat&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-cache%20%2B%20rate%20limit-DC382D?style=flat&logo=redis&logoColor=white)](https://redis.io)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-async%20jobs-FF6600?style=flat&logo=rabbitmq&logoColor=white)](https://rabbitmq.com)
[![Qdrant](https://img.shields.io/badge/Qdrant-semantic%20search-DC244C?style=flat)](https://qdrant.tech)
[![License](https://img.shields.io/badge/License-MIT-success?style=flat)](LICENSE)

---

## Documentation / Documentacao

**Repository:** [thiagodifaria/MoodAPI](https://github.com/thiagodifaria/MoodAPI)  
**Leia em Portugues:** [README_PT.md](README_PT.md)  
**Read the detailed English README:** [README_EN.md](README_EN.md)  
**Architecture:** [docs/ARQUITETURA.md](docs/ARQUITETURA.md)

---

## Visual Preview

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

MoodAPI is a compact AI platform shaped like a real backend product. It receives text, runs multilingual sentiment inference, persists predictions for audit/history, indexes records for semantic search and exposes a React technical console for validating the API.

The project is intentionally organized as a portfolio-grade service: the root stays clean, backend code lives under `service-api/`, frontend code lives under `client-web/`, infrastructure lives under `infra/`, and database assets stay separated by technology.

---

## Highlights

- FastAPI backend with Pydantic v2 validation.
- React/Vite technical console for real endpoint testing.
- Hugging Face Transformer sentiment inference.
- PostgreSQL audit/history storage.
- Redis cache and rate limiting.
- RabbitMQ/Celery asynchronous jobs.
- Redpanda/Kafka-compatible event streaming.
- Qdrant semantic search with multilingual embeddings.
- Prometheus, Grafana and OpenTelemetry local observability.
- Bash scripts for build and test workflows.

---

## Quick Start

```bash
./scripts/build.sh up
```

Useful local URLs:

| Surface | URL |
|---------|-----|
| Client Web | `http://localhost:3000` |
| API | `http://localhost:8000` |
| Swagger | `http://localhost:8000/docs` |
| Metrics | `http://localhost:8000/metrics` |
| Prometheus | `http://localhost:9090` |
| Grafana | `http://localhost:3001` |
| RabbitMQ UI | `http://localhost:15672` |
| Qdrant | `http://localhost:6333` |

---

## Validation

```bash
./scripts/build.sh check
./scripts/test.sh all
```

The validation flow covers backend linting, typing, tests, frontend build and Docker Compose configuration.

---

## Contact

**Thiago DI Faria** - thiagodifaria@gmail.com

[![GitHub](https://img.shields.io/badge/GitHub-@thiagodifaria-black?style=flat&logo=github)](https://github.com/thiagodifaria)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Thiago_DI_Faria-blue?style=flat&logo=linkedin)](https://linkedin.com/in/thiagodifaria)

---

## License

Licensed under the [MIT License](LICENSE).
