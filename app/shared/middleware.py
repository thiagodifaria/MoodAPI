import gzip
import json
import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware para adicionar timing headers e métricas de performance."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Ignorar rotas de health check para reduzir noise
        if request.url.path in ["/health", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        start_time = time.perf_counter()
        
        # Executar request
        response = await call_next(request)
        
        # Calcular tempo de processamento
        process_time = time.perf_counter() - start_time
        process_time_ms = round(process_time * 1000, 2)
        
        # Adicionar headers de timing
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Process-Time-MS"] = str(process_time_ms)
        
        # Log de performance para requests lentos
        if process_time > 1.0:  # > 1 segundo
            logger.warning(
                f"Slow request detected",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "process_time": process_time_ms,
                    "status_code": response.status_code
                }
            )
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging estruturado de requests."""
    
    def __init__(self, app, log_requests: bool = True, log_responses: bool = False):
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Gerar ID único para o request
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        # Preparar dados do request
        request_data = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": {
                key: value for key, value in request.headers.items()
                if key.lower() not in ["authorization", "cookie", "x-api-key"]  # Filtrar headers sensíveis
            },
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("User-Agent", ""),
            "timestamp": time.time()
        }
        
        # Log do request
        if self.log_requests:
            logger.info(
                f"Request started: {request.method} {request.url.path}",
                extra=request_data
            )
        
        start_time = time.perf_counter()
        
        try:
            # Executar request
            response = await call_next(request)
            
            # Adicionar request ID ao response
            response.headers["X-Request-ID"] = request_id
            
            # Preparar dados do response
            process_time = time.perf_counter() - start_time
            
            response_data = {
                **request_data,
                "status_code": response.status_code,
                "process_time": round(process_time * 1000, 2),
                "response_size": response.headers.get("content-length", "unknown")
            }
            
            # Log do response
            log_level = logging.WARNING if response.status_code >= 400 else logging.INFO
            logger.log(
                log_level,
                f"Request completed: {response.status_code} {request.method} {request.url.path}",
                extra=response_data
            )
            
            return response
            
        except Exception as e:
            # Log de erro
            process_time = time.perf_counter() - start_time
            
            error_data = {
                **request_data,
                "error": str(e),
                "error_type": type(e).__name__,
                "process_time": round(process_time * 1000, 2)
            }
            
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra=error_data,
                exc_info=True
            )
            
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Extrai IP real do cliente considerando proxies."""
        # Prioridade: X-Real-IP > X-Forwarded-For > client.host
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        return request.client.host if request.client else "unknown"


class HealthCheckBypassMiddleware(BaseHTTPMiddleware):
    """Middleware para bypass de health checks e rotas internas."""
    
    BYPASS_PATHS = {
        "/health",
        "/api/v1/sentiment/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico"
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Bypass para health checks - sem processamento adicional
        if request.url.path in self.BYPASS_PATHS:
            return await call_next(request)
        
        # Para outras rotas, continuar normalmente
        return await call_next(request)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware para tratamento global de erros."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
            
        except Exception as e:
            # Log do erro
            logger.error(
                f"Unhandled exception in {request.method} {request.url.path}",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "request_id": getattr(request.state, "request_id", "unknown"),
                    "path": request.url.path,
                    "method": request.method
                },
                exc_info=True
            )
            
            # Resposta padronizada para erros não tratados
            error_response = {
                "error": "INTERNAL_SERVER_ERROR",
                "message": "Erro interno do servidor",
                "request_id": getattr(request.state, "request_id", "unknown")
            }
            
            if settings.debug:
                error_response["debug_info"] = {
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            
            return JSONResponse(
                status_code=500,
                content=error_response,
                headers={"X-Request-ID": getattr(request.state, "request_id", "unknown")}
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware para adicionar headers de segurança."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Headers de segurança básicos
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'",
        }
        
        # Adicionar apenas se não existirem
        for header, value in security_headers.items():
            if header not in response.headers:
                response.headers[header] = value
        
        return response


def get_cors_middleware(app):
    """Configura CORS middleware baseado nas configurações."""
    return CORSMiddleware(
        app=app,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
        expose_headers=[
            "X-Process-Time",
            "X-Process-Time-MS", 
            "X-Request-ID",
            "X-RateLimit-Limit-Minute",
            "X-RateLimit-Remaining-Minute",
            "X-RateLimit-Reset-Minute"
        ]
    )


def setup_middleware(app):
    """
    Configura todos os middlewares na ordem correta.
    
    Ordem (externo para interno):
    1. CORS (mais externo)
    2. Security Headers
    3. Error Handling
    4. Health Check Bypass
    5. Request Logging
    6. Timing
    7. Compression (mais interno)
    """

    # 1. Timing
    app.add_middleware(TimingMiddleware)
    
    # 1.5. Compression (comprime responses > 500 bytes)
    from starlette.middleware.gzip import GZipMiddleware
    app.add_middleware(GZipMiddleware, minimum_size=500)
    
    # 2. Request Logging
    app.add_middleware(
        RequestLoggingMiddleware,
        log_requests=settings.debug,
        log_responses=settings.debug
    )
    
    # 3. Health Check Bypass
    app.add_middleware(HealthCheckBypassMiddleware)
    
    # 4. Error Handling
    app.add_middleware(ErrorHandlingMiddleware)
    
    # 5. Security Headers
    if settings.is_production:
        app.add_middleware(SecurityHeadersMiddleware)
    
    # 6. CORS (mais externo - aplicado primeiro)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.effective_cors_origins,  # Usa origins baseado no ambiente
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
        expose_headers=[
            "X-Process-Time",
            "X-Process-Time-MS",
            "X-Request-ID",
            "X-RateLimit-Limit-Minute",
            "X-RateLimit-Remaining-Minute",
            "X-RateLimit-Reset-Minute",
            "X-RateLimit-Limit-Hour",
            "X-RateLimit-Remaining-Hour",
            "Content-Encoding"  # Para compressão gzip
        ]
    )
    
    logger.info(f"Middleware configurado - Ambiente: {settings.environment}")


def get_middleware_stats() -> dict:
    """Retorna estatísticas dos middlewares."""
    return {
        "cors_enabled": True,
        "cors_origins": settings.cors_origins,
        "security_headers_enabled": settings.is_production,
        "compression_enabled": not settings.debug,
        "request_logging_enabled": settings.debug,
        "environment": settings.environment
    }


# Log de inicialização
logger.info("Módulo de middleware carregado")