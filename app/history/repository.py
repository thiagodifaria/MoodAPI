"""
Repository para operações de banco de dados do módulo de histórico.

Separa a lógica de persistência dos serviços de negócio.
"""
import logging
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, asc
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import DatabaseError, RecordNotFoundError
from app.sentiment.models import SentimentAnalysis

logger = logging.getLogger(__name__)


class HistoryRepository:
    """Repository para operações de histórico e analytics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, id: str) -> Optional[SentimentAnalysis]:
        """Busca análise por ID."""
        try:
            return self.db.query(SentimentAnalysis).filter(
                SentimentAnalysis.id == id
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar análise {id}: {e}")
            raise DatabaseError(f"Falha ao buscar análise: {e}") from e
    
    def get_by_id_or_raise(self, id: str) -> SentimentAnalysis:
        """Busca análise por ID ou levanta exceção."""
        analysis = self.get_by_id(id)
        if not analysis:
            raise RecordNotFoundError(resource="Análise", record_id=id)
        return analysis
    
    def delete(self, id: str) -> bool:
        """Remove análise por ID."""
        try:
            analysis = self.get_by_id_or_raise(id)
            self.db.delete(analysis)
            self.db.commit()
            logger.debug(f"Análise removida: {id}")
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao remover análise {id}: {e}")
            raise DatabaseError(f"Falha ao remover análise: {e}") from e
    
    def get_paginated(
        self,
        sentiment: Optional[str] = None,
        language: Optional[str] = None,
        min_confidence: Optional[float] = None,
        max_confidence: Optional[float] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        text_contains: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[SentimentAnalysis], int]:
        """
        Busca paginada com filtros otimizada.
        
        Returns:
            Tupla (lista de análises, total)
        """
        try:
            query = self.db.query(SentimentAnalysis)
            
            # Aplicar filtros na ordem de seletividade
            conditions = []
            
            # Filtros de data (índice disponível)
            if start_date:
                conditions.append(func.date(SentimentAnalysis.created_at) >= start_date)
            
            if end_date:
                conditions.append(func.date(SentimentAnalysis.created_at) <= end_date)
            
            # Filtros de confiança (índice disponível)
            if min_confidence is not None:
                conditions.append(SentimentAnalysis.confidence >= min_confidence)
            
            if max_confidence is not None:
                conditions.append(SentimentAnalysis.confidence <= max_confidence)
            
            # Filtros categóricos (índice disponível)
            if sentiment:
                conditions.append(SentimentAnalysis.sentiment == sentiment)
            
            if language:
                conditions.append(SentimentAnalysis.language == language)
            
            # Filtro de texto (full scan, menos eficiente)
            if text_contains:
                conditions.append(
                    SentimentAnalysis.text.ilike(f"%{text_contains}%")
                )
            
            if conditions:
                query = query.filter(and_(*conditions))
            
            # Total otimizado
            total = query.count()
            
            # Ordenação
            column_map = {
                "created_at": SentimentAnalysis.created_at,
                "confidence": SentimentAnalysis.confidence,
                "sentiment": SentimentAnalysis.sentiment
            }
            column = column_map.get(sort_by, SentimentAnalysis.created_at)
            
            if sort_order == "desc":
                query = query.order_by(desc(column))
            else:
                query = query.order_by(asc(column))
            
            # Paginação
            offset = (page - 1) * limit
            results = query.offset(offset).limit(limit).all()
            
            return results, total
            
        except SQLAlchemyError as e:
            logger.error(f"Erro na consulta paginada: {e}")
            raise DatabaseError(f"Falha na consulta: {e}") from e
    
    def get_sentiment_distribution(
        self,
        start_date: datetime
    ) -> Dict[str, int]:
        """Agregação de distribuição de sentimentos."""
        try:
            result = self.db.query(
                SentimentAnalysis.sentiment,
                func.count(SentimentAnalysis.id).label('count')
            ).filter(
                SentimentAnalysis.created_at >= start_date
            ).group_by(
                SentimentAnalysis.sentiment
            ).all()
            
            counts = {"positive": 0, "negative": 0, "neutral": 0}
            for sentiment, count in result:
                counts[sentiment] = count
            
            return counts
            
        except SQLAlchemyError as e:
            logger.error(f"Erro na distribuição de sentimentos: {e}")
            raise DatabaseError(f"Falha na agregação: {e}") from e
    
    def get_language_distribution(
        self,
        start_date: datetime,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Agregação de distribuição de idiomas."""
        try:
            total = self.db.query(func.count(SentimentAnalysis.id)).filter(
                SentimentAnalysis.created_at >= start_date
            ).scalar() or 0
            
            if total == 0:
                return []
            
            result = self.db.query(
                SentimentAnalysis.language,
                func.count(SentimentAnalysis.id).label('count')
            ).filter(
                SentimentAnalysis.created_at >= start_date
            ).group_by(
                SentimentAnalysis.language
            ).order_by(
                desc(func.count(SentimentAnalysis.id))
            ).limit(limit).all()
            
            return [
                {
                    "language": lang,
                    "count": count,
                    "percentage": round((count / total) * 100, 2)
                }
                for lang, count in result
            ]
            
        except SQLAlchemyError as e:
            logger.error(f"Erro na distribuição de idiomas: {e}")
            raise DatabaseError(f"Falha na agregação: {e}") from e
    
    def get_daily_volume(
        self,
        start_date: datetime
    ) -> List[Dict[str, Any]]:
        """Agregação de volume diário."""
        try:
            result = self.db.query(
                func.date(SentimentAnalysis.created_at).label('date'),
                func.count(SentimentAnalysis.id).label('count'),
                func.avg(SentimentAnalysis.confidence).label('avg_confidence')
            ).filter(
                SentimentAnalysis.created_at >= start_date
            ).group_by(
                func.date(SentimentAnalysis.created_at)
            ).order_by(
                func.date(SentimentAnalysis.created_at)
            ).all()
            
            return [
                {
                    "date": date_val,
                    "count": count,
                    "avg_confidence": round(float(avg_conf or 0), 4)
                }
                for date_val, count, avg_conf in result
            ]
            
        except SQLAlchemyError as e:
            logger.error(f"Erro no volume diário: {e}")
            raise DatabaseError(f"Falha na agregação: {e}") from e
    
    def get_general_stats(
        self,
        start_date: datetime
    ) -> Dict[str, Any]:
        """Estatísticas gerais."""
        try:
            result = self.db.query(
                func.count(SentimentAnalysis.id).label('total'),
                func.avg(SentimentAnalysis.confidence).label('avg_confidence')
            ).filter(
                SentimentAnalysis.created_at >= start_date
            ).first()
            
            return {
                "total_analyses": result.total or 0,
                "avg_confidence": round(float(result.avg_confidence or 0), 4)
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Erro nas estatísticas gerais: {e}")
            raise DatabaseError(f"Falha nas estatísticas: {e}") from e
    
    def get_high_confidence_percentage(
        self,
        start_date: datetime,
        threshold: float = 0.8
    ) -> float:
        """Percentual de análises com alta confiança."""
        try:
            total = self.db.query(func.count(SentimentAnalysis.id)).filter(
                SentimentAnalysis.created_at >= start_date
            ).scalar() or 0
            
            if total == 0:
                return 0.0
            
            high_conf = self.db.query(func.count(SentimentAnalysis.id)).filter(
                and_(
                    SentimentAnalysis.created_at >= start_date,
                    SentimentAnalysis.confidence >= threshold
                )
            ).scalar() or 0
            
            return round((high_conf / total) * 100, 2)
            
        except SQLAlchemyError as e:
            logger.error(f"Erro no cálculo de alta confiança: {e}")
            raise DatabaseError(f"Falha no cálculo: {e}") from e


def get_history_repository(db: Session) -> HistoryRepository:
    """Factory para criar repository."""
    return HistoryRepository(db)
