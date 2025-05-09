"""
Configurações e fixtures para testes.
Este arquivo contém fixtures que podem ser reutilizadas em vários testes.
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.services.analyzer import SentimentAnalyzer

# Criar banco de dados em memória para testes
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine():
    """Cria um motor de banco de dados para testes."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Cria uma sessão de banco de dados para testes."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Cria um cliente de teste para a API."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def analyzer():
    """Retorna uma instância do analisador de sentimentos."""
    return SentimentAnalyzer()


@pytest.fixture
def sample_texts():
    """Retorna uma amostra de textos para teste em diferentes idiomas."""
    return {
        "en": {
            "positive": "I am very happy with the results of this project!",
            "negative": "This is the worst experience I've ever had.",
            "neutral": "The sky is blue and the weather is mild today."
        },
        "pt": {
            "positive": "Estou muito feliz com o resultado deste projeto!",
            "negative": "Esta foi a pior experiência que já tive.",
            "neutral": "O céu está azul e o clima está ameno hoje."
        },
        "es": {
            "positive": "¡Estoy muy feliz con los resultados de este proyecto!",
            "negative": "Esta es la peor experiencia que he tenido.",
            "neutral": "El cielo está azul y el clima es templado hoy."
        }
    }


@pytest.fixture
def api_key_header():
    """Retorna um cabeçalho de API key para testes que requerem autenticação."""
    # Normalmente você pegaria isso de uma variável de ambiente
    # ou de um arquivo de configuração específico para testes
    return {"X-API-Key": "test-api-key"}