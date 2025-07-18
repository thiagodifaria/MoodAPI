import time
from typing import Annotated

from fastapi import (
    APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
)
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.core.cache import CacheService
from app.core.exceptions import (
    DatabaseError, RecordNotFoundError, RateLimitError
)
from app.dependencies import get_cache_dependency, get_db_session
from app.history.schemas import (
    AnalysisDetail, AnalyticsResponse, DeleteResponse, HistoryFilter,
    HistoryResponse, PaginationParams, SortParams, StatsFilter, StatsResponse
)
from app.history.service import HistoryService, get_history_service
from app.shared.rate_limiter import rate_limit

# Router com configuração otimizada
router = APIRouter(
    prefix="/api/v1/history",
    tags=["history-analytics"],
    responses={
        429: {"description": "Rate limit excedido"},
        500: {"description": "Erro interno do servidor"},
        503: {"description": "Serviço indisponível"}
    }
)


def get_service(
    cache: CacheService = Depends(get_cache_dependency)
) -> HistoryService:
    """Dependency para obter serviço de histórico."""
    return get_history_service(cache)


async def log_query_stats(
    endpoint: str,
    success: bool,
    query_time: float,
    total_results: int = 0,
    cached: bool = False
) -> None:
    """Background task para logging de estatísticas de consultas."""
    import logging
    
    logger = logging.getLogger("history_analytics")
    
    try:
        stats = {
            "endpoint": endpoint,
            "success": success,
            "query_time_ms": query_time,
            "total_results": total_results,
            "cached": cached,
            "timestamp": time.time()
        }
        
        logger.info(f"Query Analytics: {stats}")
        
    except Exception as e:
        logger.error(f"Erro no logging de analytics: {e}")


async def handle_history_error(error: Exception, request_id: str) -> HTTPException:
    """Converte erros de histórico para HTTPException."""
    if isinstance(error, RecordNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "RECORD_NOT_FOUND",
                "message": str(error),
                "request_id": request_id
            }
        )
    
    elif isinstance(error, DatabaseError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "DATABASE_ERROR",
                "message": "Erro temporário no banco de dados",
                "request_id": request_id
            }
        )
    
    elif isinstance(error, RateLimitError):
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "RATE_LIMIT_EXCEEDED",
                "message": str(error),
                "request_id": request_id
            }
        )
    
    else:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "Erro interno do servidor",
                "request_id": request_id
            }
        )


