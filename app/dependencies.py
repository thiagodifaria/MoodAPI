import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Generator

from fastapi import Depends, HTTPException, status
from sqlalchemy import text  # ADDED: Import text for SQLAlchemy 2.0
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.core.cache import CacheService, get_cache_service
from app.core.database import get_session_factory
from app.core.exceptions import DatabaseError, CacheError

logger = logging.getLogger(__name__)


def get_config() -> Settings:
    """Dependency para obter configurações da aplicação."""
    return get_settings()


def get_db_session(config: Settings = Depends(get_config)) -> Generator[Session, None, None]:
    """Dependency factory para sessões de banco de dados com error handling robusto."""
    session = None
    
    try:
        session_factory = get_session_factory()
        session = session_factory()
        
        logger.debug("Sessão de banco de dados criada")
        session.execute(text("SELECT 1")).scalar()  # FIXED: Added text() wrapper
        
        yield session
        
        session.commit()
        logger.debug("Transação commitada")
        
    except SQLAlchemyError as e:
        logger.error(f"Erro SQLAlchemy: {e}")
        
        if session:
            try:
                session.rollback()
                logger.debug("Rollback executado")
            except Exception:
                pass
        
        raise DatabaseError(
            message=f"Erro de banco de dados: {str(e)}",
            details={"original_error": str(e), "error_type": type(e).__name__}
        ) from e
        
    except Exception as e:
        logger.error(f"Erro inesperado na sessão: {e}")
        
        if session:
            try:
                session.rollback()
            except Exception:
                pass
        
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de banco de dados temporariamente indisponível"
        ) from e
        
    finally:
        if session:
            try:
                session.close()
                logger.debug("Sessão fechada")
            except Exception as cleanup_error:
                logger.error(f"Erro ao fechar sessão: {cleanup_error}")


async def get_cache_dependency(config: Settings = Depends(get_config)) -> CacheService:
    """Dependency para serviço de cache com fallback gracioso."""
    try:
        cache_service = await get_cache_service()
        is_connected = await cache_service.ping()
        
        if is_connected:
            logger.debug("Cache Redis conectado")
        else:
            logger.warning("Cache Redis indisponível - usando fallback")
            
        return cache_service
        
    except Exception as e:
        logger.error(f"Erro ao obter serviço de cache: {e}")
        
        if config.is_development:
            raise CacheError(
                message=f"Erro de cache em desenvolvimento: {str(e)}",
                details={"original_error": str(e)}
            ) from e
            
        logger.warning("Retornando serviço de cache com fallback")
        return await get_cache_service(force_fallback=True)


@asynccontextmanager
async def get_async_db_session(config: Settings = Depends(get_config)) -> AsyncGenerator[Session, None]:
    """Context manager assíncrono para sessões de banco com controle manual."""
    session = None
    
    try:
        session_factory = get_session_factory()
        session = session_factory()
        
        logger.debug("Sessão assíncrona criada")
        session.execute(text("SELECT 1")).scalar()  # FIXED: Added text() wrapper
        
        yield session
        
        session.commit()
        logger.debug("Transação assíncrona commitada")
        
    except SQLAlchemyError as e:
        logger.error(f"Erro SQLAlchemy assíncrono: {e}")
        
        if session:
            try:
                session.rollback()
            except Exception:
                pass
                
        raise DatabaseError(
            message=f"Erro de banco assíncrono: {str(e)}",
            details={"original_error": str(e)}
        ) from e
        
    except Exception as e:
        logger.error(f"Erro inesperado assíncrono: {e}")
        
        if session:
            try:
                session.rollback()
            except Exception:
                pass
        raise
        
    finally:
        if session:
            try:
                session.close()
                logger.debug("Sessão assíncrona fechada")
            except Exception as cleanup_error:
                logger.error(f"Erro ao fechar sessão assíncrona: {cleanup_error}")


def validate_database_connection() -> bool:
    """Dependency para validar conectividade com banco."""
    try:
        session_factory = get_session_factory()
        with session_factory() as session:
            session.execute(text("SELECT 1")).scalar()  # FIXED: Added text() wrapper
            logger.debug("Validação de banco bem-sucedida")
            return True
            
    except Exception as e:
        logger.error(f"Falha na validação de banco: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Banco de dados indisponível"
        ) from e


async def validate_cache_connection() -> bool:
    """Dependency para validar conectividade com cache Redis."""
    try:
        cache_service = await get_cache_service()
        is_connected = await cache_service.ping()
        
        if is_connected:
            logger.debug("Validação de cache bem-sucedida")
        else:
            logger.warning("Cache Redis não disponível")
            
        return is_connected
        
    except Exception as e:
        logger.error(f"Erro na validação de cache: {e}")
        return False


class DatabaseCacheDependency:
    """Dependency composta para banco e cache."""
    
    def __init__(
        self,
        db: Session = Depends(get_db_session),
        cache: CacheService = Depends(get_cache_dependency),
        config: Settings = Depends(get_config)
    ):
        self.db = db
        self.cache = cache
        self.config = config
        logger.debug("Dependency composta inicializada")

    async def health_check(self) -> dict:
        """Verifica saúde de ambos os serviços."""
        try:
            self.db.execute(text("SELECT 1")).scalar()  # FIXED: Added text() wrapper
            db_status = "healthy"
        except Exception:
            db_status = "unhealthy"
            
        try:
            cache_status = "healthy" if await self.cache.ping() else "degraded"
        except Exception:
            cache_status = "unhealthy"
            
        return {
            "database": db_status,
            "cache": cache_status,
            "overall": "healthy" if db_status == "healthy" else "degraded"
        }


def get_db_and_cache() -> DatabaseCacheDependency:
    """Factory para dependency composta."""
    return DatabaseCacheDependency()