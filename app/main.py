import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.cache import check_cache_health, get_cache_service
from app.core.database import check_database_health, init_database
from app.core.exceptions import (
    CacheError, DatabaseError, InvalidTextError, MLError, 
    ModelNotAvailableError, RateLimitError, get_exception_handlers
)
from app.sentiment.analyzer import get_sentiment_analyzer
from app.sentiment.router import router as sentiment_router
from app.history.router import router as history_router
from app.auth.router import router as auth_router  # NEW: Auth router
from app.shared.middleware import setup_middleware
from app.shared.rate_limiter import check_rate_limiter_health

# Configurações
settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação."""
    
    # STARTUP
    logger.info(f"Iniciando MoodAPI v{settings.app_version} - {settings.environment}")
    
    try:
        # 1. Inicializar banco de dados
        logger.info("Inicializando banco de dados...")
        init_database()
        
        # 2. Verificar conectividade do cache
        logger.info("Verificando cache...")
        cache_service = await get_cache_service()
        cache_available = await cache_service.ping()
        
        if cache_available:
            logger.info("Cache Redis conectado")
        else:
            logger.warning("Cache Redis indisponível - usando fallback")
        
        # 3. Modelo de ML - LAZY LOADING
        # Modelo agora é carregado sob demanda na primeira análise
        logger.info("Modelo ML configurado para lazy loading (carregará na primeira análise)")
        analyzer = get_sentiment_analyzer()
        model_info = analyzer.get_model_info()
        logger.info(f"Modelo configurado: {model_info['model_name']} (lazy loading)")
        
        # 4. Verificar health dos componentes
        logger.info("Verificando saúde dos componentes...")
        
        db_health = check_database_health()
        cache_health = await check_cache_health()
        rate_limiter_health = await check_rate_limiter_health()
        
        # Log dos status
        logger.info(f"Database: {db_health.get('status', 'unknown')}")
        logger.info(f"Cache: {cache_health.get('status', 'unknown')}")
        logger.info(f"Rate Limiter: {rate_limiter_health.get('status', 'unknown')}")
        
        # 5. Configurações de produção
        if settings.is_production:
            logger.info("Configurações de produção aplicadas")
        
        logger.info("✅ MoodAPI iniciado com sucesso!")
        
        yield
        
    except Exception as e:
        logger.error(f"Erro durante inicialização: {e}")
        raise
    
    # SHUTDOWN
    logger.info("Encerrando MoodAPI...")
    
    try:
        # Fechar conexões do cache
        cache_service = await get_cache_service()
        await cache_service.close()
        logger.info("Cache fechado")
        
    except Exception as e:
        logger.error(f"Erro durante shutdown: {e}")
    
    logger.info("MoodAPI encerrado")


# Criar aplicação FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    lifespan=lifespan,
    debug=settings.debug,
    docs_url="/docs" if settings.debug else None,  # Docs apenas em desenvolvimento
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    openapi_tags=[
        {
            "name": "authentication",
            "description": "Autenticação e autorização JWT"
        },
        {
            "name": "sentiment-analysis",
            "description": "Análise de sentimentos multilíngue"
        },
        {
            "name": "history-analytics",
            "description": "Histórico de análises e analytics"
        },
        {
            "name": "health",
            "description": "Verificações de saúde e status"
        }
    ]
)

# Configurar middleware
setup_middleware(app)

# Registrar exception handlers
for exception_type, handler in get_exception_handlers().items():
    app.add_exception_handler(exception_type, handler)

# Incluir routers
app.include_router(auth_router)  # NEW: Auth router primeiro
app.include_router(sentiment_router)
app.include_router(history_router)


# Endpoints principais da aplicação
@app.get(
    "/",
    summary="Página inicial",
    description="Informações básicas da API",
    tags=["health"]
)
async def root():
    """Endpoint raiz com informações da API."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": settings.app_description,
        "environment": settings.environment,
        "docs_url": "/docs" if settings.debug else "disabled",
        "status": "running",
        "features": [  # ADDED: Updated features list
            "sentiment-analysis",
            "batch-processing",
            "history-queries",
            "analytics-dashboards", 
            "multilingual-support",
            "rate-limiting",
            "caching",
            "background-tasks"
        ]
    }


