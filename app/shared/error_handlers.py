"""
Handlers de erro unificados para toda a aplicação.

Consolida lógica duplicada de tratamento de erros dos routers.
"""
import logging
from typing import Dict, Tuple, Type

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    CacheError,
    DatabaseError,
    InvalidTextError,
    MLError,
    ModelNotAvailableError,
    RateLimitError,
    RecordNotFoundError,
)

logger = logging.getLogger(__name__)


# Mapeamento de exceções para status codes e códigos de erro
ERROR_MAPPING: Dict[Type[Exception], Tuple[int, str, str]] = {
    # (status_code, error_code, default_message)
    InvalidTextError: (
        status.HTTP_400_BAD_REQUEST,
        "INVALID_TEXT",
        "Texto inválido para análise"
    ),
    RecordNotFoundError: (
        status.HTTP_404_NOT_FOUND,
        "RECORD_NOT_FOUND",
        "Registro não encontrado"
    ),
    ModelNotAvailableError: (
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "MODEL_UNAVAILABLE",
        "Modelo de análise temporariamente indisponível"
    ),
    MLError: (
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "ML_ERROR",
        "Erro no processamento de ML"
    ),
    DatabaseError: (
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "DATABASE_ERROR",
        "Erro temporário no banco de dados"
    ),
    RateLimitError: (
        status.HTTP_429_TOO_MANY_REQUESTS,
        "RATE_LIMIT_EXCEEDED",
        "Limite de requisições excedido"
    ),
    CacheError: (
        status.HTTP_200_OK,  # Cache error não é crítico
        "CACHE_WARNING",
        "Cache temporariamente indisponível"
    ),
}


async def handle_api_error(error: Exception, request_id: str = "unknown") -> HTTPException:
    """
    Handler unificado para erros de API.
    
    Converte exceções da aplicação para HTTPException com formato padronizado.
    
    Args:
        error: Exceção original
        request_id: ID da requisição para rastreamento
        
    Returns:
        HTTPException com detalhes formatados
    """
    # Buscar mapeamento específico
    error_type = type(error)
    mapping = ERROR_MAPPING.get(error_type)
    
    if mapping:
        status_code, error_code, default_message = mapping
        message = str(error) if str(error) else default_message
    else:
        # Erro genérico não mapeado
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_code = "INTERNAL_ERROR"
        message = "Erro interno do servidor"
        
        # Log para erros não esperados
        logger.error(f"Erro não mapeado: {error_type.__name__}: {error}")
    
    return HTTPException(
        status_code=status_code,
        detail={
            "error": error_code,
            "message": message,
            "request_id": request_id
        }
    )


def create_error_response(
    error: Exception,
    request_id: str = "unknown",
    include_debug: bool = False
) -> JSONResponse:
    """
    Cria JSONResponse para erros.
    
    Args:
        error: Exceção original
        request_id: ID da requisição
        include_debug: Se deve incluir informações de debug
        
    Returns:
        JSONResponse formatado
    """
    error_type = type(error)
    mapping = ERROR_MAPPING.get(error_type)
    
    if mapping:
        status_code, error_code, default_message = mapping
        message = str(error) if str(error) else default_message
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_code = "INTERNAL_ERROR"
        message = "Erro interno do servidor"
    
    content = {
        "error": error_code,
        "message": message,
        "request_id": request_id
    }
    
    if include_debug:
        content["debug"] = {
            "error_type": error_type.__name__,
            "error_details": str(error)
        }
    
    return JSONResponse(
        status_code=status_code,
        content=content
    )


def get_error_headers(error: Exception) -> Dict[str, str]:
    """
    Retorna headers adicionais para tipos específicos de erro.
    
    Args:
        error: Exceção original
        
    Returns:
        Dict de headers
    """
    headers = {}
    
    if isinstance(error, RateLimitError):
        headers["Retry-After"] = "60"
        headers["X-RateLimit-Exceeded"] = "true"
    
    return headers


logger.info("Módulo de error handlers unificados carregado")
