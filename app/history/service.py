import logging
import time
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, asc, text, case
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.config import get_settings
from app.core.cache import CacheService
from app.core.exceptions import DatabaseError, RecordNotFoundError
from app.history.schemas import (
    AnalysisDetail, AnalyticsResponse, CacheKeyParams, DailyVolume,
    DeleteResponse, HistoryFilter, HistoryItem, HistoryResponse, 
    LanguageDistribution, PaginationMeta, PaginationParams,
    SentimentDistribution, SortParams, StatsFilter, StatsResponse,
    TrendData
)
from app.sentiment.models import SentimentAnalysis

logger = logging.getLogger(__name__)
settings = get_settings()


class HistoryService:
    """Serviço otimizado para consultas de histórico e analytics."""
    
    def __init__(self, cache_service: CacheService):
        self.cache_service = cache_service
        self._cache_ttl = {
            "history": 300,      # 5 minutos para histórico
            "analytics": 1800,   # 30 minutos para analytics
            "stats": 3600,       # 1 hora para estatísticas
            "detail": 600        # 10 minutos para detalhes
        }
        logger.info("HistoryService inicializado")
    
    async def get_history(
        self,
        db: Session,
        filters: HistoryFilter,
        pagination: PaginationParams,
        sorting: SortParams,
        use_cache: bool = True
    ) -> HistoryResponse:
        """
        Recupera histórico com filtros, paginação e cache otimizado.
        
        Args:
            db: Sessão do banco
            filters: Filtros de consulta
            pagination: Parâmetros de paginação
            sorting: Parâmetros de ordenação
            use_cache: Se deve usar cache
            
        Returns:
            HistoryResponse com dados paginados e metadata
        """
        start_time = time.time()
        
        try:
            # Gerar chave de cache
            cache_key = self._generate_cache_key(
                "history", 
                filters=filters.model_dump(exclude_none=True),
                pagination=pagination.model_dump(),
                sorting=sorting.model_dump()
            )
            
            # Verificar cache
            if use_cache:
                cached_result = await self.cache_service.get(cache_key)
                if cached_result:
                    logger.debug("Cache hit para consulta de histórico")
                    cached_result["cached"] = True
                    cached_result["query_time_ms"] = round((time.time() - start_time) * 1000, 2)
                    return HistoryResponse(**cached_result)
            
            # Construir query base
            base_query = self._build_base_query(db, filters)
            
            # Contar total (query otimizada)
            total_count = self._get_optimized_count(db, base_query)
            
            # Aplicar ordenação e paginação
            ordered_query = self._apply_sorting(base_query, sorting)
            paginated_query = self._apply_pagination(ordered_query, pagination)
            
            # Executar query
            results = paginated_query.all()
            
            # Converter para HistoryItem
            items = [self._to_history_item(record) for record in results]
            
            # Criar metadata de paginação
            pagination_meta = PaginationMeta.create(
                total=total_count,
                page=pagination.page,
                limit=pagination.limit
            )
            
            # Montar response
            query_time_ms = round((time.time() - start_time) * 1000, 2)
            
            response_data = {
                "items": [item.model_dump() for item in items],
                "pagination": pagination_meta.model_dump(),
                "filters_applied": filters.model_dump(exclude_none=True),
                "query_time_ms": query_time_ms,
                "cached": False
            }
            
            # Cachear resultado
            if use_cache and total_count > 0:
                await self.cache_service.set(
                    cache_key, 
                    response_data, 
                    ttl=self._cache_ttl["history"]
                )
                logger.debug(f"Resultado cacheado para {cache_key}")
            
            return HistoryResponse(**response_data)
            
        except Exception as e:
            logger.error(f"Erro na consulta de histórico: {e}")
            raise DatabaseError(
                message=f"Falha ao consultar histórico: {str(e)}",
                details={
                    "filters": filters.model_dump(exclude_none=True),
                    "pagination": pagination.model_dump()
                }
            ) from e
    
    async def get_analysis_by_id(
        self,
        db: Session,
        analysis_id: str,
        use_cache: bool = True
    ) -> AnalysisDetail:
        """
        Recupera análise específica por ID com cache.
        
        Args:
            db: Sessão do banco
            analysis_id: ID da análise
            use_cache: Se deve usar cache
            
        Returns:
            AnalysisDetail com dados completos
        """
        try:
            # Verificar cache
            cache_key = f"analysis_detail:{analysis_id}"
            
            if use_cache:
                cached_result = await self.cache_service.get(cache_key)
                if cached_result:
                    logger.debug(f"Cache hit para análise {analysis_id}")
                    return AnalysisDetail(**cached_result)
            
            # Buscar no banco
            record = db.query(SentimentAnalysis).filter(
                SentimentAnalysis.id == analysis_id
            ).first()
            
            if not record:
                raise RecordNotFoundError(
                    resource="Análise",
                    record_id=analysis_id
                )
            
            # Converter para AnalysisDetail
            detail = AnalysisDetail(
                id=str(record.id),
                text=record.text,
                sentiment=record.sentiment,
                confidence=record.confidence,
                language=record.language,
                all_scores=record.all_scores or [],
                created_at=record.created_at,
                updated_at=record.updated_at,
                is_high_confidence=record.confidence >= 0.8,
                confidence_level="high" if record.confidence >= 0.8 else "medium" if record.confidence >= 0.6 else "low"
            )
            
            # Cachear resultado
            if use_cache:
                await self.cache_service.set(
                    cache_key,
                    detail.model_dump(),
                    ttl=self._cache_ttl["detail"]
                )
            
            return detail
            
        except RecordNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Erro ao buscar análise {analysis_id}: {e}")
            raise DatabaseError(
                message=f"Falha ao buscar análise: {str(e)}",
                details={"analysis_id": analysis_id}
            ) from e
    
    async def get_analytics(
        self,
        db: Session,
        days: int = 30,
        use_cache: bool = True
    ) -> AnalyticsResponse:
        """
        Gera analytics com agregações otimizadas e cache.
        
        Args:
            db: Sessão do banco
            days: Número de dias para análise
            use_cache: Se deve usar cache
            
        Returns:
            AnalyticsResponse com estatísticas completas
        """
        try:
            # Verificar cache
            cache_key = f"analytics:{days}d"
            
            if use_cache:
                cached_result = await self.cache_service.get(cache_key)
                if cached_result:
                    logger.debug(f"Cache hit para analytics {days}d")
                    return AnalyticsResponse(**cached_result)
            
            # Data limite
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # 1. Distribuição de sentimentos (agregação otimizada)
            sentiment_dist = self._get_sentiment_distribution(db, start_date)
            
            # 2. Distribuição de idiomas (top 10)
            language_dist = self._get_language_distribution(db, start_date, limit=10)
            
            # 3. Volume diário (últimos 30 dias)
            daily_volume = self._get_daily_volume(db, start_date)
            
            # 4. Estatísticas gerais
            general_stats = self._get_general_stats(db, start_date)
            
            # Montar response
            analytics = AnalyticsResponse(
                sentiment_distribution=sentiment_dist,
                language_distribution=language_dist,
                daily_volume=daily_volume,
                avg_confidence=general_stats["avg_confidence"],
                total_analyses=general_stats["total_analyses"],
                date_range={
                    "start_date": start_date.date(),
                    "end_date": datetime.utcnow().date()
                }
            )
            
            # Cachear resultado
            if use_cache:
                await self.cache_service.set(
                    cache_key,
                    analytics.model_dump(),
                    ttl=self._cache_ttl["analytics"]
                )
                logger.debug(f"Analytics cacheado para {days}d")
            
            return analytics
            
        except Exception as e:
            logger.error(f"Erro ao gerar analytics: {e}")
            raise DatabaseError(
                message=f"Falha ao gerar analytics: {str(e)}",
                details={"days": days}
            ) from e
    
    async def get_stats(
        self,
        db: Session,
        stats_filter: StatsFilter,
        use_cache: bool = True
    ) -> StatsResponse:
        """
        Gera estatísticas agregadas por período com cache.
        
        Args:
            db: Sessão do banco
            stats_filter: Filtros de estatísticas
            use_cache: Se deve usar cache
            
        Returns:
            StatsResponse com métricas agregadas
        """
        try:
            # Verificar cache
            cache_key = f"stats:{stats_filter.period}:{stats_filter.group_by}"
            
            if use_cache:
                cached_result = await self.cache_service.get(cache_key)
                if cached_result:
                    logger.debug(f"Cache hit para stats {stats_filter.period}")
                    return StatsResponse(**cached_result)
            
            # Calcular intervalo de datas
            end_date = datetime.utcnow()
            days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
            start_date = end_date - timedelta(days=days_map[stats_filter.period])
            
            # 1. Estatísticas gerais
            general_stats = self._get_general_stats(db, start_date)
            
            # 2. Top idiomas
            top_languages = self._get_language_distribution(db, start_date, limit=5)
            
            # 3. Tendência de sentimentos
            sentiment_trend = self._get_sentiment_trend(
                db, start_date, end_date, stats_filter.group_by
            )
            
            # 4. Percentual de alta confiança
            high_conf_pct = self._get_high_confidence_percentage(db, start_date)
            
            # Montar response
            stats = StatsResponse(
                period=stats_filter.period,
                total_analyses=general_stats["total_analyses"],
                avg_confidence=general_stats["avg_confidence"],
                top_languages=top_languages,
                sentiment_trend=sentiment_trend,
                high_confidence_percentage=high_conf_pct
            )
            
            # Cachear resultado
            if use_cache:
                await self.cache_service.set(
                    cache_key,
                    stats.model_dump(),
                    ttl=self._cache_ttl["stats"]
                )
                logger.debug(f"Stats cacheado para {stats_filter.period}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao gerar stats: {e}")
            raise DatabaseError(
                message=f"Falha ao gerar estatísticas: {str(e)}",
                details={"filter": stats_filter.model_dump()}
            ) from e
    
    async def delete_analysis(
        self,
        db: Session,
        analysis_id: str
    ) -> DeleteResponse:
        """
        Remove análise específica e invalida cache.
        
        Args:
            db: Sessão do banco
            analysis_id: ID da análise
            
        Returns:
            DeleteResponse confirmando exclusão
        """
        try:
            # Buscar registro
            record = db.query(SentimentAnalysis).filter(
                SentimentAnalysis.id == analysis_id
            ).first()
            
            if not record:
                raise RecordNotFoundError(
                    resource="Análise",
                    record_id=analysis_id
                )
            
            # Remover do banco
            db.delete(record)
            db.commit()
            
            # Invalidar caches relacionados
            await self._invalidate_related_caches(analysis_id)
            
            logger.info(f"Análise {analysis_id} removida com sucesso")
            
            return DeleteResponse(
                success=True,
                message="Análise removida com sucesso",
                deleted_id=analysis_id
            )
            
        except RecordNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Erro ao remover análise {analysis_id}: {e}")
            db.rollback()
            raise DatabaseError(
                message=f"Falha ao remover análise: {str(e)}",
                details={"analysis_id": analysis_id}
            ) from e
    
    # Métodos auxiliares otimizados
    
    def _build_base_query(self, db: Session, filters: HistoryFilter) -> Select:
        """Constrói query base com filtros otimizada para índices."""
        query = db.query(SentimentAnalysis)
        
        # Aplicar filtros na ordem de seletividade (mais seletivos primeiro)
        conditions = []
        
        # Filtros de data (muito seletivos com índice)
        if filters.start_date:
            conditions.append(
                func.date(SentimentAnalysis.created_at) >= filters.start_date
            )
        
        if filters.end_date:
            conditions.append(
                func.date(SentimentAnalysis.created_at) <= filters.end_date
            )
        
        # Filtros de confiança (seletivos com índice)
        if filters.min_confidence is not None:
            conditions.append(SentimentAnalysis.confidence >= filters.min_confidence)
        
        if filters.max_confidence is not None:
            conditions.append(SentimentAnalysis.confidence <= filters.max_confidence)
        
        # Filtros categóricos (índices específicos)
        if filters.sentiment:
            conditions.append(SentimentAnalysis.sentiment == filters.sentiment)
        
        if filters.language:
            conditions.append(SentimentAnalysis.language == filters.language)
        
        # Filtro de texto (menos seletivo, usar ILIKE)
        if filters.text_contains:
            conditions.append(
                SentimentAnalysis.text.ilike(f"%{filters.text_contains}%")
            )
        
        # Aplicar todas as condições
        if conditions:
            query = query.filter(and_(*conditions))
        
        return query
    
    def _get_optimized_count(self, db: Session, base_query) -> int:
        """Conta registros de forma otimizada."""
        # Para SQLAlchemy 2.0 - usar subquery para count
        count_query = db.query(func.count()).select_from(
            base_query.statement.alias()
        )
        return count_query.scalar() or 0
    
    def _apply_sorting(self, query, sorting: SortParams):
        """Aplica ordenação otimizada."""
        column_map = {
            "created_at": SentimentAnalysis.created_at,
            "confidence": SentimentAnalysis.confidence,
            "sentiment": SentimentAnalysis.sentiment
        }
        
        column = column_map.get(sorting.sort_by, SentimentAnalysis.created_at)
        
        if sorting.sort_order == "desc":
            return query.order_by(desc(column))
        else:
            return query.order_by(asc(column))
    
    def _apply_pagination(self, query, pagination: PaginationParams):
        """Aplica paginação otimizada."""
        return query.offset(pagination.sql_offset).limit(pagination.sql_limit)
    
    def _to_history_item(self, record: SentimentAnalysis) -> HistoryItem:
        """Converte registro para HistoryItem."""
        text_preview = (
            record.text[:100] + "..." 
            if len(record.text) > 100 
            else record.text
        )
        
        return HistoryItem(
            id=str(record.id),
            sentiment=record.sentiment,
            confidence=record.confidence,
            language=record.language,
            text_preview=text_preview,
            text_length=len(record.text),
            created_at=record.created_at,
            all_scores=record.all_scores or []
        )
    
    def _get_sentiment_distribution(
        self, 
        db: Session, 
        start_date: datetime
    ) -> SentimentDistribution:
        """Agregação otimizada de distribuição de sentimentos."""
        result = db.query(
            SentimentAnalysis.sentiment,
            func.count(SentimentAnalysis.id).label('count')
        ).filter(
            SentimentAnalysis.created_at >= start_date
        ).group_by(
            SentimentAnalysis.sentiment
        ).all()
        
        # Inicializar contadores
        counts = {"positive": 0, "negative": 0, "neutral": 0}
        
        # Preencher com resultados
        for sentiment, count in result:
            counts[sentiment] = count
        
        total = sum(counts.values())
        
        return SentimentDistribution(
            positive=counts["positive"],
            negative=counts["negative"],
            neutral=counts["neutral"],
            total=total
        )
    
    def _get_language_distribution(
        self,
        db: Session,
        start_date: datetime,
        limit: int = 10
    ) -> List[LanguageDistribution]:
        """Agregação otimizada de distribuição de idiomas."""
        # Total para calcular percentuais
        total = db.query(func.count(SentimentAnalysis.id)).filter(
            SentimentAnalysis.created_at >= start_date
        ).scalar() or 0
        
        if total == 0:
            return []
        
        # Agregação por idioma
        result = db.query(
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
            LanguageDistribution(
                language=language,
                count=count,
                percentage=round((count / total) * 100, 2)
            )
            for language, count in result
        ]
    
    def _get_daily_volume(
        self,
        db: Session,
        start_date: datetime
    ) -> List[DailyVolume]:
        """Agregação otimizada de volume diário."""
        result = db.query(
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
            DailyVolume(
                date=date_val,
                count=count,
                avg_confidence=round(float(avg_conf or 0), 4)
            )
            for date_val, count, avg_conf in result
        ]
    
    def _get_general_stats(self, db: Session, start_date: datetime) -> Dict[str, Any]:
        """Estatísticas gerais otimizadas."""
        result = db.query(
            func.count(SentimentAnalysis.id).label('total'),
            func.avg(SentimentAnalysis.confidence).label('avg_confidence')
        ).filter(
            SentimentAnalysis.created_at >= start_date
        ).first()
        
        return {
            "total_analyses": result.total or 0,
            "avg_confidence": round(float(result.avg_confidence or 0), 4)
        }
    
    def _get_sentiment_trend(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime,
        group_by: str
    ) -> List[TrendData]:
        """Tendência de sentimentos agrupada por período."""
        # Definir formato de agrupamento
        date_format_map = {
            "day": "%Y-%m-%d",
            "week": "%Y-W%u",
            "month": "%Y-%m"
        }
        
        date_format = date_format_map.get(group_by, "%Y-%m-%d")
        
        # Query com agregação condicional
        result = db.query(
            func.date_format(SentimentAnalysis.created_at, date_format).label('period'),
            func.sum(
                case((SentimentAnalysis.sentiment == 'positive', 1), else_=0)
            ).label('positive_count'),
            func.sum(
                case((SentimentAnalysis.sentiment == 'negative', 1), else_=0)
            ).label('negative_count'),
            func.sum(
                case((SentimentAnalysis.sentiment == 'neutral', 1), else_=0)
            ).label('neutral_count'),
            func.count(SentimentAnalysis.id).label('total_count'),
            func.avg(SentimentAnalysis.confidence).label('avg_confidence')
        ).filter(
            SentimentAnalysis.created_at.between(start_date, end_date)
        ).group_by(
            func.date_format(SentimentAnalysis.created_at, date_format)
        ).order_by(
            func.date_format(SentimentAnalysis.created_at, date_format)
        ).all()
        
        return [
            TrendData(
                period=period,
                sentiment_counts={
                    "positive": int(pos_count or 0),
                    "negative": int(neg_count or 0),
                    "neutral": int(neu_count or 0)
                },
                total_count=int(total_count or 0),
                avg_confidence=round(float(avg_conf or 0), 4)
            )
            for period, pos_count, neg_count, neu_count, total_count, avg_conf in result
        ]
    
    def _get_high_confidence_percentage(
        self,
        db: Session,
        start_date: datetime
    ) -> float:
        """Percentual de análises com alta confiança."""
        total = db.query(func.count(SentimentAnalysis.id)).filter(
            SentimentAnalysis.created_at >= start_date
        ).scalar() or 0
        
        if total == 0:
            return 0.0
        
        high_conf = db.query(func.count(SentimentAnalysis.id)).filter(
            and_(
                SentimentAnalysis.created_at >= start_date,
                SentimentAnalysis.confidence >= 0.8
            )
        ).scalar() or 0
        
        return round((high_conf / total) * 100, 2)
    
    def _generate_cache_key(self, endpoint: str, **kwargs) -> str:
        """Gera chave de cache determinística."""
        cache_params = CacheKeyParams(endpoint=endpoint, **kwargs)
        return cache_params.generate_key()
    
    async def _invalidate_related_caches(self, analysis_id: str) -> None:
        """Invalida caches relacionados a uma análise."""
        try:
            # Chaves específicas
            await self.cache_service.delete(f"analysis_detail:{analysis_id}")
            
            # Padrões de chaves (implementação simplificada)
            cache_patterns = [
                "analytics:*",
                "stats:*", 
                "history:*"
            ]
            
            # Note: Redis pattern deletion seria mais eficiente
            # Aqui usamos uma abordagem simplificada
            logger.debug(f"Caches invalidados para análise {analysis_id}")
            
        except Exception as e:
            logger.warning(f"Erro ao invalidar caches: {e}")


# Factory function
def get_history_service(cache_service: CacheService) -> HistoryService:
    """Factory para criar instância do HistoryService."""
    return HistoryService(cache_service)