import asyncio
import os
import tempfile
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import Settings, get_settings
from app.core.database import Base
from app.dependencies import get_cache_dependency, get_db_session
from app.main import app
from app.sentiment.analyzer import SentimentAnalyzer
from app.sentiment.models import SentimentAnalysis


# CONFIGURAÇÕES DE TESTE

@pytest.fixture(scope="session")
def test_settings():
    """Configurações otimizadas para ambiente de teste."""
    test_data_dir = tempfile.mkdtemp(prefix="moodapi_test_")
    test_db_path = os.path.join(test_data_dir, "test.db")
    
    # Override configurações para teste
    test_env = {
        "MOODAPI_DEBUG": "true",
        "MOODAPI_ENVIRONMENT": "development",
        "MOODAPI_DATABASE__URL": f"sqlite:///{test_db_path}",
        "MOODAPI_DATABASE__ECHO": "false",
        "MOODAPI_RATE_LIMIT__ENABLED": "false",
        "MOODAPI_LOG_LEVEL": "WARNING"
    }
    
    for key, value in test_env.items():
        os.environ[key] = value
    
    get_settings.cache_clear()
    settings = get_settings()
    
    yield settings
    
    # Cleanup
    for key in test_env.keys():
        os.environ.pop(key, None)
    get_settings.cache_clear()


# FIXTURES DE BANCO DE DADOS

@pytest.fixture(scope="session")
def test_engine(test_settings):
    """Engine de banco SQLite in-memory para testes."""
    engine = create_engine(
        test_settings.get_database_url(),
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False,
        future=True
    )
    
    Base.metadata.create_all(bind=engine)
    yield engine
    
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def test_db(test_engine):
    """Sessão de banco isolada para cada teste."""
    connection = test_engine.connect()
    transaction = connection.begin()
    
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


# FIXTURES DE CACHE

@pytest.fixture
def test_cache():
    """Serviço de cache mock para testes."""
    mock_cache = MagicMock()
    mock_cache.get.return_value = None
    mock_cache.set.return_value = None
    mock_cache.delete.return_value = None
    mock_cache.ping.return_value = True
    mock_cache.close.return_value = None
    return mock_cache


# MOCK DO MODELO ML

@pytest.fixture
def mock_ml_responses():
    """Respostas mock determinísticas do modelo."""
    return {
        "Eu amo este produto!": {
            "sentiment": "positive",
            "confidence": 0.95,
            "language": "pt",
            "all_scores": [
                {"label": "positive", "score": 0.95},
                {"label": "neutral", "score": 0.03},
                {"label": "negative", "score": 0.02}
            ]
        },
        "Odiei essa experiência": {
            "sentiment": "negative",
            "confidence": 0.89,
            "language": "pt",
            "all_scores": [
                {"label": "negative", "score": 0.89},
                {"label": "neutral", "score": 0.08},
                {"label": "positive", "score": 0.03}
            ]
        },
        "O produto é ok": {
            "sentiment": "neutral",
            "confidence": 0.67,
            "language": "pt",
            "all_scores": [
                {"label": "neutral", "score": 0.67},
                {"label": "positive", "score": 0.20},
                {"label": "negative", "score": 0.13}
            ]
        },
        "I love this product!": {
            "sentiment": "positive",
            "confidence": 0.92,
            "language": "en",
            "all_scores": [
                {"label": "positive", "score": 0.92},
                {"label": "neutral", "score": 0.05},
                {"label": "negative", "score": 0.03}
            ]
        },
        "This is terrible": {
            "sentiment": "negative",
            "confidence": 0.88,
            "language": "en",
            "all_scores": [
                {"label": "negative", "score": 0.88},
                {"label": "neutral", "score": 0.08},
                {"label": "positive", "score": 0.04}
            ]
        },
        "It's okay": {
            "sentiment": "neutral",
            "confidence": 0.71,
            "language": "en",
            "all_scores": [
                {"label": "neutral", "score": 0.71},
                {"label": "positive", "score": 0.16},
                {"label": "negative", "score": 0.13}
            ]
        }
    }


