# MoodAPI - Sentiment Analysis Platform

MoodAPI is a complete multilingual sentiment analysis platform, developed with Python and FastAPI to provide high-precision emotional text classification. The project combines a robust sentiment analysis API based on state-of-the-art Transformer models with a modern, interactive web dashboard built in React. The architecture follows Clean Architecture principles with clear separation of responsibilities, ensuring modularity, scalability, and maintainability. The system stands out for its industrial terminal interface, real-time analytics, complete analysis history with advanced filters, and seamless integration between frontend and backend via Docker Compose.

## 🎯 Features

- ✅ **Native multilingual analysis**: Support for Portuguese, English, Spanish with single Transformer model
- ✅ **Interactive web dashboard**: Modern industrial interface with metrics, charts, and real-time visualizations
- ✅ **Individual and batch analysis**: Efficient processing of single or multiple texts
- ✅ **Smart caching**: Redis system with automatic fallback for high performance
- ✅ **Complete history**: Storage, querying, and advanced filtering of analyses
- ✅ **Real-time analytics**: Distributions, metrics, and aggregated statistics
- ✅ **Rate limiting**: Request rate control per endpoint and IP
- ✅ **Health monitoring**: Health verification of all components
- ✅ **Containerization**: Production-ready deployment with Docker and Docker Compose
- ✅ **Details modal**: Complete visualization of each analysis with detailed scores
- ✅ **Quick examples**: Sample texts in multiple languages for immediate testing
- ✅ **Flexible configuration**: Example and settings management via interface

## 🔧 Technologies

### Backend - Core
- **Python 3.10+**: Main language with modern async/await patterns
- **FastAPI**: Modern web framework with high performance and automatic documentation
- **Pydantic v2**: Data validation, serialization, and configuration management
- **SQLAlchemy 2.0**: ORM with new syntax and async support

### Backend - Machine Learning
- **Transformers (Hugging Face)**: State-of-the-art multilingual Transformer models
- **cardiffnlp/twitter-roberta-base-sentiment-latest**: Main analysis model
- **LangDetect**: Automatic language detection

### Backend - Infrastructure
- **Redis**: High-performance cache with automatic fallback
- **SQLite/PostgreSQL**: Data persistence with multiple database support
- **Docker/Docker Compose**: Complete stack containerization

### Frontend
- **React 18+**: Modern library for user interfaces
- **TypeScript**: Static typing for safer code
- **TailwindCSS**: Utility CSS framework for styling
- **Recharts**: Responsive chart library
- **Lucide React**: Modern and consistent icons
- **Axios**: HTTP client for API communication
- **Vite**: Modern and fast build tool

## 📈 Architecture

### Backend Structure

```
app/
├── core/           # Infrastructure (database, cache, exceptions)
├── sentiment/      # ML engine and sentiment analysis
├── history/        # History, analytics, and reports
└── shared/         # Middleware, rate limiting, and utilities
```

### Frontend Structure

```
frontend/
├── src/
│   ├── components/    # Reusable components (Cards, Sidebar, Modal)
│   ├── pages/         # Application pages (Dashboard, Analysis, Logs)
│   ├── services/      # API services and communication
│   └── types/         # TypeScript types
└── public/            # Static assets
```

### Data Flow

```
User (Web Dashboard)
    ↓
React Frontend (TailwindCSS + TypeScript)
    ↓
API Client (Axios)
    ↓
FastAPI Backend
    ↓
Services (Sentiment Analysis, History, Cache)
    ↓
Persistence (SQLite/PostgreSQL + Redis)
```

## 🖥️ Dashboard Interface

### Main Dashboard
The dashboard presents a complete system overview with:
- **Real-time KPIs**: Total analyses, average confidence, high confidence rate
- **Interactive charts**: Confidence history and sentiment distribution
- **Recent analyses table**: Quick view of latest analyses with detail access

### Analysis Page
Dedicated interface for performing new analyses with:
- **Free text input**: Expandable text field for individual analysis
- **Quick examples**: Sample texts in Portuguese and English for immediate testing
- **Batch mode**: Support for analyzing multiple texts simultaneously
- **Detailed results**: Complete scores for each sentiment category

