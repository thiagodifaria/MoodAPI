# MoodAPI - Multilingual Sentiment Analysis API

API for sentiment analysis in texts using Natural Language Processing (NLP) techniques and state-of-the-art Transformer models. This project offers a complete solution for emotional classification of texts, including robust multilingual analysis of basic and detailed sentiments with high precision, intelligent cache system, advanced analytics, entity extraction, and history storage.

## 🎯 Features

- ✅ **Native multilingual analysis**: Support for Portuguese, English, Spanish with single Transformer model
- ✅ **Individual and batch analysis**: Efficient processing of single text or multiple texts
- ✅ **Intelligent cache**: Redis system with automatic fallback for high performance
- ✅ **Complete history**: Storage, queries and advanced filters for analyses
- ✅ **Real-time analytics**: Distributions, metrics and aggregated statistics
- ✅ **Rate limiting**: Request rate control per endpoint and IP
- ✅ **Health monitoring**: Health check for all components
- ✅ **Containerization**: Ready deployment with Docker and Docker Compose
- ✅ **Automated tests**: Complete functionality coverage

## 🏗️ Architecture

Modular architecture with clear separation of responsibilities:

```
app/
├── core/           # Infrastructure (database, cache, exceptions)
├── sentiment/      # ML Engine and sentiment analysis
├── history/        # History, analytics and reports
└── shared/         # Middleware, rate limiting and utilities
```

## 🔧 Technology Stack

### Core
- **Python 3.10+**: Main language
- **FastAPI**: Modern web framework with high performance
- **Pydantic v2**: Data validation and configurations
- **SQLAlchemy 2.0**: ORM with new syntax

### Machine Learning
- **Transformers (Hugging Face)**: Multilingual Transformer models
- **cardiffnlp/twitter-roberta-base-sentiment-latest**: Main model
- **LangDetect**: Automatic language detection

### Infrastructure
- **Redis**: High performance cache with fallback
- **SQLite**: Local development
- **PostgreSQL**: Production database
- **Docker**: Complete containerization

### Monitoring
- **Structured Logging**: Structured JSON logs
- **Health Checks**: Component verification
- **Metrics**: Response time, cache hits, distributions

## 📋 Prerequisites

- Python 3.10+
- Docker (optional for development, required for production)
- Redis (optional, uses fallback if unavailable)

## 🚀 Quick Installation

### Local Development

```bash
# Clone repository
git clone https://github.com/thiagodifaria/MoodAPI.git
cd MoodAPI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Start application
python -m uvicorn app.main:app --reload
```

### With Docker (Recommended)

```bash
# Development
docker-compose up --build

# Production
docker-compose -f docker-compose.prod.yml up -d
```

## ⚙️ Configuration

### Environment Variables

```env
# Application
MOODAPI_DEBUG=true
MOODAPI_ENVIRONMENT=development

# Machine Learning
MOODAPI_ML__MODEL_NAME=cardiffnlp/twitter-roberta-base-sentiment-latest
MOODAPI_ML__MAX_TEXT_LENGTH=2000

# Database
MOODAPI_DATABASE__URL=sqlite:///./data/sentiments.db
# Production: postgresql://user:pass@localhost:5432/moodapi

# Cache
MOODAPI_CACHE__URL=redis://localhost:6379/0
MOODAPI_CACHE__TTL=3600

# Rate Limiting
MOODAPI_RATE_LIMIT__REQUESTS_PER_MINUTE=100
MOODAPI_RATE_LIMIT__REQUESTS_PER_HOUR=1000
```

## 📊 API Usage

### Individual Analysis

```bash
curl -X POST "http://localhost:8000/api/v1/sentiment/analyze" \
     -H "Content-Type: application/json" \
     -d '{"text": "I love this incredible product!"}'
```