@router.get(
    "",
    response_model=HistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar histórico de análises",
    description="Recupera histórico de análises com filtros flexíveis e paginação otimizada",
    response_description="Lista paginada de análises com metadata"
)
@rate_limit(requests_per_minute=60, requests_per_hour=500)
async def get_history(
    background_tasks: BackgroundTasks,
    http_request: Request,
    db: Session = Depends(get_db_session),
    service: HistoryService = Depends(get_service),
    settings: Settings = Depends(get_settings),
    # Filtros usando Depends para Query parameters
    sentiment: Annotated[
        str | None,
        Query(
            description="Filtrar por sentimento",
            regex="^(positive|negative|neutral)$"
        )
    ] = None,
    language: Annotated[
        str | None,
        Query(
            description="Filtrar por idioma (código ISO)",
            min_length=2,
            max_length=5
        )
    ] = None,
    min_confidence: Annotated[
        float | None,
        Query(
            description="Confiança mínima",
            ge=0.0,
            le=1.0
        )
    ] = None,
    max_confidence: Annotated[
        float | None,
        Query(
            description="Confiança máxima",
            ge=0.0,
            le=1.0
        )
    ] = None,
    start_date: Annotated[
        str | None,
        Query(
            description="Data inicial (YYYY-MM-DD)",
            regex=r"^\d{4}-\d{2}-\d{2}$"
        )
    ] = None,
    end_date: Annotated[
        str | None,
        Query(
            description="Data final (YYYY-MM-DD)",
            regex=r"^\d{4}-\d{2}-\d{2}$"
        )
    ] = None,
    text_contains: Annotated[
        str | None,
        Query(
            description="Buscar texto que contenha",
            min_length=2,
            max_length=100
        )
    ] = None,
    # Paginação
    page: Annotated[
        int,
        Query(
            description="Número da página",
            ge=1,
            le=10000
        )
    ] = 1,
    limit: Annotated[
        int,
        Query(
            description="Itens por página",
            ge=1,
            le=500
        )
    ] = 50,
    # Ordenação
    sort_by: Annotated[
        str,
        Query(
            description="Campo para ordenação",
            regex="^(created_at|confidence|sentiment)$"
        )
    ] = "created_at",
    sort_order: Annotated[
        str,
        Query(
            description="Direção da ordenação",
            regex="^(asc|desc)$"
        )
    ] = "desc"
) -> HistoryResponse:
    """
    Consulta histórico de análises com filtros flexíveis.
    
    - **sentiment**: Filtrar por sentimento (positive/negative/neutral)
    - **language**: Filtrar por código de idioma
    - **min_confidence/max_confidence**: Filtrar por faixa de confiança
    - **start_date/end_date**: Filtrar por período (formato YYYY-MM-DD)
    - **text_contains**: Buscar texto que contenha substring
    - **page/limit**: Paginação (página 1-based, limite máximo 500)
    - **sort_by/sort_order**: Ordenação por campo e direção
    
    Retorna lista paginada com metadata completa e suporte a cache.
    """
    start_time = time.time()
    request_id = getattr(http_request.state, "request_id", "unknown")
    
    try:
        # Converter datas se fornecidas
        from datetime import datetime
        
        parsed_start_date = None
        parsed_end_date = None
        
        if start_date:
            parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        if end_date:
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        # Construir filtros
        filters = HistoryFilter(
            sentiment=sentiment,
            language=language,
            min_confidence=min_confidence,
            max_confidence=max_confidence,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            text_contains=text_contains
        )
        
        # Parâmetros de paginação e ordenação
        pagination = PaginationParams(page=page, limit=limit)
        sorting = SortParams(sort_by=sort_by, sort_order=sort_order)
        
        # Executar consulta
        result = await service.get_history(
            db=db,
            filters=filters,
            pagination=pagination,
            sorting=sorting,
            use_cache=True
        )
        
        # Background analytics
        query_time = (time.time() - start_time) * 1000
        background_tasks.add_task(
            log_query_stats,
            endpoint="get_history",
            success=True,
            query_time=query_time,
            total_results=result.pagination.total,
            cached=result.cached
        )
        
        return result
        
    except Exception as error:
        # Background analytics para erro
        query_time = (time.time() - start_time) * 1000
        background_tasks.add_task(
            log_query_stats,
            endpoint="get_history",
            success=False,
            query_time=query_time
        )
        
        raise await handle_history_error(error, request_id)


@router.get(
    "/{analysis_id}",
    response_model=AnalysisDetail,
    status_code=status.HTTP_200_OK,
    summary="Obter análise específica",
    description="Recupera detalhes completos de uma análise por ID",
    response_description="Dados completos da análise incluindo texto original"
)
@rate_limit(requests_per_minute=100, requests_per_hour=1000)
async def get_analysis_by_id(
    analysis_id: str,
    background_tasks: BackgroundTasks,
    http_request: Request,
    db: Session = Depends(get_db_session),
    service: HistoryService = Depends(get_service)
) -> AnalysisDetail:
    """
    Recupera análise específica por ID.
    
    - **analysis_id**: ID único da análise
    
    Retorna dados completos incluindo texto original, sentimento,
    confiança, idioma e todos os scores detalhados.
    """
    start_time = time.time()
    request_id = getattr(http_request.state, "request_id", "unknown")
    
    try:
        result = await service.get_analysis_by_id(
            db=db,
            analysis_id=analysis_id,
            use_cache=True
        )
        
        # Background analytics
        query_time = (time.time() - start_time) * 1000
        background_tasks.add_task(
            log_query_stats,
            endpoint="get_analysis_detail",
            success=True,
            query_time=query_time,
            total_results=1
        )
        
        return result
        
    except Exception as error:
        query_time = (time.time() - start_time) * 1000
        background_tasks.add_task(
            log_query_stats,
            endpoint="get_analysis_detail",
            success=False,
            query_time=query_time
        )
        
        raise await handle_history_error(error, request_id)


