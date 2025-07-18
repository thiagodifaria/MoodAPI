import asyncio
import logging
import time
from functools import wraps
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, Request, status

from app.config import get_settings
from app.core.exceptions import RateLimitError

logger = logging.getLogger(__name__)
settings = get_settings()


class InMemoryRateLimiter:
    """Rate limiter thread-safe baseado em memória com sliding window."""
    
    def __init__(self):
        # Estrutura: {client_id: {endpoint: [(timestamp, count)]}}
        self._requests: Dict[str, Dict[str, List[Tuple[float, int]]]] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()
        
        logger.info("InMemoryRateLimiter inicializado")
    
    def _start_cleanup_task(self) -> None:
        """Inicia task de cleanup automático com verificação de event loop."""
        try:
            if not self._cleanup_task or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        except RuntimeError:
            # Sem event loop ativo (ex: durante testes) - inicializar depois
            logger.debug("Event loop não disponível - cleanup task será iniciada posteriormente")
            self._cleanup_task = None
    
    async def _ensure_cleanup_task(self) -> None:
        """Garante que cleanup task está rodando (lazy initialization)."""
        if self._cleanup_task is None:
            try:
                self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            except RuntimeError:
                # Ainda sem event loop - não fazer nada
                pass
    
    async def _cleanup_loop(self) -> None:
        """Loop de cleanup para remover registros antigos."""
        while True:
            try:
                await asyncio.sleep(300)  # Cleanup a cada 5 minutos
                await self._cleanup_old_entries()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro no cleanup do rate limiter: {e}")
    
    async def _cleanup_old_entries(self) -> None:
        """Remove entradas antigas do rate limiter."""
        current_time = time.time()
        cutoff_time = current_time - 3600  # Remove entradas > 1 hora
        
        async with self._lock:
            clients_to_remove = []
            
            for client_id, endpoints in self._requests.items():
                endpoints_to_remove = []
                
                for endpoint, timestamps in endpoints.items():
                    # Filtrar timestamps antigos
                    timestamps[:] = [
                        (ts, count) for ts, count in timestamps 
                        if ts > cutoff_time
                    ]
                    
                    if not timestamps:
                        endpoints_to_remove.append(endpoint)
                
                # Remover endpoints vazios
                for endpoint in endpoints_to_remove:
                    del endpoints[endpoint]
                
                # Marcar cliente para remoção se vazio
                if not endpoints:
                    clients_to_remove.append(client_id)
            
            # Remover clientes vazios
            for client_id in clients_to_remove:
                del self._requests[client_id]
            
            if clients_to_remove or any(endpoints_to_remove for endpoints_to_remove in []):
                logger.debug(f"Cleanup: removidos {len(clients_to_remove)} clientes")
    
    def _get_client_id(self, request: Request) -> str:
        """Extrai identificador único do client."""
        # Prioridade: IP real > IP do header > IP do cliente
        client_ip = (
            request.headers.get("X-Real-IP") or
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
            request.client.host if request.client else "unknown"
        )
        
        # Adicionar User-Agent para diferenciação adicional
        user_agent = request.headers.get("User-Agent", "")[:50]  # Limitar tamanho
        
        return f"{client_ip}:{hash(user_agent) % 10000}"
    
    def _get_endpoint_key(self, request: Request) -> str:
        """Gera chave única para o endpoint."""
        return f"{request.method}:{request.url.path}"
    
    async def is_allowed(
        self,
        request: Request,
        requests_per_minute: int = 100,
        requests_per_hour: int = 1000
    ) -> Tuple[bool, Dict[str, str]]:
        """
        Verifica se request está dentro dos limites.
        
        Returns:
            (allowed, headers) - Se permitido e headers informativos
        """
        # Garantir que cleanup task está rodando
        await self._ensure_cleanup_task()
        
        current_time = time.time()
        client_id = self._get_client_id(request)
        endpoint_key = self._get_endpoint_key(request)
        
        async with self._lock:
            # Inicializar estruturas se necessário
            if client_id not in self._requests:
                self._requests[client_id] = {}
            
            if endpoint_key not in self._requests[client_id]:
                self._requests[client_id][endpoint_key] = []
            
            timestamps = self._requests[client_id][endpoint_key]
            
            # Remover timestamps antigos (sliding window)
            minute_cutoff = current_time - 60
            hour_cutoff = current_time - 3600
            
            timestamps[:] = [
                (ts, count) for ts, count in timestamps 
                if ts > hour_cutoff
            ]
            
            # Contar requests no último minuto e hora
            minute_requests = sum(
                count for ts, count in timestamps 
                if ts > minute_cutoff
            )
            
            hour_requests = sum(count for ts, count in timestamps)
            
            # Verificar limites
            minute_exceeded = minute_requests >= requests_per_minute
            hour_exceeded = hour_requests >= requests_per_hour
            
            # Headers informativos
            headers = {
                "X-RateLimit-Limit-Minute": str(requests_per_minute),
                "X-RateLimit-Limit-Hour": str(requests_per_hour),
                "X-RateLimit-Remaining-Minute": str(max(0, requests_per_minute - minute_requests - 1)),
                "X-RateLimit-Remaining-Hour": str(max(0, requests_per_hour - hour_requests - 1)),
                "X-RateLimit-Reset-Minute": str(int(current_time + 60)),
                "X-RateLimit-Reset-Hour": str(int(current_time + 3600))
            }
            
            if minute_exceeded or hour_exceeded:
                # Determinar qual limite foi excedido
                if minute_exceeded:
                    headers["X-RateLimit-Exceeded"] = "minute"
                    headers["Retry-After"] = str(60)
                else:
                    headers["X-RateLimit-Exceeded"] = "hour"
                    headers["Retry-After"] = str(3600)
                
                return False, headers
            
            # Adicionar timestamp atual
            timestamps.append((current_time, 1))
            
            return True, headers
    
    async def get_stats(self) -> Dict[str, int]:
        """Retorna estatísticas do rate limiter."""
        async with self._lock:
            total_clients = len(self._requests)
            total_endpoints = sum(
                len(endpoints) for endpoints in self._requests.values()
            )
            total_requests = sum(
                sum(count for _, count in timestamps)
                for endpoints in self._requests.values()
                for timestamps in endpoints.values()
            )
            
            return {
                "total_clients": total_clients,
                "total_endpoints": total_endpoints,
                "total_requests_tracked": total_requests,
                "memory_entries": sum(
                    len(timestamps)
                    for endpoints in self._requests.values()
                    for timestamps in endpoints.values()
                )
            }
    
    async def clear_all(self) -> None:
        """Limpa todos os registros de rate limiting."""
        async with self._lock:
            self._requests.clear()
            logger.info("Rate limiter limpo")


