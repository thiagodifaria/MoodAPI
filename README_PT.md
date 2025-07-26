# MoodAPI - API de Análise de Sentimentos Multilíngue

API para análise de sentimentos em textos utilizando técnicas de Processamento de Linguagem Natural (NLP) e modelos Transformer de última geração. Este projeto oferece uma solução completa para classificação emocional de textos, incluindo análise multilíngue de sentimentos básicos e detalhados de forma robusta com alta precisão, sistema de cache inteligente, analytics avançados, extração de entidades, e armazenamento de histórico.

## 🎯 Funcionalidades

- ✅ **Análise multilíngue nativa**: Suporte a português, inglês, espanhol com modelo Transformer único
- ✅ **Análise individual e em lote**: Processamento eficiente de texto único ou múltiplos textos
- ✅ **Cache inteligente**: Sistema Redis com fallback automático para alta performance
- ✅ **Histórico completo**: Armazenamento, consulta e filtros avançados de análises
- ✅ **Analytics em tempo real**: Distribuições, métricas e estatísticas agregadas
- ✅ **Rate limiting**: Controle de taxa de requisições por endpoint e IP
- ✅ **Health monitoring**: Verificação de saúde de todos os componentes
- ✅ **Containerização**: Deploy pronto com Docker e Docker Compose
- ✅ **Testes automatizados**: Cobertura completa de funcionalidades

## 🏗️ Arquitetura

Arquitetura modular com separação clara de responsabilidades:

```
app/
├── core/           # Infraestrutura (database, cache, exceptions)
├── sentiment/      # Engine ML e análise de sentimentos
├── history/        # Histórico, analytics e relatórios
└── shared/         # Middleware, rate limiting e utilitários
```

## 🔧 Stack Tecnológico

### Core
- **Python 3.10+**: Linguagem principal
- **FastAPI**: Framework web moderno com alta performance
- **Pydantic v2**: Validação de dados e configurações
- **SQLAlchemy 2.0**: ORM com nova sintaxe

### Machine Learning
- **Transformers (Hugging Face)**: Modelos Transformer multilíngues
- **cardiffnlp/twitter-roberta-base-sentiment-latest**: Modelo principal
- **LangDetect**: Detecção automática de idioma

### Infraestrutura
- **Redis**: Cache de alta performance com fallback
- **SQLite**: Desenvolvimento local
- **PostgreSQL**: Banco de dados para produção
- **Docker**: Containerização completa

### Monitoramento
- **Structured Logging**: Logs JSON estruturados
- **Health Checks**: Verificação de componentes
- **Metrics**: Tempo de resposta, cache hits, distribuições

## 📋 Pré-requisitos

- Python 3.10+
- Docker (opcional para desenvolvimento, obrigatório para produção)
- Redis (opcional, usa fallback se indisponível)

## 🚀 Instalação Rápida

### Desenvolvimento Local

```bash
# Clonar repositório
git clone https://github.com/thiagodifaria/MoodAPI.git
cd MoodAPI

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Iniciar aplicação
python -m uvicorn app.main:app --reload
```

### Com Docker (Recomendado)

```bash
# Desenvolvimento
docker-compose up --build

# Produção
docker-compose -f docker-compose.prod.yml up -d
```

## ⚙️ Configuração

### Variáveis de Ambiente

```env
# Aplicação
MOODAPI_DEBUG=true
MOODAPI_ENVIRONMENT=development

# Machine Learning
MOODAPI_ML__MODEL_NAME=cardiffnlp/twitter-roberta-base-sentiment-latest
MOODAPI_ML__MAX_TEXT_LENGTH=2000

# Database
MOODAPI_DATABASE__URL=sqlite:///./data/sentiments.db
# Produção: postgresql://user:pass@localhost:5432/moodapi

# Cache
MOODAPI_CACHE__URL=redis://localhost:6379/0
MOODAPI_CACHE__TTL=3600

# Rate Limiting
MOODAPI_RATE_LIMIT__REQUESTS_PER_MINUTE=100
MOODAPI_RATE_LIMIT__REQUESTS_PER_HOUR=1000
```

## 📊 Uso da API

### Análise Individual

```bash
curl -X POST "http://localhost:8000/api/v1/sentiment/analyze" \
     -H "Content-Type: application/json" \
     -d '{"text": "Eu amo este produto incrível!"}'
```

**Resposta:**
```json
{
  "id": "c5d3b066-013b-4a9c-baeb-5f420200f796",
  "text": "Eu amo este produto incrível!",
  "sentiment": "positive",
  "confidence": 0.9355,
  "language": "pt",
  "all_scores": [
    {"label": "positive", "score": 0.9355},
    {"label": "neutral", "score": 0.0501},
    {"label": "negative", "score": 0.0144}
  ],
  "timestamp": "2025-07-15T02:25:55.776352Z",
  "processing_time_ms": 301.1,
  "cached": false
}
```