@router.get(
    "/../analytics",
    response_model=AnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Obter analytics de sentimentos",
    description="Gera estatísticas e distribuições para dashboards",
    response_description="Analytics completos com distribuições e métricas"
)
@rate_limit(requests_per_minute=20, requests_per_hour=200)  # Limite menor para analytics
async def get_analytics(
    background_tasks: BackgroundTasks,
    http_request: Request,
    db: Session = Depends(get_db_session),
    service: HistoryService = Depends(get_service),
    days: Annotated[
        int,
        Query(
            description="Número de dias para análise",
            ge=1,
            le=365
        )
    ] = 30
) -> AnalyticsResponse:
    """
    Gera analytics completos para dashboards.
    
    - **days**: Período em dias para análise (1-365, padrão: 30)
    
    Retorna:
    - Distribuição de sentimentos
    - Distribuição de idiomas (top 10)
    - Volume diário dos últimos 30 dias
    - Confiança média
    - Total de análises
    - Intervalo de datas analisado
    
    **Cache**: Resultados são cacheados por 30 minutos para otimização.
    """
    start_time = time.time()
    request_id = getattr(http_request.state, "request_id", "unknown")
    
    try:
        result = await service.get_analytics(
            db=db,
            days=days,
            use_cache=True
        )
        
        # Background analytics
        query_time = (time.time() - start_time) * 1000
        background_tasks.add_task(
            log_query_stats,
            endpoint="get_analytics",
            success=True,
            query_time=query_time,
            total_results=result.total_analyses
        )
        
        return result
        
    except Exception as error:
        query_time = (time.time() - start_time) * 1000
        background_tasks.add_task(
            log_query_stats,
            endpoint="get_analytics",
            success=False,
            query_time=query_time
        )
        
        raise await handle_history_error(error, request_id)


@router.get(
    "/../stats",
    response_model=StatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Obter estatísticas agregadas",
    description="Gera métricas agregadas por período com tendências",
    response_description="Estatísticas agregadas com tendências temporais"
)
@rate_limit(requests_per_minute=15, requests_per_hour=150)  # Limite ainda menor para stats
async def get_stats(
    background_tasks: BackgroundTasks,
    http_request: Request,
    db: Session = Depends(get_db_session),
    service: HistoryService = Depends(get_service),
    period: Annotated[
        str,
        Query(
            description="Período para estatísticas",
            regex="^(7d|30d|90d|1y)$"
        )
    ] = "30d",
    group_by: Annotated[
        str,
        Query(
            description="Agrupamento temporal",
            regex="^(day|week|month)$"
        )
    ] = "day"
) -> StatsResponse:
    """
    Gera estatísticas agregadas por período.
    
    - **period**: Período de análise (7d/30d/90d/1y)
    - **group_by**: Agrupamento temporal (day/week/month)
    
    Retorna:
    - Total de análises no período
    - Confiança média
    - Top 5 idiomas
    - Tendência de sentimentos agrupada
    - Percentual de alta confiança (>0.8)
    
    **Cache**: Resultados são cacheados por 1 hora.
    """
    start_time = time.time()
    request_id = getattr(http_request.state, "request_id", "unknown")
    
    try:
        stats_filter = StatsFilter(period=period, group_by=group_by)
        
        result = await service.get_stats(
            db=db,
            stats_filter=stats_filter,
            use_cache=True
        )
        
        # Background analytics
        query_time = (time.time() - start_time) * 1000
        background_tasks.add_task(
            log_query_stats,
            endpoint="get_stats",
            success=True,
            query_time=query_time,
            total_results=result.total_analyses
        )
        
        return result
        
    except Exception as error:
        query_time = (time.time() - start_time) * 1000
        background_tasks.add_task(
            log_query_stats,
            endpoint="get_stats",
            success=False,
            query_time=query_time
        )
        
        raise await handle_history_error(error, request_id)


