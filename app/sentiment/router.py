import time
from typing import Optional

from fastapi import (
    APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
)
from fastapi.responses import JSONResponse
from sqlalchemy import text  # ADDED: Import text for SQLAlchemy 2.0
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.core.cache import CacheService
from app.core.exceptions import (
    CacheError, DatabaseError, InvalidTextError, MLError, 
    ModelNotAvailableError, RateLimitError
)
from app.dependencies import get_cache_dependency, get_db_session
from app.sentiment.schemas import (
    AnalysisRequest, AnalysisResponse, BatchRequest, BatchResponse, 
    ErrorResponse, HealthResponse
)
from app.sentiment.service import SentimentService
from app.shared.rate_limiter import rate_limit


# Router com configuração base
router = APIRouter(
    prefix="/api/v1/sentiment",
    tags=["sentiment-analysis"],
    responses={
        429: {"model": ErrorResponse, "description": "Rate limit excedido"},
        500: {"model": ErrorResponse, "description": "Erro interno do servidor"},
        503: {"model": ErrorResponse, "description": "Serviço indisponível"}
    }
)


def get_sentiment_service(
    cache: CacheService = Depends(get_cache_dependency)
) -> SentimentService:
    """Dependency para obter serviço de sentimentos."""
    return SentimentService(cache_service=cache)


async def log_analysis_stats(
    endpoint: str,
    success: bool,
    processing_time: float,
    text_count: int = 1
) -> None:
    """Background task para logging de estatísticas."""
    import logging
    
    logger = logging.getLogger("sentiment_analytics")
    
    try:
        stats = {
            "endpoint": endpoint,
            "success": success,
            "processing_time_ms": processing_time,
            "text_count": text_count,
            "timestamp": time.time()
        }
        
        logger.info(f"Analytics: {stats}")
        
    except Exception as e:
        logger.error(f"Erro no logging de analytics: {e}")


async def handle_sentiment_error(error: Exception, request_id: str) -> HTTPException:
    """Converte erros de aplicação para HTTPException."""
    if isinstance(error, InvalidTextError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_TEXT",
                "message": str(error),
                "request_id": request_id
            }
        )
    
    elif isinstance(error, ModelNotAvailableError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "MODEL_UNAVAILABLE", 
                "message": "Modelo de análise temporariamente indisponível",
                "request_id": request_id
            }
        )
    
    elif isinstance(error, MLError):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "ML_ERROR",
                "message": "Erro no processamento de ML",
                "request_id": request_id
            }
        )
    
    elif isinstance(error, DatabaseError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "DATABASE_ERROR",
                "message": "Erro temporário na persistência",
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


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analisar sentimento de texto",
    description="Executa análise de sentimento em um texto individual",
    response_description="Resultado da análise com sentimento, confiança e idioma"
)
@rate_limit(requests_per_minute=100, requests_per_hour=1000)
async def analyze_sentiment(
    analysis_request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    db: Session = Depends(get_db_session),
    sentiment_service: SentimentService = Depends(get_sentiment_service),
    settings: Settings = Depends(get_settings)
) -> AnalysisResponse:
    """
    Analisa sentimento de um texto individual.
    
    - **text**: Texto para análise (1-2000 caracteres)
    
    Retorna sentimento (positive/negative/neutral), confiança e idioma detectado.
    """
    start_time = time.time()
    request_id = getattr(http_request.state, "request_id", "unknown")
    
    try:
        # Executar análise
        result = await sentiment_service.analyze_text(
            text=analysis_request.text,
            db=db,
            use_cache=True,
            save_to_db=True
        )
        
        # Converter para response schema
        response = AnalysisResponse(
            text=analysis_request.text if settings.debug else None,  # Texto apenas em debug
            sentiment=result["sentiment"],
            confidence=result["confidence"],
            language=result["language"],
            all_scores=[
                {"label": score["label"], "score": score["score"]}
                for score in result.get("all_scores", [])
            ],
            processing_time_ms=result.get("response_time_ms"),
            cached=result.get("cached", False)
        )
        
        # Background analytics
        processing_time = (time.time() - start_time) * 1000
        background_tasks.add_task(
            log_analysis_stats,
            endpoint="analyze",
            success=True,
            processing_time=processing_time
        )
        
        return response
        
    except Exception as error:
        # Background analytics para erro
        processing_time = (time.time() - start_time) * 1000
        background_tasks.add_task(
            log_analysis_stats,
            endpoint="analyze",
            success=False,
            processing_time=processing_time
        )
        
        raise await handle_sentiment_error(error, request_id)


