# MoodAPI

![MoodAPI](https://img.shields.io/badge/MoodAPI-API-111827?style=for-the-badge&logo=fastapi&logoColor=white)

**API de inteligencia de sentimentos com FastAPI, React, inferencia Transformer, auditoria de predicoes, filas assincronas, streaming de eventos, busca semantica e observabilidade local**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-core%20api-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-client%20web-61DAFB?style=flat&logo=react&logoColor=111827)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-historico%20auditavel-4169E1?style=flat&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-cache%20%2B%20rate%20limit-DC382D?style=flat&logo=redis&logoColor=white)](https://redis.io)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-Celery%20jobs-FF6600?style=flat&logo=rabbitmq&logoColor=white)](https://rabbitmq.com)
[![Qdrant](https://img.shields.io/badge/Qdrant-busca%20vetorial-DC244C?style=flat)](https://qdrant.tech)
[![Docker](https://img.shields.io/badge/Docker-stack%20local-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-success?style=flat)](LICENSE)

---

## Documentacao

**Repositorio:** [thiagodifaria/MoodAPI](https://github.com/thiagodifaria/MoodAPI)  
**Visao geral resumida:** [README.md](README.md)  
**Read in English:** [README_EN.md](README_EN.md)  
**Referencia de arquitetura:** [docs/ARQUITETURA.md](docs/ARQUITETURA.md)

---

## Screenshots

### Analise Individual

![MoodAPI analise individual](client-web/public/images/screenshots/single-analysis.png)

### Analise em Lote

![MoodAPI analise em lote](client-web/public/images/screenshots/batch-analysis.png)

### Historico de Predicoes

![MoodAPI historico de predicoes](client-web/public/images/screenshots/history.png)

### Busca Semantica

![MoodAPI busca semantica](client-web/public/images/screenshots/semantic-search.png)

### Health Check

![MoodAPI health check](client-web/public/images/screenshots/health.png)

---

## O que e o MoodAPI?

MoodAPI e um servico backend-first de IA para analise de sentimentos. Ele expoe uma API HTTP versionada, executa inferencia multilingual com Transformer, armazena cada predicao para auditoria/historico, indexa registros em banco vetorial e entrega um client web React para operar e validar o sistema.

O projeto nao e uma demo de um endpoint unico. Ele e um servico compacto desenhado para mostrar decisoes maduras em escopo proporcional: validacao forte de entrada, runtime previsivel, separacao entre backend e frontend, migrations de banco, cache, rate limiting, jobs assincronos, streaming de eventos, busca semantica, metricas, health checks e observabilidade local.

O frontend e um console tecnico. Ele existe para exercitar a API real: inferencia individual, inferencia em lote, historico persistido, busca semantica e inspecao de saude dos componentes. A API continua sendo a superficie principal do produto.

---

## Capacidades implementadas

O projeto inclui:

- API HTTP sob `/api/v1`.
- Swagger/OpenAPI disponivel em `/docs`.
- Health, readiness, details e metrics em rotas publicas.
- Analise individual de sentimentos.
- Analise de sentimentos em lote.
- Submissao assincrona com RabbitMQ/Celery.
- Consumidor de streaming compativel com Redpanda/Kafka.
- Persistencia PostgreSQL para historico e auditoria de predicoes.
- Cache Redis para resultados de inferencia.
- Rate limiting com Redis e fallback local.
- Integracao com Qdrant como banco vetorial.
- Embeddings multilingual para busca semantica.
- Corte minimo de relevancia para evitar resultados fracos.
- Backfill automatico do historico para o Qdrant quando a colecao vetorial esta vazia.
- Endpoints de autenticacao JWT.
- Client web React para testar endpoints reais.
- Endpoint de metricas Prometheus.
- Provisionamento Grafana.
- Integracao com OpenTelemetry Collector.
- Scripts Bash para build e testes.

---

## Por que o projeto existe

MoodAPI existe como referencia tecnica para transformar inferencia de IA em uma superficie completa de aplicacao. A ideia central e que um servico util de IA precisa de mais do que uma chamada de modelo: precisa de validacao, auditoria, persistencia, observabilidade, feedback operacional, cache, lote, caminhos assincronos e uma forma clara de inspecionar predicoes historicas.

A arquitetura e organizada em torno de fronteiras claras de engenharia:

- schemas de request sao explicitos;
- configuracao de runtime e centralizada;
- migrations de banco sao versionadas;
- predicoes sao persistidas com metadados de modelo;
- resultados cacheados consideram texto e identidade do modelo;
- busca semantica usa Qdrant em vez de filtro em memoria;
- filas e streaming ficam separados do HTTP sincrono;
- observabilidade local existe com Prometheus/Grafana/OTel.

---

## Arquitetura em alto nivel

```text
React client-web
    |
    | HTTP via proxy Nginx
    v
FastAPI
    |
    +--> Sentiment service -> Transformer pipeline
    +--> History service   -> PostgreSQL
    +--> Cache/rate limit  -> Redis
    +--> Vector indexing   -> Qdrant
    +--> Metrics/traces    -> Prometheus / OpenTelemetry

Fluxo assincrono:
FastAPI -> RabbitMQ -> Celery worker -> Sentiment service -> PostgreSQL/Qdrant

Fluxo de eventos:
Topico Redpanda -> stream worker -> Sentiment service -> topico de saida Redpanda

Fluxo semantico:
Registro historico -> embedding multilingual -> Qdrant -> resultados filtrados por score
```

---

## Estrutura do repositorio

| Area | Caminho | Responsabilidade |
|------|---------|------------------|
| API service | `service-api/service-python` | app FastAPI, modulos de dominio, inferencia, testes e config Python |
| Database | `service-api/service-postgresql` | migrations Alembic e artefatos de banco |
| Client Web | `client-web` | console tecnico React/Vite e screenshots publicos |
| Infra | `infra` | Docker Compose, Prometheus, Grafana e OpenTelemetry |
| Scripts | `scripts` | entrypoints Bash para build, runtime e testes |
| Docs | `docs` | referencia focada de arquitetura |

A raiz fica intencionalmente reservada para arquivos de entrada: READMEs, licenca, exemplo de ambiente e diretorios principais. A implementacao backend fica em `service-api`, enquanto `client-web` e a raiz do frontend.

---

## Stack e racional tecnico

| Tecnologia | Uso | Motivo |
|------------|-----|--------|
| Python | Core API | Ecossistema maduro para IA/ML e integracao direta com Hugging Face |
| FastAPI | Camada HTTP | Requests/responses tipados, OpenAPI e injecao de dependencias |
| Pydantic v2 | Validacao/config | Schemas estritos e carregamento previsivel de configuracao |
| Transformers | Inferencia | Pipeline Transformer multilingual para classificacao de sentimento |
| PostgreSQL | Auditoria/historico | Armazenamento duravel de predicoes, filtros e analytics |
| Alembic | Migrations | Evolucao versionada do schema |
| Redis | Cache/rate limit | Cache rapido de resultados e controle distribuido de requisicoes |
| RabbitMQ | Jobs assincronos | Processamento fora do caminho da request |
| Celery | Workers | Modelo simples de workers Python para analise enfileirada |
| Redpanda | Streaming | Pipeline local compativel com Kafka |
| Qdrant | Busca vetorial | Recuperacao semantica sobre predicoes persistidas |
| React/Vite | Client web | Console tecnico rapido para operar a API |
| Prometheus | Metrics | Sinais operacionais por rota e dominio |
| Grafana | Dashboards | Visualizacao operacional local |
| OpenTelemetry | Tracing | Correlacao entre requests e componentes |
| Docker Compose | Runtime | Stack local reproduzivel com dependencias completas |

---

## Modulos do backend

| Modulo | Responsabilidade |
|--------|------------------|
| `app/main.py` | bootstrap FastAPI, lifecycle, routers, health e metrics |
| `app/config.py` | settings Pydantic para banco, cache, modelo, filas, streaming, vetores e telemetria |
| `app/sentiment` | orquestracao de inferencia, schemas, rotas, persistencia e hooks de indexacao vetorial |
| `app/history` | historico de predicoes, analytics, filtros, stats e detalhe |
| `app/auth` | usuario, hash de senha, login e JWT |
| `app/core` | engine de banco, cache Redis, excecoes, seguranca e observabilidade |
| `app/shared` | middleware, correlation id, handlers de erro e rate limiting |
| `app/queue` | adaptador de submissao RabbitMQ/Celery |
| `app/workers` | app Celery e tarefas em background |
| `app/streaming` | consumidor Redpanda/Kafka para analise orientada a eventos |
| `app/vector` | Qdrant, embeddings multilingual, threshold de busca e health vetorial |

---

## Inferencia de sentimento

O modelo default configurado para sentimento e:

```text
lxyuan/distilbert-base-multilingual-cased-sentiments-student
```

Esse modelo foi escolhido porque a aplicacao precisa de comportamento pratico em portugues e em cenarios multilingual. A API persiste o nome do modelo em cada predicao, permitindo auditoria depois de mudancas de modelo.

As chaves de cache incluem o texto normalizado e a identidade do modelo. Isso evita reaproveitar classificacoes antigas depois de upgrade do modelo.

---

## Busca semantica

A busca semantica usa Qdrant e embeddings multilingual:

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

A colecao vetorial armazena texto da predicao, sentimento, confianca, idioma e metadados de modelo. As buscas usam similaridade cosseno e um corte configuravel de relevancia:

```env
MOODAPI_VECTOR__SEARCH_SCORE_THRESHOLD=0.35
```

Esse corte impede que a API retorne resultados fracos apenas porque eles aparecem no top-k. Por exemplo, uma query sobre entrega atrasada nao deve retornar uma frase positiva sobre produto excelente com score muito baixo.

---

## API snapshot

Sentimentos:

- `POST /api/v1/sentiment/analyze`
- `POST /api/v1/sentiment/analyze-async`
- `POST /api/v1/sentiment/analyze-batch`
- `GET /api/v1/sentiment/health`
- `GET /api/v1/sentiment/stats`

Historico e analytics:

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

Busca vetorial:

- `GET /api/v1/vector/health`
- `POST /api/v1/vector/search`
- `GET /api/v1/vector/search?text=...`

Health e observabilidade:

- `GET /health`
- `GET /health/live`
- `GET /health/ready`
- `GET /health/details`
- `GET /metrics`
- `GET /metrics/app`

---

## Exemplos de requisicao

### Analise individual

```bash
curl -X POST "http://localhost:8000/api/v1/sentiment/analyze" \
  -H "Content-Type: application/json" \
  -d '{"text":"Eu gostei muito da experiencia, o atendimento foi excelente."}'
```

Resposta exemplo:

```json
{
  "id": "980f2deb-6869-478b-a9e0-0921c49d203f",
  "text": "Eu gostei muito da experiencia, o atendimento foi excelente.",
  "sentiment": "positive",
  "confidence": 0.9827,
  "language": "pt",
  "all_scores": [
    { "label": "positive", "score": 0.9827 },
    { "label": "neutral", "score": 0.0123 },
    { "label": "negative", "score": 0.0050 }
  ],
  "processing_time_ms": 128.3,
  "cached": false
}
```

### Analise em lote

```bash
curl -X POST "http://localhost:8000/api/v1/sentiment/analyze-batch" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "Produto excelente.",
      "A entrega atrasou e o suporte foi ruim.",
      "A experiencia foi normal."
    ]
  }'
```

### Job assincrono

```bash
curl -X POST "http://localhost:8000/api/v1/sentiment/analyze-async" \
  -H "Content-Type: application/json" \
  -d '{"text":"Este texto deve ser processado fora do ciclo da requisicao."}'
```

### Historico e analytics

```bash
curl "http://localhost:8000/api/v1/history?sentiment=positive&language=pt&min_confidence=0.8"
curl "http://localhost:8000/api/v1/history/stats?period=30d&group_by=day"
curl "http://localhost:8000/api/v1/history/analytics?days=30"
```

### Busca semantica

```bash
curl -X POST "http://localhost:8000/api/v1/vector/search" \
  -H "Content-Type: application/json" \
  -d '{"text":"problemas com entrega atrasada e suporte","limit":5}'
```

---

## Auditoria de predicoes

Cada predicao persistida guarda contexto para investigacao:

| Campo | Significado |
|-------|-------------|
| `request_id` | identificador de correlacao da requisicao |
| `actor_id` | usuario ou ator de sistema associado |
| `model_name` | modelo configurado usado na inferencia |
| `model_version` | marcador de versao da aplicacao/modelo |
| `text_hash` | hash do texto de entrada |
| `processing_time_ms` | latencia medida pelo servico |
| `cache_hit` | indica se o resultado veio de cache |
| `error_code` | codigo estruturado de erro |
| `error_message` | detalhe tecnico do erro |

---

## Como iniciar localmente

```bash
./scripts/build.sh up
```

Superficies:

- Client Web: `http://localhost:3000`
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Metrics: `http://localhost:8000/metrics`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001`
- RabbitMQ UI: `http://localhost:15672`
- Qdrant: `http://localhost:6333`

Credenciais de desenvolvimento:

```text
PostgreSQL: moodapi / moodapi
RabbitMQ: moodapi / moodapi
Grafana: admin / admin
```

---

## Configuracao

As settings usam prefixo `MOODAPI_` e delimitador `__` para objetos aninhados.

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

A stack de desenvolvimento em Docker Compose habilita filas, streaming, busca vetorial e observabilidade.

---

## Validacao local

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

Repositorio e infra:

```bash
./scripts/build.sh check
./scripts/test.sh all
docker compose -p moodapi -f infra/docker-compose.yml config --quiet
docker compose -p moodapi -f infra/docker-compose.prod.yml config --quiet
```

## Licenca

MIT. Veja [LICENSE](LICENSE).

---

## Contato

**Thiago DI Faria** - thiagodifaria@gmail.com

[GitHub](https://github.com/thiagodifaria)  
[LinkedIn](https://linkedin.com/in/thiagodifaria)