@pytest.fixture
def mock_analyzer(mock_ml_responses):
    """Mock do SentimentAnalyzer com respostas previsíveis."""
    mock = MagicMock(spec=SentimentAnalyzer)
    
    def analyze(text: str):
        normalized_text = text.strip()
        
        # Usar resposta específica ou gerar baseada em heurística
        response = mock_ml_responses.get(normalized_text)
        if not response:
            text_lower = normalized_text.lower()
            if any(word in text_lower for word in ["love", "great", "excellent", "amo"]):
                sentiment, confidence = "positive", 0.85
            elif any(word in text_lower for word in ["hate", "terrible", "awful", "odio"]):
                sentiment, confidence = "negative", 0.82
            else:
                sentiment, confidence = "neutral", 0.60
            
            response = {
                "sentiment": sentiment,
                "confidence": confidence,
                "language": "en",
                "all_scores": [
                    {"label": sentiment, "score": confidence},
                    {"label": "neutral", "score": round((1 - confidence) / 2, 2)},
                    {"label": "positive" if sentiment != "positive" else "negative", 
                     "score": round((1 - confidence) / 2, 2)}
                ]
            }
        
        return response
    
    mock.analyze.side_effect = analyze
    mock.analyze_batch.side_effect = lambda texts: [analyze(text) for text in texts]
    mock.get_model_info.return_value = {
        "model_name": "mock_model",
        "model_loaded": True,
        "device": "cpu"
    }
    mock._model_loaded = True
    
    return mock


# CLIENTE DE TESTE

@pytest.fixture
def test_client(test_db, test_cache, mock_analyzer):
    """Cliente FastAPI configurado para testes."""
    def override_get_db():
        yield test_db
    
    def override_get_cache():
        return test_cache
    
    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_cache_dependency] = override_get_cache
    
    # Múltiplos patches para garantir que o mock seja usado
    patches = [
        patch('app.sentiment.service.get_sentiment_analyzer', return_value=mock_analyzer),
        patch('app.sentiment.analyzer.SentimentAnalyzer', return_value=mock_analyzer),
        patch('app.main.get_sentiment_analyzer', return_value=mock_analyzer),
    ]
    
    for p in patches:
        p.start()
    
    try:
        with TestClient(app) as client:
            yield client
    finally:
        for p in patches:
            p.stop()
        app.dependency_overrides.clear()


# DADOS DE TESTE

@pytest.fixture
def sample_analyses(test_db):
    """Dados de amostra para testes de histórico."""
    base_time = datetime.utcnow()
    
    analyses = [
        SentimentAnalysis(
            text="Produto excelente, recomendo!",
            sentiment="positive",
            confidence=0.95,
            language="pt",
            all_scores=[{"label": "positive", "score": 0.95}],
            created_at=base_time - timedelta(days=1)
        ),
        SentimentAnalysis(
            text="Amazing service!",
            sentiment="positive",
            confidence=0.89,
            language="en",
            all_scores=[{"label": "positive", "score": 0.89}],
            created_at=base_time - timedelta(days=2)
        ),
        SentimentAnalysis(
            text="Terrível experiência",
            sentiment="negative",
            confidence=0.87,
            language="pt",
            all_scores=[{"label": "negative", "score": 0.87}],
            created_at=base_time - timedelta(days=3)
        ),
        SentimentAnalysis(
            text="Very disappointing",
            sentiment="negative",
            confidence=0.82,
            language="en",
            all_scores=[{"label": "negative", "score": 0.82}],
            created_at=base_time - timedelta(days=4)
        ),
        SentimentAnalysis(
            text="O produto é razoável",
            sentiment="neutral",
            confidence=0.65,
            language="pt",
            all_scores=[{"label": "neutral", "score": 0.65}],
            created_at=base_time - timedelta(days=5)
        )
    ]
    
    for analysis in analyses:
        test_db.add(analysis)
    test_db.commit()
    
    for analysis in analyses:
        test_db.refresh(analysis)
    
    return analyses


@pytest.fixture
def analysis_texts():
    """Textos de exemplo para testes."""
    return {
        "positive_pt": "Eu amo este produto!",
        "negative_pt": "Odiei essa experiência",
        "neutral_pt": "O produto é ok",
        "positive_en": "I love this product!",
        "negative_en": "This is terrible",
        "neutral_en": "It's okay",
        "empty": "",
        "whitespace": "   ",
        "long_text": "a" * 2001,
        "short_valid": "ok"
    }


# CONFIGURAÇÃO PYTEST

def pytest_configure(config):
    """Configuração do pytest."""
    config.addinivalue_line("markers", "slow: marca testes lentos")
    config.addinivalue_line("markers", "integration: marca testes de integração")


@pytest.fixture(autouse=True)
def cleanup():
    """Cleanup automático entre testes."""
    yield
    app.dependency_overrides.clear()
    get_settings.cache_clear()