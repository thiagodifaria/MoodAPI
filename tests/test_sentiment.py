import pytest
import time
from fastapi import status
from fastapi.testclient import TestClient

from app.sentiment.models import SentimentAnalysis


# TESTES DE ANÁLISE INDIVIDUAL

def test_analyze_valid_text_portuguese(test_client, analysis_texts):
    """Testa análise de texto positivo em português."""
    response = test_client.post(
        "/api/v1/sentiment/analyze",
        json={"text": analysis_texts["positive_pt"]}
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["sentiment"] == "positive"
    assert data["confidence"] >= 0.5
    assert data["language"] == "pt"
    assert len(data["all_scores"]) == 3
    assert data["cached"] is False
    assert "processing_time_ms" in data or "query_time_ms" in data


def test_analyze_valid_text_english(test_client, analysis_texts):
    """Testa análise de texto negativo em inglês."""
    response = test_client.post(
        "/api/v1/sentiment/analyze", 
        json={"text": analysis_texts["negative_en"]}
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["sentiment"] == "negative"
    assert data["confidence"] >= 0.5
    assert data["language"] == "en"
    assert len(data["all_scores"]) == 3


def test_analyze_neutral_text(test_client, analysis_texts):
    """Testa análise de texto neutro."""
    response = test_client.post(
        "/api/v1/sentiment/analyze",
        json={"text": analysis_texts["neutral_pt"]}
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["sentiment"] == "neutral"
    assert data["confidence"] >= 0.5


def test_analyze_caching_behavior(test_client, analysis_texts):
    """Testa comportamento de cache em análises repetidas."""
    text = analysis_texts["positive_en"]
    
    # Primeira análise
    response1 = test_client.post(
        "/api/v1/sentiment/analyze",
        json={"text": text}
    )
    assert response1.status_code == status.HTTP_200_OK
    data1 = response1.json()
    assert data1["cached"] is False
    
    # Segunda análise (deve usar cache)
    response2 = test_client.post(
        "/api/v1/sentiment/analyze", 
        json={"text": text}
    )
    assert response2.status_code == status.HTTP_200_OK
    data2 = response2.json()
    
    # Resultados devem ser idênticos
    assert data1["sentiment"] == data2["sentiment"]
    assert data1["confidence"] == data2["confidence"]
    assert data1["language"] == data2["language"]


def test_analyze_saves_to_database(test_client, test_db, analysis_texts):
    """Testa se análise é salva no banco de dados."""
    initial_count = test_db.query(SentimentAnalysis).count()
    
    response = test_client.post(
        "/api/v1/sentiment/analyze",
        json={"text": analysis_texts["positive_pt"]}
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    final_count = test_db.query(SentimentAnalysis).count()
    assert final_count == initial_count + 1
    
    # Verificar dados salvos
    saved_analysis = test_db.query(SentimentAnalysis).order_by(
        SentimentAnalysis.created_at.desc()
    ).first()
    
    assert saved_analysis.text == analysis_texts["positive_pt"]
    assert saved_analysis.sentiment == "positive"
    assert saved_analysis.confidence > 0
    assert saved_analysis.language == "pt"


# TESTES DE VALIDAÇÃO DE ENTRADA

def test_analyze_empty_text(test_client, analysis_texts):
    """Testa análise com texto vazio."""
    response = test_client.post(
        "/api/v1/sentiment/analyze",
        json={"text": analysis_texts["empty"]}
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_analyze_whitespace_only(test_client, analysis_texts):
    """Testa análise com apenas espaços em branco."""
    response = test_client.post(
        "/api/v1/sentiment/analyze",
        json={"text": analysis_texts["whitespace"]}
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_analyze_text_too_long(test_client, analysis_texts):
    """Testa análise com texto muito longo."""
    response = test_client.post(
        "/api/v1/sentiment/analyze",
        json={"text": analysis_texts["long_text"]}
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_analyze_missing_text_field(test_client):
    """Testa análise sem campo text."""
    response = test_client.post(
        "/api/v1/sentiment/analyze",
        json={}
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_analyze_invalid_json(test_client):
    """Testa análise com JSON inválido."""
    response = test_client.post(
        "/api/v1/sentiment/analyze",
        data="invalid json"
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# TESTES DE ANÁLISE EM LOTE

def test_analyze_batch_valid_texts(test_client, analysis_texts):
    """Testa análise em lote com textos válidos."""
    texts = [
        analysis_texts["positive_pt"],
        analysis_texts["negative_en"], 
        analysis_texts["neutral_pt"]
    ]
    
    response = test_client.post(
        "/api/v1/sentiment/analyze-batch",
        json={"texts": texts}
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["total_processed"] == 3
    assert len(data["results"]) == 3
    assert "processing_time_ms" in data
    
    # Verificar resultados individuais
    results = data["results"]
    assert results[0]["sentiment"] == "positive"
    assert results[1]["sentiment"] == "negative"
    assert results[2]["sentiment"] == "neutral"


def test_analyze_batch_saves_to_database(test_client, test_db, analysis_texts):
    """Testa se análise em lote salva no banco."""
    initial_count = test_db.query(SentimentAnalysis).count()
    
    texts = [analysis_texts["positive_en"], analysis_texts["negative_pt"]]
    
    response = test_client.post(
        "/api/v1/sentiment/analyze-batch",
        json={"texts": texts}
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    final_count = test_db.query(SentimentAnalysis).count()
    assert final_count == initial_count + 2


def test_analyze_batch_empty_list(test_client):
    """Testa análise em lote com lista vazia."""
    response = test_client.post(
        "/api/v1/sentiment/analyze-batch",
        json={"texts": []}
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_analyze_batch_too_many_texts(test_client):
    """Testa análise em lote com muitos textos."""
    texts = ["texto"] * 51  # Máximo é 50
    
    response = test_client.post(
        "/api/v1/sentiment/analyze-batch",
        json={"texts": texts}
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_analyze_batch_with_invalid_text(test_client):
    """Testa lote com texto inválido."""
    texts = ["texto válido", "", "outro texto válido"]
    
    response = test_client.post(
        "/api/v1/sentiment/analyze-batch",
        json={"texts": texts}
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_analyze_batch_mixed_languages(test_client, analysis_texts):
    """Testa lote com múltiplos idiomas."""
    texts = [
        analysis_texts["positive_pt"],
        analysis_texts["positive_en"]
    ]
    
    response = test_client.post(
        "/api/v1/sentiment/analyze-batch", 
        json={"texts": texts}
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    results = data["results"]
    
    assert results[0]["language"] == "pt"
    assert results[1]["language"] == "en"
    assert all(r["sentiment"] == "positive" for r in results)


# TESTES DE HEALTH CHECK

def test_sentiment_health_check(test_client):
    """Testa health check do serviço de sentimentos."""
    response = test_client.get("/api/v1/sentiment/health")
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "model_info" in data
    
    # Verificar componentes
    services = data["services"]
    assert "ml_model" in services
    assert "cache" in services
    assert "database" in services


def test_sentiment_health_model_available(test_client):
    """Testa se modelo ML está disponível."""
    response = test_client.get("/api/v1/sentiment/health")
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    model_info = data.get("model_info", {})
    assert model_info.get("model_loaded") is True
    assert "model_name" in model_info


# TESTES DE PERFORMANCE

@pytest.mark.slow
def test_analyze_response_time(test_client, analysis_texts):
    """Testa tempo de resposta da análise."""
    start_time = time.time()
    
    response = test_client.post(
        "/api/v1/sentiment/analyze",
        json={"text": analysis_texts["positive_pt"]}
    )
    
    elapsed_time = time.time() - start_time
    
    assert response.status_code == status.HTTP_200_OK
    assert elapsed_time < 1.0  # Máximo 1 segundo


@pytest.mark.slow  
def test_analyze_batch_performance(test_client, analysis_texts):
    """Testa performance de análise em lote."""
    texts = [
        analysis_texts["positive_pt"],
        analysis_texts["negative_en"],
        analysis_texts["neutral_pt"],
        analysis_texts["positive_en"],
        analysis_texts["negative_pt"]
    ]
    
    start_time = time.time()
    
    response = test_client.post(
        "/api/v1/sentiment/analyze-batch",
        json={"texts": texts}
    )
    
    elapsed_time = time.time() - start_time
    
    assert response.status_code == status.HTTP_200_OK
    assert elapsed_time < 2.0  # Máximo 2 segundos para 5 textos


def test_cache_performance_improvement(test_client, analysis_texts):
    """Testa melhoria de performance com cache."""
    text = analysis_texts["positive_pt"]
    
    # Primeira chamada (sem cache)
    start_time = time.time()
    response1 = test_client.post(
        "/api/v1/sentiment/analyze",
        json={"text": text}
    )
    first_call_time = time.time() - start_time
    
    # Segunda chamada (com cache)
    start_time = time.time()
    response2 = test_client.post(
        "/api/v1/sentiment/analyze",
        json={"text": text}
    )
    second_call_time = time.time() - start_time
    
    assert response1.status_code == status.HTTP_200_OK
    assert response2.status_code == status.HTTP_200_OK
    
    # Cache deve ser mais rápido (ou pelo menos não mais lento)
    assert second_call_time <= first_call_time * 1.5


# TESTES DE CASOS EXTREMOS

def test_analyze_special_characters(test_client):
    """Testa análise com caracteres especiais."""
    special_text = "😀 Produto incrível! @#$%&*()[]{}|\\:;\"'<>,.?/~`"
    
    response = test_client.post(
        "/api/v1/sentiment/analyze",
        json={"text": special_text}
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["sentiment"] in ["positive", "negative", "neutral"]
    assert 0 <= data["confidence"] <= 1


def test_analyze_very_short_text(test_client, analysis_texts):
    """Testa análise com texto muito curto."""
    response = test_client.post(
        "/api/v1/sentiment/analyze",
        json={"text": analysis_texts["short_valid"]}
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["sentiment"] in ["positive", "negative", "neutral"]


def test_analyze_numbers_only(test_client):
    """Testa análise com apenas números."""
    response = test_client.post(
        "/api/v1/sentiment/analyze",
        json={"text": "123456789"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["sentiment"] in ["positive", "negative", "neutral"]


def test_analyze_repeated_text(test_client):
    """Testa análise com texto repetitivo."""
    repeated_text = "bom " * 100  # 400 caracteres
    
    response = test_client.post(
        "/api/v1/sentiment/analyze",
        json={"text": repeated_text}
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["sentiment"] in ["positive", "negative", "neutral"]


# TESTES DE INTEGRAÇÃO

def test_full_workflow_single_analysis(test_client, test_db, analysis_texts):
    """Testa fluxo completo de análise individual."""
    text = analysis_texts["positive_pt"]
    
    # 1. Análise
    response = test_client.post(
        "/api/v1/sentiment/analyze",
        json={"text": text}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # 2. Verificar resposta
    assert data["sentiment"] == "positive"
    assert data["confidence"] > 0.5
    assert data["language"] == "pt"
    
    # 3. Verificar salvamento no banco
    saved_analysis = test_db.query(SentimentAnalysis).filter(
        SentimentAnalysis.text == text
    ).first()
    
    assert saved_analysis is not None
    assert saved_analysis.sentiment == data["sentiment"]
    assert saved_analysis.confidence == data["confidence"]


def test_full_workflow_batch_analysis(test_client, test_db, analysis_texts):
    """Testa fluxo completo de análise em lote."""
    texts = [
        analysis_texts["positive_pt"],
        analysis_texts["negative_en"]
    ]
    
    initial_count = test_db.query(SentimentAnalysis).count()
    
    # 1. Análise em lote
    response = test_client.post(
        "/api/v1/sentiment/analyze-batch",
        json={"texts": texts}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # 2. Verificar resposta
    assert data["total_processed"] == 2
    assert len(data["results"]) == 2
    
    results = data["results"]
    assert results[0]["sentiment"] == "positive"
    assert results[1]["sentiment"] == "negative"
    
    # 3. Verificar salvamento no banco
    final_count = test_db.query(SentimentAnalysis).count()
    assert final_count == initial_count + 2
    
    # Verificar dados específicos
    for i, text in enumerate(texts):
        saved = test_db.query(SentimentAnalysis).filter(
            SentimentAnalysis.text == text
        ).first()
        assert saved is not None
        assert saved.sentiment == results[i]["sentiment"]


# TESTES DE RESPOSTA FORMAT

def test_analyze_response_format(test_client, analysis_texts):
    """Testa formato da resposta de análise."""
    response = test_client.post(
        "/api/v1/sentiment/analyze",
        json={"text": analysis_texts["positive_pt"]}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Campos obrigatórios
    required_fields = [
        "id", "sentiment", "confidence", "language", 
        "all_scores", "timestamp", "cached"
    ]
    
    for field in required_fields:
        assert field in data, f"Campo {field} não encontrado na resposta"
    
    # Tipos corretos
    assert isinstance(data["sentiment"], str)
    assert isinstance(data["confidence"], (int, float))
    assert isinstance(data["language"], str) 
    assert isinstance(data["all_scores"], list)
    assert isinstance(data["cached"], bool)
    
    # Valores válidos
    assert data["sentiment"] in ["positive", "negative", "neutral"]
    assert 0 <= data["confidence"] <= 1
    assert len(data["all_scores"]) > 0


def test_batch_response_format(test_client, analysis_texts):
    """Testa formato da resposta de análise em lote."""
    texts = [analysis_texts["positive_pt"], analysis_texts["negative_en"]]
    
    response = test_client.post(
        "/api/v1/sentiment/analyze-batch",
        json={"texts": texts}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Campos obrigatórios
    assert "results" in data
    assert "total_processed" in data
    
    # Tipos corretos
    assert isinstance(data["results"], list)
    assert isinstance(data["total_processed"], int)
    
    # Valores consistentes
    assert len(data["results"]) == data["total_processed"]
    assert data["total_processed"] == len(texts)