**Response:**
```json
{
  "id": "c5d3b066-013b-4a9c-baeb-5f420200f796",
  "text": "I love this incredible product!",
  "sentiment": "positive",
  "confidence": 0.9355,
  "language": "en",
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

### Batch Analysis

```bash
curl -X POST "http://localhost:8000/api/v1/sentiment/analyze-batch" \
     -H "Content-Type: application/json" \
     -d '{
       "texts": [
         "Excellent product!",
         "Terrible service",
         "Regular experience"
       ]
     }'
```

### History with Filters

```bash
# Query with advanced filters
curl "http://localhost:8000/api/v1/history?sentiment=positive&language=en&min_confidence=0.8&page=1&limit=20"

# Analytics
curl "http://localhost:8000/api/v1/analytics"

# Aggregated statistics
curl "http://localhost:8000/api/v1/stats?period=7d&group_by=day"
```

## 🔍 Main Endpoints

| Endpoint | Method | Description | Rate Limit |
|----------|--------|-------------|-------------|
| `/api/v1/sentiment/analyze` | POST | Individual analysis | 100/min |
| `/api/v1/sentiment/analyze-batch` | POST | Batch analysis | 20/min |
| `/api/v1/sentiment/health` | GET | Service health check | 200/min |
| `/api/v1/history` | GET | History with filters | 60/min |
| `/api/v1/history/{id}` | GET/DELETE | Operations by ID | 100/min |
| `/api/v1/analytics` | GET | Distributions and metrics | 20/min |
| `/api/v1/stats` | GET | Aggregated statistics | 15/min |

## 🧪 Tests

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=app tests/

# Specific tests
pytest tests/test_sentiment.py
pytest tests/test_history.py

# Verbose
pytest -v
```

### Test Coverage

- ✅ Sentiment analysis (individual and batch)
- ✅ History and complex filters
- ✅ Analytics and statistics
- ✅ Rate limiting and validations
- ✅ Health checks and monitoring
- ✅ Edge cases and error handling

## 📈 Performance

### Typical Benchmarks

- **Individual analysis**: < 100ms (cache miss), < 10ms (cache hit)
- **Batch analysis (10 texts)**: < 500ms
- **History queries**: < 300ms (with filters)
- **Analytics**: < 500ms (complex aggregations)
- **Cache hit rate**: > 70% in typical usage

### Optimizations

- Redis cache with intelligent TTL
- Optimized SQL queries with indexes
- Single ML model loading
- Background tasks for analytics
- Connection pooling for database

## 🐳 Production Deploy

### Production Docker Compose

```bash
# Complete deploy
docker-compose -f docker-compose.prod.yml up -d

# Check health
docker-compose ps
curl http://localhost:8000/health
```

### Production Configuration

- **Database**: PostgreSQL with connection pooling
- **Cache**: Redis with persistence
- **Workers**: Multiple Uvicorn workers
- **Proxy**: Nginx as reverse proxy
- **Monitoring**: Health checks and metrics
- **Security**: Rate limiting and strict validation

## 📊 Monitoring

### Health Checks

```bash
# General health
curl http://localhost:8000/health

# Sentiment specific health
curl http://localhost:8000/api/v1/sentiment/health
```

### Available Metrics

- Request volume per endpoint
- Average response time
- Cache hits/misses rate
- Sentiment distribution
- Most analyzed languages
- Error rate per component

### Structured Logs

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
  "language": "en"
}
```

## 🔒 Security

- **Rate Limiting**: Protection against abuse by IP
- **Input Validation**: Strict validation with Pydantic
- **Error Handling**: No exposure of sensitive information
- **Non-root Containers**: Secure containers
- **Resource Limits**: CPU and memory limits

## 📝 Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📞 Contact

**Thiago Di Faria**
- Email: thiagodifaria@gmail.com
- GitHub: [@thiagodifaria](https://github.com/thiagodifaria)
- Project: [https://github.com/thiagodifaria/MoodAPI](https://github.com/thiagodifaria/MoodAPI)

---

⭐ **MoodAPI** - Sentiment analysis with multilingual precision and optimized performance. 