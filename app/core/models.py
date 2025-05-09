from datetime import datetime
import uuid
import json
from typing import Dict, List, Optional, Any

from sqlalchemy import Column, String, Float, Integer, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from app.core.database import Base


class Analysis(Base):
    """Modelo para armazenar análises de sentimento"""
    __tablename__ = "analysis"

    # Identificador único da análise
    id = Column(String(36), primary_key=True, index=True, default=lambda: f"analysis_{uuid.uuid4().hex}")
    
    # Texto analisado
    text = Column(Text, nullable=False)
    
    # Timestamp da análise
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Idioma do texto
    language = Column(String(5), nullable=False)
    
    # Classificação do sentimento (positivo, negativo, neutro)
    sentiment_label = Column(String(20), nullable=False)
    
    # Pontuação do sentimento (-1.0 a 1.0)
    sentiment_score = Column(Float, nullable=False)
    
    # Confiança da análise (0.0 a 1.0)
    confidence = Column(Float, nullable=False)
    
    # Tempo de processamento em milissegundos
    processing_time_ms = Column(Integer, nullable=False)
    
    # Análise completa em formato JSON (para análises detalhadas)
    full_analysis = Column(JSON, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Converte o modelo para um dicionário"""
        result = {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "text": self.text,
            "language": self.language,
            "sentiment": {
                "label": self.sentiment_label,
                "score": self.sentiment_score,
                "confidence": self.confidence
            },
            "processing_time_ms": self.processing_time_ms
        }
        
        # Adicionar análise detalhada se disponível
        if self.full_analysis:
            full_analysis = self.full_analysis
            if isinstance(full_analysis, str):
                full_analysis = json.loads(full_analysis)
                
            # Adicionar campos detalhados
            if "emotions" in full_analysis:
                result["emotions"] = full_analysis["emotions"]
            if "entities" in full_analysis:
                result["entities"] = full_analysis["entities"]
            if "keywords" in full_analysis:
                result["keywords"] = full_analysis["keywords"]
                
        return result


class ApiStats(Base):
    """Modelo para armazenar estatísticas da API"""
    __tablename__ = "api_stats"

    # Identificador único
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Data das estatísticas
    date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Número de requisições
    requests_count = Column(Integer, default=0, nullable=False)
    
    # Tempo médio de resposta em milissegundos
    avg_response_time_ms = Column(Float, default=0.0, nullable=False)
    
    # Número de erros
    error_count = Column(Integer, default=0, nullable=False)
    
    # Distribuição de tipos de análise (JSON)
    analysis_types = Column(JSON, nullable=True)
    
    # Distribuição de idiomas (JSON)
    language_distribution = Column(JSON, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Converte o modelo para um dicionário"""
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "requests_count": self.requests_count,
            "avg_response_time_ms": self.avg_response_time_ms,
            "error_count": self.error_count,
            "analysis_types": self.analysis_types,
            "language_distribution": self.language_distribution
        }