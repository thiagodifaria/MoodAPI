"""
Repository para operações de banco de dados do módulo de sentimentos.

Separa a lógica de persistência dos serviços de negócio.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import DatabaseError, RecordNotFoundError
from app.sentiment.models import SentimentAnalysis

logger = logging.getLogger(__name__)


class SentimentRepository:
    """Repository para operações de SentimentAnalysis."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, analysis: SentimentAnalysis) -> SentimentAnalysis:
        """
        Cria nova análise no banco.
        
        Args:
            analysis: Entidade SentimentAnalysis
            
        Returns:
            Entidade persistida com ID gerado
        """
        try:
            self.db.add(analysis)
            self.db.commit()
            self.db.refresh(analysis)
            logger.debug(f"Análise criada: {analysis.id}")
            return analysis
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao criar análise: {e}")
            raise DatabaseError(f"Falha ao salvar análise: {e}") from e
    
    def get_by_id(self, id: str) -> Optional[SentimentAnalysis]:
        """
        Busca análise por ID.
        
        Args:
            id: ID da análise
            
        Returns:
            SentimentAnalysis ou None
        """
        try:
            return self.db.query(SentimentAnalysis).filter(
                SentimentAnalysis.id == id
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar análise {id}: {e}")
            raise DatabaseError(f"Falha ao buscar análise: {e}") from e
    
    def get_by_id_or_raise(self, id: str) -> SentimentAnalysis:
        """
        Busca análise por ID ou levanta exceção.
        
        Args:
            id: ID da análise
            
        Returns:
            SentimentAnalysis
            
        Raises:
            RecordNotFoundError: Se não encontrar
        """
        analysis = self.get_by_id(id)
        if not analysis:
            raise RecordNotFoundError(resource="Análise", record_id=id)
        return analysis
    
    def delete(self, id: str) -> bool:
        """
        Remove análise por ID.
        
        Args:
            id: ID da análise
            
        Returns:
            True se removido
        """
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
    
    def find_by_text_hash(self, text_hash: str) -> Optional[SentimentAnalysis]:
        """
        Busca análise por hash do texto (para evitar duplicatas).
        
        Args:
            text_hash: Hash SHA256 do texto
            
        Returns:
            SentimentAnalysis ou None
        """
        # Nota: Requer campo text_hash no modelo para funcionar
        # Por ora, busca por texto exato (limitado)
        return None
    
    def get_paginated(
        self,
        page: int = 1,
        limit: int = 50,
        sentiment: Optional[str] = None,
        language: Optional[str] = None,
        min_confidence: Optional[float] = None,
        max_confidence: Optional[float] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[SentimentAnalysis], int]:
        """
        Busca paginada com filtros.
        
        Returns:
            Tupla (lista de análises, total)
        """
        try:
            query = self.db.query(SentimentAnalysis)
            
            # Aplicar filtros
            conditions = []
            
            if sentiment:
                conditions.append(SentimentAnalysis.sentiment == sentiment)
            
            if language:
                conditions.append(SentimentAnalysis.language == language)
            
            if min_confidence is not None:
                conditions.append(SentimentAnalysis.confidence >= min_confidence)
            
            if max_confidence is not None:
                conditions.append(SentimentAnalysis.confidence <= max_confidence)
            
            if start_date:
                conditions.append(SentimentAnalysis.created_at >= start_date)
            
            if end_date:
                conditions.append(SentimentAnalysis.created_at <= end_date)
            
            if conditions:
                query = query.filter(and_(*conditions))
            
            # Total
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
                query = query.order_by(column)
            
            # Paginação
            offset = (page - 1) * limit
            results = query.offset(offset).limit(limit).all()
            
            return results, total
            
        except SQLAlchemyError as e:
            logger.error(f"Erro na consulta paginada: {e}")
            raise DatabaseError(f"Falha na consulta: {e}") from e
    
    def get_recent(self, limit: int = 10) -> List[SentimentAnalysis]:
        """Retorna análises mais recentes."""
        try:
            return self.db.query(SentimentAnalysis).order_by(
                desc(SentimentAnalysis.created_at)
            ).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar recentes: {e}")
            raise DatabaseError(f"Falha ao buscar: {e}") from e
    
    def count_by_sentiment(
        self,
        start_date: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Conta análises por sentimento."""
        try:
            query = self.db.query(
                SentimentAnalysis.sentiment,
                func.count(SentimentAnalysis.id).label('count')
            )
            
            if start_date:
                query = query.filter(SentimentAnalysis.created_at >= start_date)
            
            result = query.group_by(SentimentAnalysis.sentiment).all()
            
            counts = {"positive": 0, "negative": 0, "neutral": 0}
            for sentiment, count in result:
                counts[sentiment] = count
            
            return counts
            
        except SQLAlchemyError as e:
            logger.error(f"Erro ao contar por sentimento: {e}")
            raise DatabaseError(f"Falha na contagem: {e}") from e
    
    def get_statistics(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """Retorna estatísticas agregadas."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            result = self.db.query(
                func.count(SentimentAnalysis.id).label('total'),
                func.avg(SentimentAnalysis.confidence).label('avg_confidence')
            ).filter(
                SentimentAnalysis.created_at >= start_date
            ).first()
            
            return {
                "total": result.total or 0,
                "avg_confidence": round(float(result.avg_confidence or 0), 4),
                "period_days": days
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar estatísticas: {e}")
            raise DatabaseError(f"Falha nas estatísticas: {e}") from e


def get_sentiment_repository(db: Session) -> SentimentRepository:
    """Factory para criar repository."""
    return SentimentRepository(db)