@router.delete(
    "/{analysis_id}",
    response_model=DeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Remover análise",
    description="Remove análise específica e invalida caches relacionados",
    response_description="Confirmação da remoção"
)
@rate_limit(requests_per_minute=30, requests_per_hour=300)
async def delete_analysis(
    analysis_id: str,
    background_tasks: BackgroundTasks,
    http_request: Request,
    db: Session = Depends(get_db_session),
    service: HistoryService = Depends(get_service)
) -> DeleteResponse:
    """
    Remove análise específica.
    
    - **analysis_id**: ID único da análise a ser removida
    
    **Atenção**: Esta operação é irreversível e invalidará
    caches relacionados para manter consistência.
    """
    start_time = time.time()
    request_id = getattr(http_request.state, "request_id", "unknown")
    
    try:
        result = await service.delete_analysis(
            db=db,
            analysis_id=analysis_id
        )
        
        # Background analytics
        query_time = (time.time() - start_time) * 1000
        background_tasks.add_task(
            log_query_stats,
            endpoint="delete_analysis",
            success=True,
            query_time=query_time,
            total_results=1
        )
        
        return result
        
    except Exception as error:
        query_time = (time.time() - start_time) * 1000
        background_tasks.add_task(
            log_query_stats,
            endpoint="delete_analysis",
            success=False,
            query_time=query_time
        )
        
        raise await handle_history_error(error, request_id)


@router.get(
    "/../health",
    summary="Health check do módulo de histórico",
    description="Verifica saúde dos componentes de histórico e analytics",
    tags=["health"]
)
async def history_health_check(
    db: Session = Depends(get_db_session),
    service: HistoryService = Depends(get_service)
) -> dict:
    """
    Verifica saúde específica do módulo de histórico.
    
    Testa conectividade com banco, cache e performance de consultas.
    """
    try:
        start_time = time.time()
        
        # Teste básico de consulta
        from app.history.schemas import HistoryFilter, PaginationParams, SortParams
        
        test_result = await service.get_history(
            db=db,
            filters=HistoryFilter(),
            pagination=PaginationParams(page=1, limit=1),
            sorting=SortParams(),
            use_cache=False
        )
        
        query_time = (time.time() - start_time) * 1000
        
        # Teste de cache
        cache_available = await service.cache_service.ping()
        
        return {
            "status": "healthy",
            "components": {
                "database_query": "healthy",
                "cache": "healthy" if cache_available else "degraded",
                "pagination": "healthy"
            },
            "metrics": {
                "test_query_time_ms": round(query_time, 2),
                "cache_available": cache_available,
                "total_records_sample": test_result.pagination.total
            },
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }


# Endpoints auxiliares para cache management

@router.post(
    "/../cache/clear",
    summary="Limpar cache de histórico",
    description="Remove todos os caches relacionados ao histórico (admin)",
    dependencies=[Depends(rate_limit(requests_per_minute=5))]
)
async def clear_history_cache(
    background_tasks: BackgroundTasks,
    service: HistoryService = Depends(get_service)
) -> dict:
    """
    Limpa cache de histórico (operação administrativa).
    
    **Uso**: Para forçar recalculo de analytics ou resolver
    inconsistências de cache.
    """
    try:
        # Limpar todo o cache (implementação simplificada)
        success = await service.cache_service.clear_all()
        
        background_tasks.add_task(
            log_query_stats,
            endpoint="clear_cache",
            success=success,
            query_time=0
        )
        
        return {
            "success": success,
            "message": "Cache limpo com sucesso" if success else "Erro ao limpar cache",
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro ao limpar cache: {str(e)}",
            "timestamp": time.time()
        }