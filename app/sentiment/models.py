import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Float, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base

logger = logging.getLogger(__name__)


class SentimentAnalysis(Base):
    """Modelo para armazenar análises de sentimento."""
    
    __tablename__ = "sentiment_analyses"
    
    # Campos principais
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        comment="Identificador único da análise"
    )
    
    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Texto original analisado"
    )
    
    sentiment: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Sentimento identificado: positive, negative, neutral"
    )
    
    confidence: Mapped[float] = mapped_column(
        Float(),
        nullable=False,
        comment="Confiança do modelo (0.0 a 1.0)"
    )
    
    language: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
        comment="Código ISO do idioma detectado"
    )
    
    all_scores: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Scores detalhados de todos os sentimentos"
    )
    
    # Metadados temporais
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        comment="Timestamp de criação da análise"
    )
    
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        onupdate=func.now(),
        comment="Timestamp da última atualização"
    )
    
    # Configuração de índices para otimização de consultas
    __table_args__ = (
        # Índice composto para consultas por sentimento e data
        Index("idx_sentiment_created", "sentiment", "created_at"),
        
        # Índice para consultas por idioma
        Index("idx_language", "language"),
        
        # Índice para consultas por confiança (analytics)
        Index("idx_confidence", "confidence"),
        
        # Índice composto para filtros complexos
        Index("idx_sentiment_lang_date", "sentiment", "language", "created_at"),
        
        # Índice para busca por período
        Index("idx_created_at", "created_at"),
        
        # Configurações de tabela
        {
            "comment": "Armazena resultados de análises de sentimento",
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        }
    )
    
    def __repr__(self) -> str:
        return (
            f"<SentimentAnalysis("
            f"id='{self.id[:8]}...', "
            f"sentiment='{self.sentiment}', "
            f"confidence={self.confidence:.3f}, "
            f"language='{self.language}'"
            f")>"
        )
    
    def to_dict(self, include_text: bool = False) -> Dict[str, Any]:
        """
        Converte instância para dicionário.
        
        Args:
            include_text: Se deve incluir o texto original (padrão: False por privacidade)
            
        Returns:
            Dict com dados da análise
        """
        result = {
            "id": self.id,
            "sentiment": self.sentiment,
            "confidence": self.confidence,
            "language": self.language,
            "all_scores": self.all_scores,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_text:
            result["text"] = self.text
        else:
            # Incluir apenas preview do texto
            result["text_preview"] = (
                self.text[:100] + "..." 
                if self.text and len(self.text) > 100 
                else self.text
            )
            result["text_length"] = len(self.text) if self.text else 0
        
        return result
    
    def to_summary(self) -> Dict[str, Any]:
        """
        Converte para formato resumido (para listas e APIs).
        
        Returns:
            Dict com resumo da análise
        """
        return {
            "id": self.id,
            "sentiment": self.sentiment,
            "confidence": self.confidence,
            "language": self.language,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "text_length": len(self.text) if self.text else 0,
        }
    
    @classmethod
    def create_from_analysis(
        cls,
        text: str,
        sentiment: str,
        confidence: float,
        language: str,
        all_scores: Optional[List[Dict[str, Any]]] = None
    ) -> "SentimentAnalysis":
        """
        Factory method para criar instância a partir de resultado de análise.
        
        Args:
            text: Texto analisado
            sentiment: Sentimento identificado
            confidence: Confiança do modelo
            language: Idioma detectado
            all_scores: Scores detalhados opcionais
            
        Returns:
            Nova instância de SentimentAnalysis
        """
        return cls(
            text=text,
            sentiment=sentiment,
            confidence=confidence,
            language=language,
            all_scores=all_scores or []
        )
    
    @property
    def is_high_confidence(self) -> bool:
        """Verifica se análise tem alta confiança (>= 0.8)."""
        return self.confidence >= 0.8
    
    @property
    def is_neutral_tendency(self) -> bool:
        """Verifica se há tendência neutra (confidence < 0.6)."""
        return self.confidence < 0.6
    
    @property
    def dominant_score(self) -> Optional[Dict[str, Any]]:
        """Retorna o score dominante da análise."""
        if not self.all_scores:
            return None
        
        return max(self.all_scores, key=lambda x: x.get("score", 0.0))
    
    def get_secondary_sentiments(self) -> List[Dict[str, Any]]:
        """
        Retorna sentimentos secundários ordenados por score.
        
        Returns:
            Lista de sentimentos secundários (excluindo o dominante)
        """
        if not self.all_scores or len(self.all_scores) <= 1:
            return []
        
        # Ordenar por score decrescente e remover o primeiro (dominante)
        sorted_scores = sorted(
            self.all_scores, 
            key=lambda x: x.get("score", 0.0), 
            reverse=True
        )
        
        return sorted_scores[1:]
    
    def is_mixed_sentiment(self, threshold: float = 0.3) -> bool:
        """
        Verifica se há sentimento misto (múltiplos sentimentos com scores altos).
        
        Args:
            threshold: Limite mínimo para considerar score significativo
            
        Returns:
            True se há sentimento misto
        """
        if not self.all_scores or len(self.all_scores) < 2:
            return False
        
        significant_scores = [
            score for score in self.all_scores 
            if score.get("score", 0.0) >= threshold
        ]
        
        return len(significant_scores) >= 2
    
    def get_analysis_quality(self) -> str:
        """
        Avalia qualidade da análise baseada em confiança e distribuição de scores.
        
        Returns:
            String indicando qualidade: "high", "medium", "low"
        """
        if self.confidence >= 0.8:
            return "high"
        elif self.confidence >= 0.6:
            return "medium"
        else:
            return "low"
    
    @staticmethod
    def get_sentiment_distribution_query(session):
        """
        Query helper para distribuição de sentimentos.
        
        Args:
            session: Sessão SQLAlchemy
            
        Returns:
            Query para distribuição de sentimentos
        """
        return session.query(
            SentimentAnalysis.sentiment,
            func.count(SentimentAnalysis.id).label('count'),
            func.avg(SentimentAnalysis.confidence).label('avg_confidence')
        ).group_by(SentimentAnalysis.sentiment)
    
    @staticmethod
    def get_language_distribution_query(session):
        """
        Query helper para distribuição de idiomas.
        
        Args:
            session: Sessão SQLAlchemy
            
        Returns:
            Query para distribuição de idiomas
        """
        return session.query(
            SentimentAnalysis.language,
            func.count(SentimentAnalysis.id).label('count'),
            func.avg(SentimentAnalysis.confidence).label('avg_confidence')
        ).group_by(SentimentAnalysis.language)
    
    @staticmethod
    def get_daily_analytics_query(session, days: int = 30):
        """
        Query helper para analytics diárias.
        
        Args:
            session: Sessão SQLAlchemy
            days: Número de dias para análise
            
        Returns:
            Query para analytics diárias
        """
        cutoff_date = func.date_sub(func.now(), text(f"INTERVAL {days} DAY"))
        
        return session.query(
            func.date(SentimentAnalysis.created_at).label('date'),
            SentimentAnalysis.sentiment,
            func.count(SentimentAnalysis.id).label('count'),
            func.avg(SentimentAnalysis.confidence).label('avg_confidence')
        ).filter(
            SentimentAnalysis.created_at >= cutoff_date
        ).group_by(
            func.date(SentimentAnalysis.created_at),
            SentimentAnalysis.sentiment
        ).order_by(
            func.date(SentimentAnalysis.created_at).desc()
        )
    
    @staticmethod
    def get_high_confidence_analyses_query(session, confidence_threshold: float = 0.8):
        """
        Query helper para análises de alta confiança.
        
        Args:
            session: Sessão SQLAlchemy
            confidence_threshold: Limite de confiança
            
        Returns:
            Query para análises de alta confiança
        """
        return session.query(SentimentAnalysis).filter(
            SentimentAnalysis.confidence >= confidence_threshold
        ).order_by(SentimentAnalysis.confidence.desc())


# Modelo adicional para futuras funcionalidades (feedback, avaliação manual)
class SentimentFeedback(Base):
    """Modelo para armazenar feedback sobre análises de sentimento."""
    
    __tablename__ = "sentiment_feedback"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Identificador único do feedback"
    )
    
    analysis_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        comment="ID da análise original"
    )
    
    user_sentiment: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Sentimento indicado pelo usuário"
    )
    
    model_sentiment: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Sentimento original do modelo"
    )
    
    is_correct: Mapped[bool] = mapped_column(
        nullable=False,
        comment="Se o modelo acertou segundo o usuário"
    )
    
    feedback_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Notas adicionais do feedback"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        comment="Timestamp do feedback"
    )
    
    # Índices para analytics de feedback
    __table_args__ = (
        Index("idx_analysis_id", "analysis_id"),
        Index("idx_is_correct", "is_correct"),
        Index("idx_feedback_created", "created_at"),
        {
            "comment": "Armazena feedback de usuários sobre análises",
        }
    )
    
    def __repr__(self) -> str:
        return (
            f"<SentimentFeedback("
            f"analysis_id='{self.analysis_id[:8]}...', "
            f"correct={self.is_correct}"
            f")>"
        )


logger.info("Modelos de sentimento carregados")