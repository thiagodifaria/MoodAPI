import logging
import traceback
from typing import Any, Dict, Optional, Union

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class MoodAPIError(Exception):
    """Exceção base para todas as exceções do MoodAPI."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.error_code = error_code or self.__class__.__name__
        
        logger.error(
            f"Exceção {self.__class__.__name__}: {message}",
            extra={"details": self.details, "error_code": self.error_code}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
        }
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (Detalhes: {self.details})"
        return self.message


# Exceções de configuração
class ConfigurationError(MoodAPIError):
    """Erros de configuração da aplicação."""
    pass


# Exceções de banco de dados
class DatabaseError(MoodAPIError):
    """Exceção base para erros de banco de dados."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Erros de conexão com banco."""
    
    def __init__(self, message: str = "Falha na conexão com banco de dados", **kwargs):
        super().__init__(message, **kwargs)


class RecordNotFoundError(DatabaseError):
    """Registro não encontrado."""
    
    def __init__(self, resource: str = "Registro", record_id: Any = None, **kwargs):
        message = f"{resource} não encontrado"
        if record_id:
            message += f" (ID: {record_id})"
        
        details = kwargs.get("details", {})
        details.update({"resource": resource, "record_id": record_id})
        kwargs["details"] = details
        
        super().__init__(message, **kwargs)


class DuplicateRecordError(DatabaseError):
    """Tentativa de criar registro duplicado."""
    
    def __init__(self, resource: str = "Registro", field: str = None, **kwargs):
        message = f"{resource} já existe"
        if field:
            message += f" (Campo: {field})"
        
        details = kwargs.get("details", {})
        details.update({"resource": resource, "field": field})
        kwargs["details"] = details
        
        super().__init__(message, **kwargs)


# Exceções de cache
class CacheError(MoodAPIError):
    """Exceção base para erros de cache."""
    pass


class CacheConnectionError(CacheError):
    """Erros de conexão com Redis."""
    
    def __init__(self, message: str = "Falha na conexão com Redis", **kwargs):
        super().__init__(message, **kwargs)


# Exceções de Machine Learning
class MLError(MoodAPIError):
    """Exceção base para erros de ML."""
    pass


class ModelLoadError(MLError):
    """Erro ao carregar modelo de ML."""
    
    def __init__(self, model_name: str, message: str = "Erro ao carregar modelo", **kwargs):
        full_message = f"{message}: {model_name}"
        
        details = kwargs.get("details", {})
        details.update({"model_name": model_name})
        kwargs["details"] = details
        
        super().__init__(full_message, **kwargs)


class ModelInferenceError(MLError):
    """Erro durante inferência do modelo."""
    pass


class InvalidTextError(MLError):
    """Texto inválido para análise."""
    
    def __init__(self, reason: str, text_sample: str = None, **kwargs):
        message = f"Texto inválido: {reason}"
        
        details = kwargs.get("details", {})
        details.update({"reason": reason})
        if text_sample:
            details["text_sample"] = text_sample[:100] + "..." if len(text_sample) > 100 else text_sample
        kwargs["details"] = details
        
        super().__init__(message=message, **kwargs)


class ModelNotAvailableError(MLError):
    """Modelo não disponível."""
    
    def __init__(self, model_name: str = "modelo", **kwargs):
        message = f"Modelo não disponível: {model_name}"
        
        details = kwargs.get("details", {})
        details.update({"model_name": model_name})
        kwargs["details"] = details
        
        super().__init__(message, **kwargs)


# Exceções de API
class APIError(MoodAPIError):
    """Exceção base para erros de API."""
    pass


class ValidationError(APIError):
    """Erro de validação de dados."""
    
    def __init__(self, field: str, value: Any = None, message: str = "Erro de validação", **kwargs):
        full_message = f"{message} no campo '{field}'"
        if value is not None:
            full_message += f" (Valor: {value})"
        
        details = kwargs.get("details", {})
        details.update({"field": field, "value": value})
        kwargs["details"] = details
        
        super().__init__(full_message, **kwargs)


class RateLimitError(APIError):
    """Limite de taxa excedido."""
    
    def __init__(self, limit: int, window: str = "minuto", **kwargs):
        message = f"Limite de taxa excedido: {limit} requests por {window}"
        
        details = kwargs.get("details", {})
        details.update({"limit": limit, "window": window})
        kwargs["details"] = details
        
        super().__init__(message, **kwargs)


class AuthenticationError(APIError):
    """Erro de autenticação."""
    
    def __init__(self, message: str = "Falha na autenticação", **kwargs):
        super().__init__(message, **kwargs)