### Logs & History
Complete analysis history management:
- **Advanced filters**: By sentiment, language, period, and text search
- **Pagination**: Efficient navigation through large data volumes
- **Individual actions**: Detail viewing and record deletion
- **Details modal**: Complete text, metadata, and scores when clicking any item

### Settings
System settings panel:
- **Model status**: Information about loaded ML model
- **Example management**: Add, edit, and remove sample texts
- **Documentation links**: Direct access to Swagger UI and ReDoc

### About
Page with project information:
- **Project description**: Purpose and features
- **Technology stack**: Technologies used in backend and frontend
- **Author and contact**: Contact information and relevant links

## 📷 Screenshots

### Dashboard - Overview with KPIs and Charts
![Dashboard](public/dashboard.png)

### Analysis - Sentiment Analysis Interface
![Analysis](public/analysis.png)

### Logs & History - Analysis Management
![Logs](public/logs.png)

### Settings - Configuration Panel
![Settings](public/config.png)

### About - Project Information
![About](public/about.png)

## 📋 Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend development)
- Docker & Docker Compose (recommended)
- Redis (optional, uses fallback if unavailable)

## 🚀 Quick Start

### With Docker Compose (Recommended)

```bash
# Clone repository
git clone https://github.com/thiagodifaria/MoodAPI.git
cd MoodAPI

# Start all services
cd dockerfile
docker compose up --build

# Access application
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

### Local Development

```bash
# Backend
cd MoodAPI
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
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
     -d '{"text": "I love this amazing product!"}'
```

**Response:**
```json
{
  "id": "c5d3b066-013b-4a9c-baeb-5f420200f796",
  "text": "I love this amazing product!",
  "sentiment": "positive",
  "confidence": 0.9355,
  "language": "en",
  "all_scores": [
    {"label": "positive", "score": 0.9355},
    {"label": "neutral", "score": 0.0501},
    {"label": "negative", "score": 0.0144}
  ],
  "processing_time_ms": 156.2
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
         "Average experience"
       ]
     }'
```

### History with Filters

```bash
# Query with advanced filters
curl "http://localhost:8000/api/v1/history?sentiment=positive&language=en&min_confidence=0.8"

# Aggregated statistics
curl "http://localhost:8000/api/v1/history/stats?period=7d"
```

## 🔍 Main Endpoints

| Endpoint | Method | Description | Rate Limit |
|----------|--------|-------------|-------------|
| `/api/v1/sentiment/analyze` | POST | Individual analysis | 100/min |
| `/api/v1/sentiment/analyze-batch` | POST | Batch analysis | 20/min |
| `/api/v1/sentiment/health` | GET | Service health check | 200/min |
| `/api/v1/history` | GET | History with filters | 60/min |
| `/api/v1/history/{id}` | GET/DELETE | Operations by ID | 100/min |
| `/api/v1/history/analytics` | GET | Distributions and metrics | 20/min |
| `/api/v1/history/stats` | GET | Aggregated statistics | 15/min |

## 📈 Performance

### Typical Benchmarks

- **Individual analysis**: < 100ms (cache miss), < 10ms (cache hit)
- **Batch analysis (10 texts)**: < 500ms
- **History queries**: < 300ms (with filters)
- **Analytics**: < 500ms (complex aggregations)
- **Cache hit rate**: > 70% in typical usage

### Optimizations

- Redis cache with smart TTL
- Optimized SQL queries with indexes
- Single ML model loading
- Background tasks for analytics
- Connection pooling for database

## 🐳 Production Deployment

### Docker Compose

```bash
# Full deployment
cd dockerfile
docker compose up -d

# Check health
docker compose ps
curl http://localhost:8000/api/v1/sentiment/health
```

### Included Services

- **moodapi-api**: FastAPI backend with ML model
- **moodapi-frontend**: React dashboard with Nginx
- **moodapi-db**: PostgreSQL for persistence
- **moodapi-redis**: Redis for caching

## 📝 Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📞 Contact

**Thiago Di Faria**
- Email: thiagodifaria@gmail.com
- Website: [thiagodifaria.com](https://thiagodifaria.com)
- GitHub: [@thiagodifaria](https://github.com/thiagodifaria)
- Project: [https://github.com/thiagodifaria/MoodAPI](https://github.com/thiagodifaria/MoodAPI)

---

⭐ **MoodAPI** - Multilingual sentiment analysis with precision, interactive dashboard, and optimized performance.