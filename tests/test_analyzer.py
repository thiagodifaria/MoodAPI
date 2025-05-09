"""
Testes unitários para o serviço de análise de sentimentos.
"""
import pytest
from app.services.analyzer import SentimentAnalyzer

class TestSentimentAnalyzer:
    """Testes para o analisador de sentimentos."""

    def test_detect_language(self, analyzer, sample_texts):
        """Testa a detecção de idioma."""
        # Inglês
        lang_en = analyzer.detect_language(sample_texts["en"]["positive"])
        assert lang_en == "en"
        
        # Português
        lang_pt = analyzer.detect_language(sample_texts["pt"]["positive"])
        assert lang_pt == "pt"
        
        # Espanhol
        lang_es = analyzer.detect_language(sample_texts["es"]["positive"])
        assert lang_es == "es"
        
        # Texto muito curto (deve retornar "en" como padrão)
        lang_short = analyzer.detect_language("Hi")
        assert lang_short == "en"

    def test_analyze_sentiment_basic(self, analyzer, sample_texts):
        """Testa a análise básica de sentimentos."""
        # Texto positivo em inglês
        result_pos = analyzer.analyze_sentiment(sample_texts["en"]["positive"])
        assert result_pos["sentiment"]["label"] == "positive"
        assert result_pos["sentiment"]["score"] > 0
        
        # Texto negativo em inglês
        result_neg = analyzer.analyze_sentiment(sample_texts["en"]["negative"])
        assert result_neg["sentiment"]["label"] == "negative"
        assert result_neg["sentiment"]["score"] < 0
        
        # Texto neutro em inglês
        result_neu = analyzer.analyze_sentiment(sample_texts["en"]["neutral"])
        assert result_neu["sentiment"]["label"] in ["neutral", "positive", "negative"]
        
        # Verificar se outros campos estão presentes
        assert "language" in result_pos
        assert "processing_time" in result_pos

    def test_analyze_sentiment_with_language(self, analyzer, sample_texts):
        """Testa a análise de sentimentos com idioma especificado."""
        # Português
        result_pt = analyzer.analyze_sentiment(sample_texts["pt"]["positive"], language="pt")
        assert result_pt["language"] == "pt"
        assert result_pt["sentiment"]["label"] == "positive"
        
        # Espanhol
        result_es = analyzer.analyze_sentiment(sample_texts["es"]["negative"], language="es")
        assert result_es["language"] == "es"
        assert result_es["sentiment"]["label"] == "negative"

    def test_analyze_emotions(self, analyzer, sample_texts):
        """Testa a análise de emoções."""
        # Texto positivo - deve detectar emoções como felicidade
        emotions_pos = analyzer.analyze_emotions(sample_texts["en"]["positive"])
        assert "joy" in emotions_pos or "happiness" in emotions_pos
        
        # Texto negativo - deve detectar emoções como tristeza ou raiva
        emotions_neg = analyzer.analyze_emotions(sample_texts["en"]["negative"])
        assert any(e in emotions_neg for e in ["sadness", "anger", "disgust"])
        
        # Verifica formato da resposta
        assert isinstance(emotions_pos, dict)
        assert all(isinstance(v, float) for v in emotions_pos.values())

    def test_extract_entities(self, analyzer):
        """Testa a extração de entidades."""
        text = "Microsoft and Google are two major technology companies based in the United States."
        entities = analyzer.extract_entities(text)
        
        # Verificar se entidades comuns foram extraídas
        extracted_texts = [e["text"].lower() for e in entities]
        assert any("microsoft" in text.lower() for text in extracted_texts)
        assert any("google" in text.lower() for text in extracted_texts)
        assert any("united states" in text.lower() for text in extracted_texts)
        
        # Verificar formato da resposta
        assert isinstance(entities, list)
        for entity in entities:
            assert "text" in entity
            assert "type" in entity
            assert isinstance(entity["text"], str)
            assert isinstance(entity["type"], str)

    def test_extract_keywords(self, analyzer):
        """Testa a extração de palavras-chave."""
        text = "Artificial intelligence and machine learning are transforming the technology landscape."
        keywords = analyzer.extract_keywords(text)
        
        # Verificar se palavras-chave esperadas foram extraídas
        keyword_texts = [k["text"].lower() for k in keywords]
        assert any("artificial intelligence" in kw or "intelligence" in kw for kw in keyword_texts)
        assert any("machine learning" in kw or "learning" in kw for kw in keyword_texts)
        assert any("technology" in kw for kw in keyword_texts)
        
        # Verificar formato da resposta
        assert isinstance(keywords, list)
        for keyword in keywords:
            assert "text" in keyword
            assert "relevance" in keyword
            assert isinstance(keyword["text"], str)
            assert isinstance(keyword["relevance"], float)

    def test_analyze_detailed(self, analyzer, sample_texts):
        """Testa a análise detalhada completa."""
        text = sample_texts["en"]["positive"]
        result = analyzer.analyze_detailed(text)
        
        # Verificar presença de todos os componentes
        assert "sentiment" in result
        assert "emotions" in result
        assert "entities" in result
        assert "keywords" in result
        assert "language" in result
        assert "processing_time" in result
        
        # Verificar tipos
        assert isinstance(result["sentiment"], dict)
        assert isinstance(result["emotions"], dict)
        assert isinstance(result["entities"], list)
        assert isinstance(result["keywords"], list)
        assert isinstance(result["language"], str)
        assert isinstance(result["processing_time"], (int, float))

    def test_batch_analyze(self, analyzer, sample_texts):
        """Testa o processamento em lote."""
        texts = [
            sample_texts["en"]["positive"],
            sample_texts["en"]["negative"],
            sample_texts["en"]["neutral"]
        ]
        
        results = analyzer.batch_analyze(texts)
        
        # Verificar se todos os textos foram analisados
        assert len(results) == len(texts)
        
        # Verificar se cada resultado tem os campos básicos
        for result in results:
            assert "sentiment" in result
            assert "language" in result
            assert "processing_time" in result