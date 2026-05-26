# ARQUITETURA

Este documento descreve a arquitetura, a API, o runtime local e as decisoes tecnicas do MoodAPI. Ele concentra a documentacao do projeto porque o escopo ainda e pequeno o suficiente para nao justificar varios documentos separados.

## Escopo

MoodAPI e uma plataforma de analise de sentimentos. O backend recebe textos, executa inferencia, persiste predicoes, mantem auditoria tecnica e expoe historico/analytics para o dashboard. O frontend e um console tecnico para testar a API, acompanhar logs e visualizar metricas de negocio.

## Estrutura

```text
client-web/                       frontend React
docs/                             documentacao tecnica
infra/                            runtime local e observabilidade
scripts/build.sh                  build, quality, migrations e runtime em shell
scripts/test.sh                   suites de teste em shell
service-api/service-python/       FastAPI, dominio e testes
service-api/service-postgresql/   migrations e seeds
```

## Principios

- Raiz limpa: codigo fica em `service-api/` e `client-web/`.
- Documentacao proporcional: um documento tecnico unico enquanto o projeto for compacto.
- API primeiro: OpenAPI gerado pelo FastAPI e a referencia detalhada dos endpoints.
- Operacao verificavel: health, readiness, metricas e logs fazem parte do produto.
- Auditoria de IA: predicoes devem guardar contexto tecnico suficiente para investigacao.
- Infra opcional com fallback claro: Redis e observabilidade melhoram o runtime, mas falhas devem aparecer como `degraded`, nao como sucesso falso.

## Backend

O backend fica em `service-api/service-python/` e usa FastAPI, SQLAlchemy, Pydantic v2, Redis e Transformers.

Modulos principais:

| Modulo | Responsabilidade |
|--------|------------------|
| `app/sentiment` | inferencia, schemas, rotas e persistencia de predicoes |
| `app/history` | consultas, filtros, analytics e detalhes de predicoes |
| `app/auth` | usuarios, login e JWT |
| `app/core` | database, cache, observabilidade e excecoes |
| `app/queue` | adaptador HTTP para RabbitMQ/Celery |
| `app/streaming` | consumidor Kafka/Redpanda |
| `app/vector` | busca semantica e integracao Qdrant |
| `app/workers` | tarefas Celery |
| `app/shared` | middleware, rate limit e utilitarios |

## Frontend

O frontend fica direto em `client-web/`. Ele e um dashboard tecnico para:

- executar analise individual e em lote;
- visualizar KPIs;
- consultar historico;
- inspecionar detalhes de predicoes;
- acessar configuracoes e links de operacao.

## Persistencia

PostgreSQL e o banco principal do runtime local. As migrations ficam em:

```text
service-api/service-postgresql/migrations
```

SQLite continua aceitavel para testes e fallback local simples. No runtime Docker, o Compose usa PostgreSQL.

Campos de auditoria relevantes em predicoes:

- `request_id`;
- `actor_id`;
- `model_name`;
- `model_version`;
- `text_hash`;
- `processing_time_ms`;
- `cache_hit`;
- `error_code`;
- `error_message`.

## Redis

Redis e usado para:

- cache de resultados;
- cache de consultas;
- rate limiting distribuido.
- backend de resultado para jobs assincronos.

Quando Redis estiver indisponivel, o cache e o rate limit podem cair para fallback local em memoria. Esse estado deve aparecer como degradado nos health checks.

## Filas E Streaming

RabbitMQ e Celery atendem o caminho de processamento assincrono para cargas que nao devem segurar conexao HTTP:

```text
POST /api/v1/sentiment/analyze-async
```

O endpoint publica um job na fila `sentiment.analysis`. O worker Celery executa a mesma regra de negocio do endpoint sincrono, persiste auditoria e respeita cache/modelo.

Redpanda e usado como broker Kafka local para fluxo continuo de eventos. O consumidor em `app/streaming/consumer.py` escuta:

```text
moodapi.sentiment.input
```

e publica resultados em:

```text
moodapi.sentiment.output
```

Essa camada existe para demonstrar ingestao por evento sem misturar streaming com os controllers HTTP.

## Busca Semantica

Qdrant armazena vetores das predicoes quando `MOODAPI_VECTOR__ENABLED=true`. A API exposta e:

```text
GET  /api/v1/vector/health
POST /api/v1/vector/search
GET  /api/v1/vector/search?text=...
```

O embedding atual e deterministico e leve para manter o projeto testavel localmente. Ele cria uma base tecnica clara para trocar por embeddings reais do modelo quando a feature de busca virar experiencia principal no dashboard.

## API

A API publica principal fica sob `/api/v1`.

Endpoints centrais:

```text
POST /api/v1/sentiment/analyze
POST /api/v1/sentiment/analyze-async
POST /api/v1/sentiment/analyze-batch
GET  /api/v1/sentiment/health
GET  /api/v1/history
GET  /api/v1/history/{analysis_id}
GET  /api/v1/history/analytics
GET  /api/v1/history/stats
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
GET  /api/v1/vector/health
POST /api/v1/vector/search
```

Referencia detalhada:

```text
http://localhost:8000/docs
http://localhost:8000/openapi.json
```

## Health E Observabilidade

Health:

```text
GET /health/live
GET /health/ready
GET /health/details
```

Metricas Prometheus:

```text
GET /metrics
```

Metricas JSON auxiliares:

```text
GET /metrics/app
```

O runtime local inclui:

- Prometheus em `http://localhost:9090`;
- Grafana em `http://localhost:3001`;
- OpenTelemetry Collector em `infra/otel/`.

Metricas principais:

- requests HTTP por rota/status;
- latencia HTTP;
- inferencias por sentimento;
- tempo de inferencia;
- operacoes de cache;
- memoria residente do processo;
- estado de carregamento do modelo.

## Comandos Oficiais

Runtime:

```bash
./scripts/build.sh up
./scripts/build.sh ps
./scripts/build.sh logs api
./scripts/build.sh down
```

Qualidade:

```bash
./scripts/build.sh check
```

Testes:

```bash
./scripts/test.sh unit
./scripts/test.sh web
./scripts/test.sh all
```

## Decisoes Tecnicas

| Tema | Decisao |
|------|---------|
| Estrutura | `service-api/service-python` e `client-web` sem subpasta redundante |
| Docs | documento tecnico unico enquanto o projeto for pequeno |
| Banco | PostgreSQL no runtime, SQLite em testes/fallback |
| Migrations | Alembic em `service-api/service-postgresql/migrations` |
| Cache | Redis com fallback local |
| Rate limit | Redis distribuido com fallback em memoria |
| Observabilidade | Prometheus, Grafana e OpenTelemetry |
| Validacao | Pydantic v2 com strict progressivo |
| Tipagem | MyPy progressivo |
| Filas | RabbitMQ/Celery para inferencias longas |
| Streaming | Redpanda/Kafka isolado em worker proprio |
| Vector DB | Qdrant com embedding leve e trocavel |

## Proximos Benchmarks

ONNX Runtime, TensorRT e quantizacao devem entrar apenas com benchmark antes/depois. A base ja separa inferencia, auditoria, filas e observabilidade, entao a troca do runtime do modelo pode ser feita sem alterar contratos publicos da API.