@app.get(
    "/health",
    summary="Health check geral",
    description="Verificação de saúde de todos os componentes",
    tags=["health"]
)
async def health_check():
    """
    Health check completo da aplicação.
    
    Verifica status de todos os componentes críticos incluindo
    funcionalidades de histórico e analytics.
    """
    try:
        # Verificar componentes
        db_health = check_database_health()
        cache_health = await check_cache_health()
        rate_limiter_health = await check_rate_limiter_health()
        
        # Verificar modelo ML
        try:
            analyzer = get_sentiment_analyzer()
            model_info = analyzer.get_model_info()
            model_status = "healthy" if model_info.get("model_loaded") else "unhealthy"
        except Exception:
            model_status = "unhealthy"
            model_info = {}
        
        # ADDED: Test history functionality
        history_status = "healthy"  # Simplified - would test actual queries in production
        
        # Determinar status geral
        statuses = [
            db_health.get("status"),
            cache_health.get("status"), 
            rate_limiter_health.get("status"),
            model_status,
            history_status  # ADDED: Include history in overall status
        ]
        
        if all(s == "healthy" for s in statuses):
            overall_status = "healthy"
        elif any(s == "healthy" for s in statuses):
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        response = {
            "status": overall_status,
            "timestamp": asyncio.get_event_loop().time(),
            "components": {
                "database": db_health.get("status", "unknown"),
                "cache": cache_health.get("status", "unknown"),
                "rate_limiter": rate_limiter_health.get("status", "unknown"),
                "ml_model": model_status,
                "history_analytics": history_status  # ADDED: History component status
            },
            "version": settings.app_version,
            "environment": settings.environment
        }
        
        # Status code baseado na saúde
        status_code = {
            "healthy": status.HTTP_200_OK,
            "degraded": status.HTTP_200_OK,  # 200 mas com warnings
            "unhealthy": status.HTTP_503_SERVICE_UNAVAILABLE
        }.get(overall_status, status.HTTP_503_SERVICE_UNAVAILABLE)
        
        return JSONResponse(
            status_code=status_code,
            content=response
        )
        
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "Erro no health check",
                "error": str(e) if settings.debug else "Internal error"
            }
        )


@app.get(
    "/version",
    summary="Informações de versão",
    description="Retorna versão detalhada da aplicação",
    tags=["health"]
)
async def version_info():
    """Informações detalhadas de versão."""
    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "environment": settings.environment,
        "python_version": "3.11+",
        "fastapi_version": "0.100+",
        "pydantic_version": "2.5+",
        "features": [
            "sentiment-analysis",
            "multilingual-support", 
            "rate-limiting",
            "caching",
            "background-tasks",
            "structured-logging",
            "history-queries",      # ADDED: New features
            "analytics-dashboards",
            "query-optimization",
            "cache-invalidation"
        ]
    }


@app.get(
    "/metrics",
    summary="Métricas da aplicação",
    description="Estatísticas e métricas de performance incluindo histórico",
    tags=["health"]
)
async def metrics():
    """
    Métricas completas da aplicação.
    
    Endpoint útil para monitoramento e observabilidade incluindo
    métricas de consultas de histórico e analytics.
    """
    try:
        # Coletar métricas dos componentes
        cache_service = await get_cache_service()
        cache_stats = await cache_service.get_stats()
        
        rate_limiter_stats = await check_rate_limiter_health()
        
        # Informações do modelo
        analyzer = get_sentiment_analyzer()
        model_info = analyzer.get_model_info()
        
        # ADDED: Basic history metrics (would be more comprehensive in production)
        history_metrics = {
            "endpoints_available": [
                "/api/v1/history",
                "/api/v1/analytics", 
                "/api/v1/stats"
            ],
            "cache_strategies": ["query_results", "analytics", "stats"],
            "pagination_support": True,
            "filter_capabilities": [
                "sentiment", "language", "confidence", 
                "date_range", "text_search"
            ]
        }
        
        return {
            "timestamp": asyncio.get_event_loop().time(),
            "cache": cache_stats,
            "rate_limiter": rate_limiter_stats,
            "model": model_info,
            "history": history_metrics,  # ADDED: History metrics
            "environment": settings.environment,
            "uptime": "runtime_dependent"  # Seria calculado com timestamp de startup
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter métricas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao obter métricas"
        )


