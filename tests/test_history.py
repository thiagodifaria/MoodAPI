import pytest
from datetime import datetime, date, timedelta
from fastapi import status
from sqlalchemy.orm import Session

from app.sentiment.models import SentimentAnalysis


class TestHistoryEndpoints:
    """Testes para endpoints de histórico."""
    
    def test_get_history_empty(self, test_client):
        """Testa consulta de histórico vazio."""
        response = test_client.get("/api/v1/history")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "items" in data
        assert "pagination" in data
        assert data["pagination"]["total"] == 0
        assert len(data["items"]) == 0
    
    def test_get_history_with_data(self, test_client, test_db, sample_analyses):
        """Testa consulta de histórico com dados."""
        # Adicionar análises de teste
        for analysis in sample_analyses:
            test_db.add(analysis)
        test_db.commit()
        
        response = test_client.get("/api/v1/history")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data["items"]) > 0
        assert data["pagination"]["total"] > 0
        
        # Verificar estrutura do item
        item = data["items"][0]
        assert "id" in item
        assert "text" in item
        assert "sentiment" in item
        assert "confidence" in item
        assert "language" in item
        assert "created_at" in item
    
    def test_get_history_pagination(self, test_client, test_db, sample_analyses):
        """Testa paginação do histórico."""
        # Adicionar análises de teste
        for analysis in sample_analyses:
            test_db.add(analysis)
        test_db.commit()
        
        # Primeira página
        response = test_client.get("/api/v1/history?page=1&limit=2")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert len(data["items"]) <= 2
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["limit"] == 2
        
        # Segunda página
        if data["pagination"]["pages"] > 1:
            response = test_client.get("/api/v1/history?page=2&limit=2")
            assert response.status_code == status.HTTP_200_OK
            
            data2 = response.json()
            assert data2["pagination"]["page"] == 2
    
    def test_get_history_filter_sentiment(self, test_client, test_db, sample_analyses):
        """Testa filtro por sentimento."""
        # Adicionar análises de teste
        for analysis in sample_analyses:
            test_db.add(analysis)
        test_db.commit()
        
        response = test_client.get("/api/v1/history?sentiment=positive")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verificar se todos os resultados são positive
        for item in data["items"]:
            assert item["sentiment"] == "positive"
    
    def test_get_history_filter_language(self, test_client, test_db, sample_analyses):
        """Testa filtro por idioma."""
        # Adicionar análises de teste
        for analysis in sample_analyses:
            test_db.add(analysis)
        test_db.commit()
        
        response = test_client.get("/api/v1/history?language=pt")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verificar se todos os resultados são em português
        for item in data["items"]:
            assert item["language"] == "pt"
    
    def test_get_history_filter_date_range(self, test_client, test_db, sample_analyses):
        """Testa filtro por intervalo de datas."""
        # Adicionar análises de teste
        for analysis in sample_analyses:
            test_db.add(analysis)
        test_db.commit()
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        response = test_client.get(
            f"/api/v1/history?start_date={yesterday}&end_date={today}"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verificar filtros aplicados
        filters_applied = data.get("filters_applied", {})
        assert "start_date" in filters_applied or "end_date" in filters_applied
    
    def test_get_history_filter_confidence(self, test_client, test_db, sample_analyses):
        """Testa filtro por confiança."""
        # Adicionar análises de teste
        for analysis in sample_analyses:
            test_db.add(analysis)
        test_db.commit()
        
        response = test_client.get("/api/v1/history?min_confidence=0.8")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verificar se todas as confianças são >= 0.8
        for item in data["items"]:
            assert item["confidence"] >= 0.8
    
    def test_get_history_multiple_filters(self, test_client, test_db, sample_analyses):
        """Testa múltiplos filtros combinados."""
        # Adicionar análises de teste
        for analysis in sample_analyses:
            test_db.add(analysis)
        test_db.commit()
        
        response = test_client.get(
            "/api/v1/history?sentiment=positive&language=pt&min_confidence=0.7"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verificar se todos os filtros foram aplicados
        for item in data["items"]:
            assert item["sentiment"] == "positive"
            assert item["language"] == "pt"
            assert item["confidence"] >= 0.7
    
    def test_get_history_invalid_page(self, test_client):
        """Testa página inexistente."""
        response = test_client.get("/api/v1/history?page=999")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Deve retornar array vazio, não erro 404
        assert data["items"] == []
        assert data["pagination"]["total"] >= 0
    
    def test_get_history_invalid_limit(self, test_client):
        """Testa limite inválido."""
        response = test_client.get("/api/v1/history?limit=1000")
        
        # Deve ser rejeitado por exceder limite máximo
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestHistoryByID:
    """Testes para consulta por ID específico."""
    
    def test_get_analysis_by_id_success(self, test_client, test_db, sample_analyses):
        """Testa busca por ID existente."""
        # Adicionar análise de teste
        analysis = sample_analyses[0]
        test_db.add(analysis)
        test_db.commit()
        
        response = test_client.get(f"/api/v1/history/{analysis.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["id"] == analysis.id
        assert data["text"] == analysis.text
        assert data["sentiment"] == analysis.sentiment
    
    def test_get_analysis_by_id_not_found(self, test_client):
        """Testa busca por ID inexistente."""
        fake_id = "non-existent-id-12345"
        response = test_client.get(f"/api/v1/history/{fake_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        
        assert "error" in data
        assert fake_id in data["detail"]
    
    def test_delete_analysis_success(self, test_client, test_db, sample_analyses):
        """Testa remoção de análise existente."""
        # Adicionar análise de teste
        analysis = sample_analyses[0]
        test_db.add(analysis)
        test_db.commit()
        
        initial_count = test_db.query(SentimentAnalysis).count()
        
        response = test_client.delete(f"/api/v1/history/{analysis.id}")
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verificar se foi removida do banco
        final_count = test_db.query(SentimentAnalysis).count()
        assert final_count == initial_count - 1
        
        # Verificar se não existe mais
        response = test_client.get(f"/api/v1/history/{analysis.id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_analysis_not_found(self, test_client):
        """Testa remoção de análise inexistente."""
        fake_id = "non-existent-id-12345"
        response = test_client.delete(f"/api/v1/history/{fake_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAnalyticsEndpoints:
    """Testes para endpoints de analytics."""
    
    def test_get_analytics_empty(self, test_client):
        """Testa analytics sem dados."""
        response = test_client.get("/api/v1/analytics")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "sentiment_distribution" in data
        assert "language_distribution" in data
        assert "total_analyses" in data
        assert data["total_analyses"] == 0
    
    def test_get_analytics_with_data(self, test_client, test_db, sample_analyses):
        """Testa analytics com dados."""
        # Adicionar análises de teste
        for analysis in sample_analyses:
            test_db.add(analysis)
        test_db.commit()
        
        response = test_client.get("/api/v1/analytics")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verificar estrutura
        assert "sentiment_distribution" in data
        assert "language_distribution" in data
        assert "avg_confidence" in data
        assert "total_analyses" in data
        
        # Verificar se total bate com número de análises
        assert data["total_analyses"] > 0
        
        # Verificar distribuição de sentimentos
        sentiment_dist = data["sentiment_distribution"]
        assert "positive" in sentiment_dist
        assert "negative" in sentiment_dist
        assert "neutral" in sentiment_dist
        
        # Verificar se soma dos sentimentos bate com total
        total_sentiments = sum(sentiment_dist.values())
        assert total_sentiments == data["total_analyses"]
    
    def test_get_analytics_with_date_filter(self, test_client, test_db, sample_analyses):
        """Testa analytics com filtro de data."""
        # Adicionar análises de teste
        for analysis in sample_analyses:
            test_db.add(analysis)
        test_db.commit()
        
        response = test_client.get("/api/v1/analytics?days=7")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "date_range" in data
        assert data["total_analyses"] >= 0


class TestStatsEndpoints:
    """Testes para endpoints de estatísticas."""
    
    def test_get_stats_default_period(self, test_client):
        """Testa stats com período padrão."""
        response = test_client.get("/api/v1/stats")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "period" in data
        assert "total_analyses" in data
        assert "avg_confidence" in data
        assert "timestamp" in data
    
    def test_get_stats_custom_period(self, test_client, test_db, sample_analyses):
        """Testa stats com período customizado."""
        # Adicionar análises de teste
        for analysis in sample_analyses:
            test_db.add(analysis)
        test_db.commit()
        
        response = test_client.get("/api/v1/stats?period=7d&group_by=day")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["period"] == "7d"
        assert "group_by" in data
        assert data["group_by"] == "day"
    
    def test_get_stats_weekly_grouping(self, test_client, test_db, sample_analyses):
        """Testa stats com agrupamento semanal."""
        # Adicionar análises de teste
        for analysis in sample_analyses:
            test_db.add(analysis)
        test_db.commit()
        
        response = test_client.get("/api/v1/stats?period=30d&group_by=week")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["period"] == "30d"
        assert data["group_by"] == "week"
    
    def test_get_stats_invalid_period(self, test_client):
        """Testa stats com período inválido."""
        response = test_client.get("/api/v1/stats?period=invalid")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestHistoryPerformance:
    """Testes de performance e edge cases."""
    
    def test_large_page_size(self, test_client, test_db, sample_analyses):
        """Testa consulta com página grande."""
        # Adicionar análises de teste
        for analysis in sample_analyses:
            test_db.add(analysis)
        test_db.commit()
        
        response = test_client.get("/api/v1/history?limit=100")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verificar se não excede limite
        assert len(data["items"]) <= 100
    
    def test_text_search_functionality(self, test_client, test_db, sample_analyses):
        """Testa funcionalidade de busca textual."""
        # Adicionar análises de teste
        for analysis in sample_analyses:
            test_db.add(analysis)
        test_db.commit()
        
        response = test_client.get("/api/v1/history?text_contains=test")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verificar se busca textual funciona
        for item in data["items"]:
            assert "test" in item["text"].lower()
    
    def test_sorting_functionality(self, test_client, test_db, sample_analyses):
        """Testa funcionalidade de ordenação."""
        # Adicionar análises de teste
        for analysis in sample_analyses:
            test_db.add(analysis)
        test_db.commit()
        
        response = test_client.get("/api/v1/history?sort_by=confidence&sort_order=desc")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verificar ordenação por confiança decrescente
        if len(data["items"]) > 1:
            confidences = [item["confidence"] for item in data["items"]]
            assert confidences == sorted(confidences, reverse=True)
    
    @pytest.mark.parametrize("invalid_sentiment", ["invalid", "POSITIVE", "123"])
    def test_invalid_sentiment_filter(self, test_client, invalid_sentiment):
        """Testa filtros de sentimento inválidos."""
        response = test_client.get(f"/api/v1/history?sentiment={invalid_sentiment}")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.parametrize("invalid_confidence", [-1, 2, "invalid"])
    def test_invalid_confidence_filter(self, test_client, invalid_confidence):
        """Testa filtros de confiança inválidos."""
        response = test_client.get(f"/api/v1/history?min_confidence={invalid_confidence}")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestHistoryWorkflow:
    """Testes de fluxo completo."""
    
    def test_full_history_workflow(self, test_client, test_db, analysis_texts):
        """Testa fluxo completo: análise → histórico → analytics."""
        # 1. Fazer análise
        response = test_client.post(
            "/api/v1/sentiment/analyze",
            json={"text": analysis_texts["positive_pt"]}
        )
        assert response.status_code == status.HTTP_200_OK
        analysis_id = response.json()["id"]
        
        # 2. Verificar no histórico
        response = test_client.get("/api/v1/history")
        assert response.status_code == status.HTTP_200_OK
        history_data = response.json()
        assert len(history_data["items"]) >= 1
        
        # 3. Buscar por ID específico
        response = test_client.get(f"/api/v1/history/{analysis_id}")
        assert response.status_code == status.HTTP_200_OK
        
        # 4. Verificar analytics
        response = test_client.get("/api/v1/analytics")
        assert response.status_code == status.HTTP_200_OK
        analytics_data = response.json()
        assert analytics_data["total_analyses"] >= 1
        
        # 5. Remover análise
        response = test_client.delete(f"/api/v1/history/{analysis_id}")
        assert response.status_code == status.HTTP_200_OK
        
        # 6. Verificar remoção
        response = test_client.get(f"/api/v1/history/{analysis_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_cache_behavior_analytics(self, test_client, test_db, sample_analyses):
        """Testa comportamento de cache em analytics."""
        # Adicionar análises de teste
        for analysis in sample_analyses:
            test_db.add(analysis)
        test_db.commit()
        
        # Primeira chamada
        response1 = test_client.get("/api/v1/analytics")
        assert response1.status_code == status.HTTP_200_OK
        
        # Segunda chamada (deveria usar cache)
        response2 = test_client.get("/api/v1/analytics")
        assert response2.status_code == status.HTTP_200_OK
        
        # Verificar se dados são consistentes
        assert response1.json()["total_analyses"] == response2.json()["total_analyses"]
    
    def test_rate_limiting_history(self, test_client):
        """Testa rate limiting em endpoints de histórico."""
        # Fazer múltiplas requisições rápidas
        responses = []
        for _ in range(10):
            response = test_client.get("/api/v1/history")
            responses.append(response)
        
        # Verificar se pelo menos algumas passaram
        successful_responses = [r for r in responses if r.status_code == 200]
        assert len(successful_responses) > 0
        
        # Verificar headers de rate limiting
        last_response = responses[-1]
        assert "X-RateLimit-Limit" in last_response.headers