@router.post(
    "/analyze-batch",
    response_model=BatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Analisar sentimentos em lote",
    description="Executa análise de sentimento em múltiplos textos",
    response_description="Lista de resultados de análise"
)
@rate_limit(requests_per_minute=20, requests_per_hour=200)  # Limite menor para batch
async def analyze_batch_sentiment(
    batch_request: BatchRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    db: Session = Depends(get_db_session),
    sentiment_service: SentimentService = Depends(get_sentiment_service),
    settings: Settings = Depends(get_settings)
) -> BatchResponse:
    """
    Analisa sentimento de múltiplos textos em lote.
    
    - **texts**: Lista de textos (máximo 50 itens)
    
    Retorna lista de análises individuais com otimização para processamento em lote.
    """
    start_time = time.time()
    request_id = getattr(http_request.state, "request_id", "unknown")
    
    try:
        # Executar análise em lote
        results = await sentiment_service.analyze_batch(
            texts=batch_request.texts,
            db=db,
            use_cache=True,
            save_to_db=True,
            max_batch_size=settings.ml.batch_size
        )
        
        # Converter para response schemas
        analysis_responses = []
        for i, result in enumerate(results):
            response = AnalysisResponse(
                text=batch_request.texts[i] if settings.debug else None,
                sentiment=result["sentiment"],
                confidence=result["confidence"],
                language=result["language"],
                all_scores=[
                    {"label": score["label"], "score": score["score"]}
                    for score in result.get("all_scores", [])
                ],
                cached=result.get("cached", False)
            )
            analysis_responses.append(response)
        
        processing_time = (time.time() - start_time) * 1000
        
        batch_response = BatchResponse(
            results=analysis_responses,
            total_processed=len(analysis_responses),
            processing_time_ms=processing_time
        )
        
        # Background analytics
        background_tasks.add_task(
            log_analysis_stats,
            endpoint="analyze-batch",
            success=True,
            processing_time=processing_time,
            text_count=len(batch_request.texts)
        )
        
        return batch_response
        
    except Exception as error:
        # Background analytics para erro
        processing_time = (time.time() - start_time) * 1000
        background_tasks.add_task(
            log_analysis_stats,
            endpoint="analyze-batch",
            success=False,
            processing_time=processing_time,
            text_count=len(batch_request.texts)

        )
        
        raise await handle_sentiment_error(error, request_id)


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Verificar saúde do serviço",
    description="Retorna status de saúde do serviço de análise de sentimentos",
    response_description="Status detalhado dos componentes"
)
async def health_check(
    db: Session = Depends(get_db_session),
    sentiment_service: SentimentService = Depends(get_sentiment_service)
) -> HealthResponse:
    """
    Verifica saúde do serviço de análise de sentimentos.
    
    Retorna status dos componentes: modelo ML, cache, banco de dados.
    """
    try:
        # Verificar modelo ML
        model_info = sentiment_service.analyzer.get_model_info()
        model_available = model_info.get("model_loaded", False)
        
        # Verificar cache
        cache_available = await sentiment_service.cache_service.ping()
        
        # Verificar banco (teste simples)
        try:
            db.execute(text("SELECT 1")).scalar()  # FIXED: Added text() wrapper
            db_available = True
        except Exception:
            db_available = False
        
        # Determinar status geral
        if model_available and db_available:
            overall_status = "healthy"
        elif model_available or db_available:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        # Obter estatísticas do cache
        cache_stats = await sentiment_service.cache_service.get_stats()
        
        return HealthResponse(
            status=overall_status,
            services={
                "ml_model": "healthy" if model_available else "unhealthy",
                "cache": "healthy" if cache_available else "degraded",
                "database": "healthy" if db_available else "unhealthy"
            },
            model_info=model_info,
            cache_stats=cache_stats
        )
        
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            services={
                "error": str(e)
            }
        )


@router.get(
    "/stats",
    summary="Estatísticas do serviço",
    description="Retorna estatísticas detalhadas do serviço",
    dependencies=[Depends(rate_limit(requests_per_minute=10))]
)
async def get_service_statistics(
    db: Session = Depends(get_db_session),
    sentiment_service: SentimentService = Depends(get_sentiment_service)
) -> dict:
    """
    Retorna estatísticas completas do serviço.
    
    Inclui métricas de performance, uso de cache e distribuição de sentimentos.
    """
    try:
        stats = await sentiment_service.get_statistics(db)
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "STATS_ERROR",
                "message": f"Erro ao obter estatísticas: {str(e)}"
            }
        )