"""
Testes de integração para os endpoints da API.
"""
import json
from fastapi import status
import pytest


class TestHealthEndpoint:
    """Testes para o endpoint de verificação de saúde."""

    def test_health_check(self, client):
        """Testa se o endpoint de saúde responde corretamente."""
        response = client.get("/api/v1/health")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"
        assert "version" in data
        assert "uptime" in data
        assert "database" in data


class TestRootEndpoint:
    """Testes para o endpoint raiz."""

    def test_root_endpoint(self, client):
        """Testa se o endpoint raiz responde corretamente."""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "title" in data
        assert "description" in data
        assert "version" in data
        assert "docs_url" in data


class TestSentimentAnalysisEndpoints:
    """Testes para os endpoints de análise de sentimentos."""

    def test_basic_analysis(self, client, sample_texts):
        """Testa a análise básica de sentimentos."""
        payload = {"text": sample_texts["en"]["positive"]}
        response = client.post("/api/v1/analyze/basic", json=payload)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "id" in data
        assert "timestamp" in data
        assert "text" in data
        assert "language" in data
        assert "sentiment" in data
        assert "processing_time_ms" in data
        
        assert data["sentiment"]["label"] == "positive"
        assert data["language"] == "en"

    def test_basic_analysis_with_language(self, client, sample_texts):
        """Testa a análise básica com idioma especificado."""
        payload = {
            "text": sample_texts["pt"]["positive"],
            "language": "pt"
        }
        response = client.post("/api/v1/analyze/basic", json=payload)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["language"] == "pt"
        assert data["sentiment"]["label"] == "positive"

    def test_detailed_analysis(self, client, sample_texts):
        """Testa a análise detalhada de sentimentos."""
        payload = {"text": sample_texts["en"]["positive"]}
        response = client.post("/api/v1/analyze/detailed", json=payload)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "id" in data
        assert "timestamp" in data
        assert "text" in data
        assert "language" in data
        assert "sentiment" in data
        assert "emotions" in data
        assert "entities" in data
        assert "keywords" in data
        assert "processing_time_ms" in data

    def test_batch_analysis(self, client, sample_texts):
        """Testa o processamento em lote."""
        payload = {
            "texts": [
                sample_texts["en"]["positive"],
                sample_texts["en"]["negative"],
                sample_texts["en"]["neutral"]
            ],
            "analysis_type": "basic"
        }
        response = client.post("/api/v1/analyze/batch", json=payload)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 3
        
        # Verificar se cada resultado tem os campos básicos
        for result in data["results"]:
            assert "id" in result
            assert "sentiment" in result
            assert "language" in result

    def test_batch_analysis_detailed(self, client, sample_texts):
        """Testa o processamento em lote com análise detalhada."""
        payload = {
            "texts": [
                sample_texts["en"]["positive"],
                sample_texts["en"]["negative"]
            ],
            "analysis_type": "detailed"
        }
        response = client.post("/api/v1/analyze/batch", json=payload)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert len(data["results"]) == 2
        
        # Verificar se cada resultado tem os campos detalhados
        for result in data["results"]:
            assert "emotions" in result
            assert "entities" in result
            assert "keywords" in result

    def test_invalid_text_input(self, client):
        """Testa a validação de entrada inválida."""
        # Texto vazio
        payload = {"text": ""}
        response = client.post("/api/v1/analyze/basic", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Texto muito longo (simulado - dependerá do limite configurado)
        payload = {"text": "a" * 10001}  # Assumindo um limite de 10000 caracteres
        response = client.post("/api/v1/analyze/basic", json=payload)
        assert response.status_code in [status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, 
                                       status.HTTP_422_UNPROCESSABLE_ENTITY]


class TestHistoryEndpoints:
    """Testes para os endpoints de histórico."""

    def test_get_history_empty(self, client):
        """Testa a consulta de histórico vazio."""
        response = client.get("/api/v1/history")
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_get_history_after_analysis(self, client, sample_texts):
        """Testa a consulta de histórico após análise."""
        # Primeiro, fazer uma análise para criar um registro
        payload = {"text": sample_texts["en"]["positive"]}
        client.post("/api/v1/analyze/basic", json=payload)
        
        # Agora, consultar o histórico
        response = client.get("/api/v1/history")
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        
        # Verificar se o primeiro item tem os campos esperados
        first_item = data["items"][0]
        assert "id" in first_item
        assert "timestamp" in first_item
        assert "text" in first_item
        assert "sentiment" in first_item
        assert "language" in first_item

    def test_get_analysis_by_id(self, client, sample_texts):
        """Testa a consulta de uma análise específica por ID."""
        # Primeiro, fazer uma análise para criar um registro
        payload = {"text": sample_texts["en"]["positive"]}
        response = client.post("/api/v1/analyze/detailed", json=payload)
        analysis_id = response.json()["id"]
        
        # Agora, consultar a análise por ID
        response = client.get(f"/api/v1/history/{analysis_id}")
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["id"] == analysis_id
        assert "sentiment" in data
        assert "emotions" in data
        assert "entities" in data
        assert "keywords" in data

    def test_get_nonexistent_analysis(self, client):
        """Testa a consulta de uma análise que não existe."""
        response = client.get("/api/v1/history/nonexistent_id")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_analysis(self, client, sample_texts):
        """Testa a exclusão de uma análise."""
        # Primeiro, fazer uma análise para criar um registro
        payload = {"text": sample_texts["en"]["positive"]}
        response = client.post("/api/v1/analyze/basic", json=payload)
        analysis_id = response.json()["id"]
        
        # Excluir a análise
        response = client.delete(f"/api/v1/history/{analysis_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verificar se a análise foi realmente excluída
        response = client.get(f"/api/v1/history/{analysis_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestStatsEndpoint:
    """Testes para o endpoint de estatísticas."""

    def test_get_stats_empty(self, client):
        """Testa as estatísticas quando não há dados."""
        response = client.get("/api/v1/stats")
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "total_requests" in data
        assert "sentiment_distribution" in data
        assert "language_distribution" in data
        assert "average_processing_time" in data

    def test_get_stats_after_analysis(self, client, sample_texts):
        """Testa as estatísticas após algumas análises."""
        # Realizar algumas análises
        client.post("/api/v1/analyze/basic", json={"text": sample_texts["en"]["positive"]})
        client.post("/api/v1/analyze/basic", json={"text": sample_texts["en"]["negative"]})
        client.post("/api/v1/analyze/basic", json={"text": sample_texts["pt"]["positive"], "language": "pt"})
        
        # Consultar estatísticas
        response = client.get("/api/v1/stats")
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["total_requests"] >= 3
        
        # Verificar distribuição de sentimentos
        assert "positive" in data["sentiment_distribution"]
        assert "negative" in data["sentiment_distribution"]
        
        # Verificar distribuição de idiomas
        assert "en" in data["language_distribution"]
        assert "pt" in data["language_distribution"]