class AuthorizationError(APIError):
    """Erro de autorização."""
    
    def __init__(self, resource: str = "recurso", action: str = "acessar", **kwargs):
        message = f"Sem permissão para {action} {resource}"
        
        details = kwargs.get("details", {})
        details.update({"resource": resource, "action": action})
        kwargs["details"] = details
        
        super().__init__(message, **kwargs)


# HTTPError wrapper
class HTTPError(HTTPException):
    """HTTPException com estrutura padronizada."""
    
    def __init__(
        self,
        status_code: int,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        self.error_code = error_code or "HTTP_ERROR"
        self.message = message
        self.details = details or {}
        
        detail = {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }
        
        super().__init__(status_code=status_code, detail=detail)
        
        logger.warning(
            f"HTTP Error {status_code}: {message}",
            extra={"status_code": status_code, "details": self.details}
        )


def create_http_error_from_app_error(app_error: MoodAPIError) -> HTTPError:
    """Converte exceção da aplicação para HTTPError."""
    error_mapping = {
        # Configuração
        ConfigurationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        
        # Banco de dados
        DatabaseConnectionError: status.HTTP_503_SERVICE_UNAVAILABLE,
        DatabaseError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        RecordNotFoundError: status.HTTP_404_NOT_FOUND,
        DuplicateRecordError: status.HTTP_409_CONFLICT,
        
        # Cache (não crítico)
        CacheError: status.HTTP_200_OK,
        CacheConnectionError: status.HTTP_200_OK,
        
        # Machine Learning
        ModelLoadError: status.HTTP_503_SERVICE_UNAVAILABLE,
        ModelInferenceError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        InvalidTextError: status.HTTP_400_BAD_REQUEST,
        ModelNotAvailableError: status.HTTP_503_SERVICE_UNAVAILABLE,
        
        # API
        ValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
        RateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        AuthorizationError: status.HTTP_403_FORBIDDEN,
    }
    
    status_code = error_mapping.get(type(app_error), status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return HTTPError(
        status_code=status_code,
        message=app_error.message,
        details=app_error.details,
        error_code=app_error.error_code
    )


# Exception handlers para FastAPI
async def mood_api_error_handler(request: Request, exc: MoodAPIError) -> JSONResponse:
    """Handler para exceções específicas do MoodAPI."""
    http_error = create_http_error_from_app_error(exc)
    
    logger.error(
        f"Exceção da aplicação: {exc.__class__.__name__}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error": exc.to_dict(),
            "traceback": traceback.format_exc()
        }
    )
    
    return JSONResponse(
        status_code=http_error.status_code,
        content=http_error.detail
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler para exceções não tratadas."""
    logger.error(
        f"Exceção não tratada: {exc.__class__.__name__}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error": str(exc),
            "traceback": traceback.format_exc()
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "Erro interno do servidor",
            "details": {
                "request_id": getattr(request.state, "request_id", "unknown"),
            }
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handler personalizado para HTTPException."""
    logger.warning(
        f"HTTP Exception {exc.status_code}: {exc.detail}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code
        }
    )
    
    # Se já está no formato correto, usar diretamente
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    
    # Padronizar formato
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP_{exc.status_code}",
            "message": str(exc.detail),
            "details": {}
        }
    )


def get_exception_handlers() -> Dict[Union[int, type], callable]:
    """Retorna handlers de exceção para FastAPI."""
    return {
        MoodAPIError: mood_api_error_handler,
        HTTPException: http_exception_handler,
        Exception: general_exception_handler,
    }


def raise_for_text_validation(text: str, min_length: int = 1, max_length: int = 2000) -> None:
    """Valida texto e levanta exceção se inválido."""
    if not text or not text.strip():
        raise InvalidTextError(
            reason="Texto vazio ou apenas espaços",
            text_sample=text,
            details={"text_length": len(text)}
        )
    
    text_length = len(text.strip())
    
    if text_length < min_length:
        raise InvalidTextError(
            reason=f"Texto muito curto (mínimo: {min_length} caracteres)",
            text_sample=text,
            details={"text_length": text_length, "min_length": min_length}
        )
    
    if text_length > max_length:
        raise InvalidTextError(
            reason=f"Texto muito longo (máximo: {max_length} caracteres)",
            text_sample=text[:100] + "..." if len(text) > 100 else text,
            details={"text_length": text_length, "max_length": max_length}
        )


logger.info("Módulo de exceções carregado")