### Análise em Lote

```bash
curl -X POST "http://localhost:8000/api/v1/sentiment/analyze-batch" \
     -H "Content-Type: application/json" \
     -d '{
       "texts": [
         "Produto excelente!",
         "Serviço terrível",
         "Experiência regular"
       ]
     }'
```

### Histórico com Filtros

```bash
# Consulta com filtros avançados
curl "http://localhost:8000/api/v1/history?sentiment=positive&language=pt&min_confidence=0.8&page=1&limit=20"

# Analytics
curl "http://localhost:8000/api/v1/analytics"

# Estatísticas agregadas
curl "http://localhost:8000/api/v1/stats?period=7d&group_by=day"
```

## 🔍 Endpoints Principais

| Endpoint | Método | Descrição | Rate Limit |
|----------|--------|-----------|-------------|
| `/api/v1/sentiment/analyze` | POST | Análise individual | 100/min |
| `/api/v1/sentiment/analyze-batch` | POST | Análise em lote | 20/min |
| `/api/v1/sentiment/health` | GET | Health check do serviço | 200/min |
| `/api/v1/history` | GET | Histórico com filtros | 60/min |
| `/api/v1/history/{id}` | GET/DELETE | Operações por ID | 100/min |
| `/api/v1/analytics` | GET | Distribuições e métricas | 20/min |
| `/api/v1/stats` | GET | Estatísticas agregadas | 15/min |

## 🧪 Testes

### Executar Testes

```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=app tests/

# Testes específicos
pytest tests/test_sentiment.py
pytest tests/test_history.py

# Verbose
pytest -v
```

### Cobertura de Testes

- ✅ Análise de sentimentos (individual e lote)
- ✅ Histórico e filtros complexos
- ✅ Analytics e estatísticas
- ✅ Rate limiting e validações
- ✅ Health checks e monitoramento
- ✅ Edge cases e error handling

## 📈 Performance

### Benchmarks Típicos

- **Análise individual**: < 100ms (cache miss), < 10ms (cache hit)
- **Análise em lote (10 textos)**: < 500ms
- **Consultas de histórico**: < 300ms (com filtros)
- **Analytics**: < 500ms (agregações complexas)
- **Cache hit rate**: > 70% em uso típico

### Otimizações

- Cache Redis com TTL inteligente
- Queries SQL otimizadas com índices
- Carregamento único de modelo ML
- Background tasks para analytics
- Connection pooling para banco

## 🐳 Deploy em Produção

### Docker Compose Produção

```bash
# Deploy completo
docker-compose -f docker-compose.prod.yml up -d

# Verificar saúde
docker-compose ps
curl http://localhost:8000/health
```

### Configuração Produção

- **Database**: PostgreSQL com connection pooling
- **Cache**: Redis com persistência
- **Workers**: Múltiplos workers Uvicorn
- **Proxy**: Nginx como reverse proxy
- **Monitoring**: Health checks e métricas
- **Security**: Rate limiting e validação rigorosa

## 📊 Monitoramento

### Health Checks

```bash
# Health geral
curl http://localhost:8000/health

# Health específico do sentiment
curl http://localhost:8000/api/v1/sentiment/health
```

### Métricas Disponíveis

- Volume de requisições por endpoint
- Tempo de resposta médio
- Taxa de cache hits/misses
- Distribuição de sentimentos
- Idiomas mais analisados
- Taxa de erro por componente

### Logs Estruturados

```json
{
  "timestamp": "2025-07-15T10:30:00Z",
  "level": "INFO",
  "message": "Request completed",
  "endpoint": "analyze",
  "status_code": 200,
  "process_time": 156.78,
  "cached": false,
  "sentiment": "positive",
  "language": "pt"
}
```

## 🔒 Segurança

- **Rate Limiting**: Proteção contra abuso por IP
- **Input Validation**: Validação rigorosa com Pydantic
- **Error Handling**: Não exposição de informações sensíveis
- **Non-root Containers**: Containers seguros
- **Resource Limits**: Limites de CPU e memória

## 📝 Documentação

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 📜 Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

## 📞 Contato

**Thiago Di Faria**
- Email: thiagodifaria@gmail.com
- GitHub: [@thiagodifaria](https://github.com/thiagodifaria)
- Projeto: [https://github.com/thiagodifaria/MoodAPI](https://github.com/thiagodifaria/MoodAPI)

---

⭐ **MoodAPI** - Análise de sentimentos com precisão multilíngue e performance otimizada. 