# Instância global do rate limiter
_rate_limiter = InMemoryRateLimiter()


def rate_limit(
    requests_per_minute: int = None,
    requests_per_hour: int = None
):
    """
    Decorator para aplicar rate limiting a endpoints FastAPI.
    
    Args:
        requests_per_minute: Limite por minuto (padrão: config)
        requests_per_hour: Limite por hora (padrão: config)
    """
    # Usar valores padrão das configurações se não especificado
    rpm = requests_per_minute or settings.rate_limit.requests_per_minute
    rph = requests_per_hour or settings.rate_limit.requests_per_hour
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extrair request do endpoint FastAPI
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            # Buscar request nos kwargs
            if not request:
                request = kwargs.get('request') or kwargs.get('http_request')
            
            if not request:
                # Se não houver request, pular rate limiting
                logger.warning("Rate limiting pulado - Request não encontrado")
                return await func(*args, **kwargs)
            
            # Verificar se rate limiting está habilitado
            if not settings.rate_limit.enabled:
                return await func(*args, **kwargs)
            
            # Aplicar rate limiting
            allowed, headers = await _rate_limiter.is_allowed(
                request=request,
                requests_per_minute=rpm,
                requests_per_hour=rph
            )
            
            if not allowed:
                # Determinar qual limite foi excedido
                exceeded_type = headers.get("X-RateLimit-Exceeded", "minute")
                limit_value = rpm if exceeded_type == "minute" else rph
                
                logger.warning(
                    f"Rate limit excedido para {_rate_limiter._get_client_id(request)}: "
                    f"{limit_value} requests per {exceeded_type}"
                )
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "RATE_LIMIT_EXCEEDED",
                        "message": f"Limite de {limit_value} requests per {exceeded_type} excedido",
                        "retry_after": headers.get("Retry-After", "60")
                    },
                    headers=headers
                )
            
            # Executar função original
            response = await func(*args, **kwargs)
            
            # Adicionar headers informativos à response se possível
            if hasattr(response, 'headers'):
                for key, value in headers.items():
                    response.headers[key] = value
            
            return response
        
        return wrapper
    return decorator


async def get_rate_limiter_stats() -> Dict[str, int]:
    """Retorna estatísticas do rate limiter."""
    return await _rate_limiter.get_stats()


async def clear_rate_limiter() -> None:
    """Limpa todos os registros de rate limiting."""
    await _rate_limiter.clear_all()


# Dependency para FastAPI
async def rate_limit_dependency(
    request: Request,
    requests_per_minute: int = settings.rate_limit.requests_per_minute,
    requests_per_hour: int = settings.rate_limit.requests_per_hour
) -> None:
    """
    Dependency FastAPI para rate limiting.
    
    Use como: Depends(partial(rate_limit_dependency, requests_per_minute=50))
    """
    if not settings.rate_limit.enabled:
        return
    
    allowed, headers = await _rate_limiter.is_allowed(
        request=request,
        requests_per_minute=requests_per_minute,
        requests_per_hour=requests_per_hour
    )
    
    if not allowed:
        exceeded_type = headers.get("X-RateLimit-Exceeded", "minute")
        limit_value = requests_per_minute if exceeded_type == "minute" else requests_per_hour
        
        raise RateLimitError(
            limit=limit_value,
            window=exceeded_type,
            details={
                "client_id": _rate_limiter._get_client_id(request),
                "endpoint": _rate_limiter._get_endpoint_key(request),
                "headers": headers
            }
        )


# Função de health check do rate limiter
async def check_rate_limiter_health() -> Dict[str, any]:
    """Verifica saúde do rate limiter."""
    try:
        stats = await _rate_limiter.get_stats()
        
        return {
            "status": "healthy",
            "enabled": settings.rate_limit.enabled,
            "stats": stats,
            "config": {
                "default_requests_per_minute": settings.rate_limit.requests_per_minute,
                "default_requests_per_hour": settings.rate_limit.requests_per_hour,
                "burst_size": settings.rate_limit.burst_size
            }
        }
        
    except Exception as e:
        logger.error(f"Erro no health check do rate limiter: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


logger.info(f"Rate limiter carregado - Habilitado: {settings.rate_limit.enabled}")