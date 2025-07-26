# MoodAPI

![MoodAPI Logo](https://img.shields.io/badge/MoodAPI-Sentiment%20Analysis-purple?style=for-the-badge&logo=brain)

**Advanced Multilingual Sentiment Analysis API**

[![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Transformers](https://img.shields.io/badge/🤗_Transformers-Latest-yellow?style=flat)](https://huggingface.co/transformers)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ed?style=flat&logo=docker&logoColor=white)](https://docker.com)

---

## 🌍 **Documentation / Documentação**

**📖 [🇺🇸 Read in English](README_EN.md)**  
**📖 [🇧🇷 Leia em Português](README_PT.md)**

---

## 🎯 What is MoodAPI?

MoodAPI is a **production-ready sentiment analysis API** that leverages state-of-the-art **Transformer models** to provide accurate, multilingual sentiment classification. Built with **FastAPI** and designed for high-performance applications.

### ⚡ Key Highlights

- 🌍 **Multilingual Native Support** - Portuguese, English, Spanish with single unified model
- 🚀 **High Performance** - Redis caching, optimized queries, < 100ms response time
- 📊 **Advanced Analytics** - Real-time statistics, distributions, and aggregated metrics
- 🔄 **Batch Processing** - Analyze multiple texts efficiently in a single request
- 📈 **Complete History** - Store, query, and filter all analysis results
- 🛡️ **Production Ready** - Rate limiting, health checks, structured logging
- 🐳 **Easy Deployment** - Docker Compose setup with Redis and PostgreSQL
- 📚 **Auto Documentation** - Interactive Swagger UI and ReDoc

### 🏆 What Makes It Special?

```
✅ 93%+ accuracy with Transformer models
✅ Intelligent caching with Redis fallback
✅ Comprehensive rate limiting by endpoint
✅ Advanced filtering and search capabilities
✅ Real-time analytics and monitoring
✅ Modular architecture with clear separation
```

---

## ⚡ Quick Start

### Option 1: Docker Compose (Recommended)
```bash
# Clone and run with all services
git clone https://github.com/thiagodifaria/MoodAPI.git
cd MoodAPI
docker-compose up --build

# API available at: http://localhost:8000
# Docs available at: http://localhost:8000/docs
```

### Option 2: Local Development
```bash
git clone https://github.com/thiagodifaria/MoodAPI.git
cd MoodAPI
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 🔥 Test It Now!
```bash
# Analyze sentiment
curl -X POST "http://localhost:8000/api/v1/sentiment/analyze" \
     -H "Content-Type: application/json" \
     -d '{"text": "I love this amazing product!"}'

# Response:
# {
#   "sentiment": "positive",
#   "confidence": 0.9355,
#   "language": "en",
#   "processing_time_ms": 89.2
# }
```

---

## 🔍 API Overview

| Feature | Endpoint | Description |
|---------|----------|-------------|
| 🎯 **Individual Analysis** | `POST /api/v1/sentiment/analyze` | Analyze single text |
| 📦 **Batch Analysis** | `POST /api/v1/sentiment/analyze-batch` | Analyze multiple texts |
| 📊 **Analytics** | `GET /api/v1/analytics` | Get distributions and metrics |
| 📈 **Statistics** | `GET /api/v1/stats` | Aggregated stats with time filters |
| 📋 **History** | `GET /api/v1/history` | Query with advanced filters |
| 🏥 **Health Check** | `GET /health` | Service health monitoring |

---

## 📞 Contact

**Thiago Di Faria** - thiagodifaria@gmail.com

[![GitHub](https://img.shields.io/badge/GitHub-@thiagodifaria-black?style=flat&logo=github)](https://github.com/thiagodifaria)

---

### 🌟 **Star this project if you find it useful!**

**Made with ❤️ by [Thiago Di Faria](https://github.com/thiagodifaria)** 