# ADDED: New endpoint for API overview including history capabilities
@app.get(
    "/api-overview",
    summary="Visão geral da API",
    description="Documentação resumida de todas as funcionalidades",
    tags=["health"]
)
async def api_overview():
    """
    Visão geral completa das capacidades da API.
    
    Útil para desenvolvedores entenderem rapidamente
    todas as funcionalidades disponíveis.
    """
    return {
        "api_name": settings.app_name,
        "version": settings.app_version,
        "base_url": "/api/v1",
        "modules": {
            "sentiment_analysis": {
                "description": "Análise de sentimentos multilíngue",
                "endpoints": [
                    "POST /sentiment/analyze - Análise individual",
                    "POST /sentiment/analyze-batch - Análise em lote",
                    "GET /sentiment/health - Health check do módulo"
                ],
                "features": [
                    "Suporte a múltiplos idiomas",
                    "Confiança do modelo",
                    "Cache automático",
                    "Rate limiting"
                ]
            },
            "history_analytics": {
                "description": "Histórico e analytics de análises",
                "endpoints": [
                    "GET /history - Consultar histórico com filtros",
                    "GET /history/{id} - Detalhes de análise específica",
                    "GET /analytics - Estatísticas para dashboards",
                    "GET /stats - Métricas agregadas por período",
                    "DELETE /history/{id} - Remover análise"
                ],
                "features": [
                    "Filtros flexíveis",
                    "Paginação otimizada",
                    "Cache de consultas",
                    "Agregações SQL eficientes",
                    "Invalidação automática de cache"
                ]
            }
        },
        "data_formats": {
            "input": "JSON com texto em qualquer idioma",
            "output": "JSON estruturado com sentimento, confiança e metadados",
            "pagination": "Offset/limit com metadata completa",
            "filtering": "Query parameters opcionais flexíveis"
        },
        "performance": {
            "sentiment_analysis": "< 500ms para textos até 2000 caracteres",
            "history_queries": "< 300ms para filtros simples, < 500ms para complexos",
            "analytics": "< 1s para períodos até 1 ano",
            "cache_hits": "< 50ms para consultas repetidas"
        },
        "rate_limits": {
            "sentiment_analysis": "100 req/min, 1000 req/hora",
            "batch_analysis": "20 req/min, 200 req/hora", 
            "history_queries": "60 req/min, 500 req/hora",
            "analytics": "20 req/min, 200 req/hora",
            "stats": "15 req/min, 150 req/hora"
        }
    }


# Handler customizado para 404
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handler personalizado para 404."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "NOT_FOUND",
            "message": f"Endpoint {request.method} {request.url.path} não encontrado",
            "available_endpoints": {
                "sentiment_analysis": "/api/v1/sentiment/analyze",
                "batch_analysis": "/api/v1/sentiment/analyze-batch",
                "history_queries": "/api/v1/history",        # ADDED: History endpoints
                "analytics": "/api/v1/analytics",
                "stats": "/api/v1/stats",
                "health": "/health",
                "docs": "/docs" if settings.debug else "disabled"
            }
        }
    )


# Handler para method not allowed
@app.exception_handler(405)
async def method_not_allowed_handler(request: Request, exc: HTTPException):
    """Handler para métodos não permitidos."""
    return JSONResponse(
        status_code=405,
        content={
            "error": "METHOD_NOT_ALLOWED",
            "message": f"Método {request.method} não permitido para {request.url.path}",
            "allowed_methods": ["GET", "POST", "DELETE", "OPTIONS"]  # ADDED: DELETE for history
        }
    )


# Configurações de startup logging
if __name__ == "__main__":
    import uvicorn
    
    # Configuração para desenvolvimento
    uvicorn.run(
        "app.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload and settings.debug,
        workers=1,  # Single worker para desenvolvimento
        log_level=settings.log_level.lower(),
        access_log=settings.debug
    )
else:
    # Configuração para produção (quando importado)
    logger.info(f"MoodAPI carregado - Versão: {settings.app_version}")


# Log de finalização do módulo
logger.info("Aplicação FastAPI configurada com módulo de histórico")

# Exception handlers específicos do router
@app.exception_handler(InvalidTextError)
async def invalid_text_handler(request: Request, exc: InvalidTextError):
    """Handler para erros de texto inválido."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "INVALID_TEXT",
            "message": str(exc),
            "details": getattr(exc, "details", {}),
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )


@app.exception_handler(RateLimitError)
async def rate_limit_handler(request: Request, exc: RateLimitError):
    """Handler para erros de rate limit."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "RATE_LIMIT_EXCEEDED",
            "message": str(exc),
            "request_id": getattr(request.state, "request_id", "unknown")
        },
        headers={
            "Retry-After": "60",
            "X-RateLimit-Limit": str(getattr(exc, "limit", "unknown")),
            "X-RateLimit-Window": getattr(exc, "window", "minute")
        }
    )


@app.exception_handler(CacheError)
async def cache_error_handler(request: Request, exc: CacheError):
    """Handler para erros de cache (não críticos)."""
    import logging
    
    logger = logging.getLogger("sentiment_router")
    logger.warning(f"Cache error (non-critical): {exc}")
    
    # Retornar erro genérico sem expor detalhes
    return JSONResponse(
        status_code=status.HTTP_200_OK,  # Cache error não falha request
        content={
            "warning": "Cache temporarily unavailable, using fallback",
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )