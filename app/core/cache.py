import asyncio
import hashlib
import json
import logging
from functools import lru_cache
from typing import Any, Dict, Optional, Union

import redis.asyncio as redis
from redis.asyncio import ConnectionPool
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError, RedisError, TimeoutError, BusyLoadingError
from redis.retry import Retry

from app.config import get_settings
from app.core.exceptions import CacheError

logger = logging.getLogger(__name__)
settings = get_settings()


class CacheMetrics:
    """Métricas básicas de cache em memória."""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.errors = 0
        self.fallback_operations = 0
    
    def hit(self) -> None:
        self.hits += 1
    
    def miss(self) -> None:
        self.misses += 1
    
    def set_operation(self) -> None:
        self.sets += 1
    
    def delete_operation(self) -> None:
        self.deletes += 1
    
    def error(self) -> None:
        self.errors += 1
    
    def fallback(self) -> None:
        self.fallback_operations += 1
    
    @property
    def hit_rate(self) -> float:
        total_reads = self.hits + self.misses
        return self.hits / total_reads if total_reads > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Union[int, float]]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "errors": self.errors,
            "fallback_operations": self.fallback_operations,
            "hit_rate": self.hit_rate,
        }


class CacheService:
    """Serviço de cache com Redis e fallback gracioso."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None, fallback_mode: bool = False):
        self.redis_client = redis_client
        self.fallback_mode = fallback_mode
        self.metrics = CacheMetrics()
        self._fallback_store: Dict[str, Any] = {}
        logger.info(f"CacheService inicializado - Fallback: {fallback_mode}")
    
    def _generate_cache_key(self, key: str) -> str:
        """Gera chave com hash MD5 e prefixo."""
        key_hash = hashlib.md5(key.encode('utf-8')).hexdigest()
        return settings.get_cache_key(f"hash:{key_hash}")
    
    def _serialize_value(self, value: Any) -> str:
        """Serializa valor para JSON."""
        try:
            return json.dumps(value, ensure_ascii=False, separators=(',', ':'))
        except (TypeError, ValueError) as e:
            logger.error(f"Erro ao serializar: {e}")
            raise CacheError(
                message=f"Falha na serialização: {str(e)}",
                details={"value_type": type(value).__name__}
            ) from e
    
    def _deserialize_value(self, value: str) -> Any:
        """Deserializa valor do JSON."""
        try:
            return json.loads(value)
        except (TypeError, ValueError, json.JSONDecodeError) as e:
            logger.error(f"Erro ao deserializar: {e}")
            raise CacheError(
                message=f"Falha na deserialização: {str(e)}",
                details={"value": value[:100]}
            ) from e
    
    async def ping(self) -> bool:
        """Testa conectividade com Redis."""
        if self.fallback_mode or not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.ping()
            logger.debug("Ping Redis bem-sucedido")
            return result
        except Exception as e:
            logger.warning(f"Ping Redis falhou: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Obtém valor do cache."""
        cache_key = self._generate_cache_key(key)
        
        # Modo fallback
        if self.fallback_mode or not self.redis_client:
            self.metrics.fallback()
            
            if cache_key in self._fallback_store:
                self.metrics.hit()
                logger.debug(f"Cache hit (fallback): {key}")
                return self._fallback_store[cache_key]
            else:
                self.metrics.miss()
                logger.debug(f"Cache miss (fallback): {key}")
                return None
        
        # Modo Redis
        try:
            cached_value = await self.redis_client.get(cache_key)
            
            if cached_value is not None:
                self.metrics.hit()
                logger.debug(f"Cache hit (Redis): {key}")
                return self._deserialize_value(cached_value)
            else:
                self.metrics.miss()
                logger.debug(f"Cache miss (Redis): {key}")
                return None
                
        except Exception as e:
            self.metrics.error()
            logger.error(f"Erro ao buscar no cache: {e}")
            
            # Tentar fallback
            if cache_key in self._fallback_store:
                self.metrics.fallback()
                logger.warning(f"Usando fallback devido a erro Redis: {key}")
                return self._fallback_store[cache_key]
            
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Define valor no cache."""
        cache_key = self._generate_cache_key(key)
        serialized_value = self._serialize_value(value)
        
        if ttl is None:
            ttl = settings.cache.default_ttl
        
        # Modo fallback
        if self.fallback_mode or not self.redis_client:
            self.metrics.fallback()
            self.metrics.set_operation()
            
            self._fallback_store[cache_key] = value
            logger.debug(f"Cache set (fallback): {key}")
            
            # Limitar tamanho do cache em memória
            if len(self._fallback_store) > 1000:
                keys_to_remove = list(self._fallback_store.keys())[:100]
                for old_key in keys_to_remove:
                    del self._fallback_store[old_key]
                logger.warning("Cache fallback limitado a 1000 itens")
            
            return True
        
        # Modo Redis
        try:
            result = await self.redis_client.setex(cache_key, ttl, serialized_value)
            
            if result:
                self.metrics.set_operation()
                logger.debug(f"Cache set (Redis): {key} (TTL: {ttl}s)")
                
                # Salvar no fallback também
                self._fallback_store[cache_key] = value
                return True
            else:
                self.metrics.error()
                logger.error(f"Falha ao definir valor no Redis: {key}")
                return False
                
        except Exception as e:
            self.metrics.error()
            logger.error(f"Erro ao definir no cache: {e}")
            
            # Fallback
            self.metrics.fallback()
            self._fallback_store[cache_key] = value
            logger.warning(f"Usando fallback devido a erro Redis: {key}")
            return True
    
    async def delete(self, key: str) -> bool:
        """Remove valor do cache."""
        cache_key = self._generate_cache_key(key)
        
        # Sempre remover do fallback
        fallback_deleted = cache_key in self._fallback_store
        if fallback_deleted:
            del self._fallback_store[cache_key]
        
        if self.fallback_mode or not self.redis_client:
            self.metrics.fallback()
            self.metrics.delete_operation()
            logger.debug(f"Cache delete (fallback): {key}")
            return fallback_deleted
        
        try:
            result = await self.redis_client.delete(cache_key)
            self.metrics.delete_operation()
            logger.debug(f"Cache delete (Redis): {key}")
            return result > 0 or fallback_deleted
            
        except Exception as e:
            self.metrics.error()
            logger.error(f"Erro ao deletar do cache: {e}")
            return fallback_deleted
    
    async def clear_all(self) -> bool:
        """Limpa todo o cache da aplicação."""
        self._fallback_store.clear()
        
        if self.fallback_mode or not self.redis_client:
            logger.info("Cache fallback limpo")
            return True
        
        try:
            pattern = f"{settings.cache.key_prefix}*"
            cursor = 0
            deleted_count = 0
            
            while True:
                cursor, keys = await self.redis_client.scan(cursor=cursor, match=pattern, count=100)
                
                if keys:
                    deleted_count += await self.redis_client.delete(*keys)
                
                if cursor == 0:
                    break
            
            logger.info(f"Cache Redis limpo: {deleted_count} chaves removidas")
            return True
            
        except Exception as e:
            self.metrics.error()
            logger.error(f"Erro ao limpar cache: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do cache."""
        stats = {
            "metrics": self.metrics.to_dict(),
            "fallback_mode": self.fallback_mode,
            "fallback_store_size": len(self._fallback_store),
            "redis_available": await self.ping(),
        }
        
        # Info do Redis se disponível
        if not self.fallback_mode and self.redis_client:
            try:
                redis_info = await self.redis_client.info("memory")
                stats["redis_memory"] = {
                    "used_memory": redis_info.get("used_memory", 0),
                    "used_memory_human": redis_info.get("used_memory_human", "0B"),
                }
            except Exception:
                pass
        
        return stats
    
    async def close(self) -> None:
        """Fecha conexão com Redis."""
        if self.redis_client and not self.fallback_mode:
            try:
                await self.redis_client.close()
                logger.info("Conexão Redis fechada")
            except Exception as e:
                logger.error(f"Erro ao fechar Redis: {e}")


def create_redis_client() -> redis.Redis:
    """Cria cliente Redis com retry robustas."""
    try:
        retry_policy = Retry(
            ExponentialBackoff(cap=10, base=1),
            retries=5
        )
        
        connection_pool = ConnectionPool.from_url(
            settings.get_cache_url(),
            max_connections=settings.cache.max_connections,
            socket_timeout=settings.cache.socket_timeout,
            socket_connect_timeout=settings.cache.socket_connect_timeout,
            retry_on_timeout=settings.cache.retry_on_timeout,
            health_check_interval=settings.cache.health_check_interval,
            retry=retry_policy,
            retry_on_error=[ConnectionError, TimeoutError, BusyLoadingError]
        )
        
        redis_client = redis.Redis(
            connection_pool=connection_pool,
            decode_responses=True,
        )
        
        logger.info("Cliente Redis criado")
        return redis_client
        
    except Exception as e:
        logger.error(f"Erro ao criar cliente Redis: {e}")
        raise CacheError(
            message=f"Falha ao criar cliente Redis: {str(e)}",
            details={"redis_url": settings.get_cache_url()}
        ) from e


# FIXED: Singleton assíncrono thread-safe sem @lru_cache()
_cache_service_instance: Optional[CacheService] = None
_cache_service_lock = asyncio.Lock()


async def get_cache_service(force_fallback: bool = False) -> CacheService:
    """Factory singleton assíncrono para serviço de cache com fallback automático."""
    global _cache_service_instance
    
    # Se já existe uma instância e não está forçando fallback, retornar
    if _cache_service_instance is not None and not force_fallback:
        return _cache_service_instance
    
    # Use lock para thread safety
    async with _cache_service_lock:
        # Double-check locking pattern
        if _cache_service_instance is not None and not force_fallback:
            return _cache_service_instance
        
        if force_fallback:
            logger.warning("Modo fallback forçado")
            return CacheService(fallback_mode=True)
        
        try:
            redis_client = create_redis_client()
            
            try:
                await asyncio.wait_for(redis_client.ping(), timeout=5.0)
                logger.info("Cache Redis conectado")
                _cache_service_instance = CacheService(redis_client=redis_client)
                return _cache_service_instance
                
            except asyncio.TimeoutError:
                logger.warning("Timeout Redis - usando fallback")
                await redis_client.close()
                
            except Exception as e:
                logger.warning(f"Redis indisponível ({e}) - usando fallback")
                await redis_client.close()
        
        except Exception as e:
            logger.warning(f"Erro ao configurar Redis ({e}) - usando fallback")
        
        logger.info("Cache em modo fallback")
        _cache_service_instance = CacheService(fallback_mode=True)
        return _cache_service_instance


async def reset_cache_service() -> None:
    """Reseta o singleton do cache service (útil para testes)."""
    global _cache_service_instance
    
    async with _cache_service_lock:
        if _cache_service_instance:
            await _cache_service_instance.close()
        _cache_service_instance = None
        logger.info("Cache service resetado")


async def check_cache_health() -> Dict[str, Any]:
    """Health check completo do cache."""
    try:
        cache_service = await get_cache_service()
        redis_available = await cache_service.ping()
        
        # Teste de operações
        test_key = "health_check_test"
        test_value = {"status": "ok"}
        
        set_success = await cache_service.set(test_key, test_value, ttl=60)
        get_result = await cache_service.get(test_key)
        delete_success = await cache_service.delete(test_key)
        
        operations_ok = set_success and get_result == test_value and delete_success
        stats = await cache_service.get_stats()
        
        return {
            "status": "healthy" if redis_available else "degraded",
            "redis_available": redis_available,
            "operations_test": operations_ok,
            "fallback_mode": cache_service.fallback_mode,
            "stats": stats,
        }
        
    except Exception as e:
        logger.error(f"Erro no health check do cache: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "error_type": type(e).__name__,
        }


logger.info("Módulo de cache carregado")
logger.info(f"URL do Redis: {settings.get_cache_url()}")