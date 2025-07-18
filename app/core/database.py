import logging
from contextlib import contextmanager
from functools import lru_cache
from typing import Any, Dict, Generator

from sqlalchemy import Engine, MetaData, create_engine, event, text
from sqlalchemy.exc import DatabaseError, DisconnectionError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.core.exceptions import DatabaseError as AppDatabaseError

logger = logging.getLogger(__name__)
settings = get_settings()


class Base(DeclarativeBase):
    """Base declarativa para modelos SQLAlchemy 2.0 com suporte a typing."""
    
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s"
        }
    )

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        primary_key = getattr(self, 'id', 'unknown')
        return f"<{class_name}(id={primary_key})>"


def create_database_engine() -> Engine:
    """Cria e configura engine do banco com otimizações."""
    try:
        database_url = settings.get_database_url()
        
        engine_kwargs: Dict[str, Any] = {
            "echo": settings.database.echo,
            "future": True,
        }
        
        if database_url.startswith("sqlite"):
            logger.info("Configurando engine SQLite")
            engine_kwargs.update({
                "poolclass": StaticPool,
                "connect_args": {
                    "check_same_thread": False,
                    "timeout": 20,
                    "isolation_level": None,
                },
                "pool_pre_ping": True,
            })
            
        else:
            logger.info("Configurando engine PostgreSQL")
            engine_kwargs.update({
                "pool_size": settings.database.pool_size,
                "max_overflow": settings.database.max_overflow,
                "pool_timeout": settings.database.pool_timeout,
                "pool_recycle": settings.database.pool_recycle,
                "pool_pre_ping": True,
            })
        
        engine = create_engine(database_url, **engine_kwargs)
        
        # Setup básico de event listeners
        if database_url.startswith("sqlite"):
            @event.listens_for(engine, "connect")
            def receive_connect(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA synchronous=NORMAL") 
                cursor.execute("PRAGMA cache_size=10000")
                cursor.execute("PRAGMA temp_store=MEMORY")
                cursor.close()
        
        logger.info(f"Engine de banco criado: {database_url}")
        return engine
        
    except Exception as e:
        logger.error(f"Erro ao criar engine: {e}")
        raise AppDatabaseError(
            message=f"Falha ao criar engine: {str(e)}",
            details={"database_url": database_url, "error": str(e)}
        ) from e


@lru_cache()
def get_engine() -> Engine:
    """Factory singleton para engine de banco."""
    return create_database_engine()


def get_session_factory() -> sessionmaker[Session]:
    """Factory para criar sessionmaker configurado."""
    engine = get_engine()
    
    return sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


@contextmanager
def get_db_transaction() -> Generator[Session, None, None]:
    """Context manager para transações com commit/rollback automático."""
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        logger.debug("Iniciando transação")
        yield session
        session.commit()
        logger.debug("Transação commitada")
        
    except SQLAlchemyError as e:
        logger.error(f"Erro SQLAlchemy: {e}")
        session.rollback()
        logger.debug("Rollback executado")
        
        raise AppDatabaseError(
            message=f"Erro de banco: {str(e)}",
            details={"error_type": type(e).__name__, "error": str(e)}
        ) from e
        
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        session.rollback()
        logger.debug("Rollback por erro inesperado")
        raise
        
    finally:
        session.close()
        logger.debug("Sessão fechada")


def test_database_connection() -> bool:
    """Testa conectividade com banco executando query simples."""
    try:
        engine = get_engine()
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test_value"))
            test_value = result.scalar()
            
            if test_value == 1:
                logger.info("Teste de conexão bem-sucedido")
                return True
            else:
                raise AppDatabaseError(
                    message="Teste falhou: resultado inesperado",
                    details={"expected": 1, "received": test_value}
                )
                
    except (OperationalError, DatabaseError, DisconnectionError) as e:
        logger.error(f"Erro de conectividade: {e}")
        raise AppDatabaseError(
            message=f"Falha na conexão: {str(e)}",
            details={"error_type": type(e).__name__}
        ) from e
        
    except Exception as e:
        logger.error(f"Erro inesperado ao testar conexão: {e}")
        raise AppDatabaseError(
            message=f"Erro inesperado: {str(e)}",
            details={"error_type": type(e).__name__}
        ) from e


def init_database() -> None:
    """Inicializa banco criando todas as tabelas."""
    try:
        engine = get_engine()
        logger.info("Inicializando banco de dados...")
        
        Base.metadata.create_all(bind=engine)
        logger.info("Banco inicializado com sucesso")
        
        # Testar conectividade
        test_database_connection()
        
    except Exception as e:
        logger.error(f"Erro ao inicializar banco: {e}")
        raise AppDatabaseError(
            message=f"Falha na inicialização: {str(e)}",
            details={"error": str(e)}
        ) from e


def get_database_info() -> Dict[str, Any]:
    """Retorna informações sobre configuração do banco."""
    engine = get_engine()
    
    return {
        "database_url": str(engine.url).replace(engine.url.password or "", "***"),
        "dialect": engine.dialect.name,
        "driver": engine.dialect.driver,
        "pool_size": getattr(engine.pool, 'size', lambda: "N/A")(),
        "max_overflow": getattr(engine.pool, '_max_overflow', "N/A"),
        "echo": engine.echo,
        "tables": list(Base.metadata.tables.keys()),
    }


def check_database_health() -> Dict[str, Any]:
    """Executa verificação de saúde do banco."""
    try:
        connection_ok = test_database_connection()
        db_info = get_database_info()
        engine = get_engine()
        
        pool_status = {
            "checked_in": getattr(engine.pool, 'checkedin', lambda: 0)(),
            "checked_out": getattr(engine.pool, 'checkedout', lambda: 0)(),
            "overflow": getattr(engine.pool, 'overflow', lambda: 0)(),
        }
        
        return {
            "status": "healthy" if connection_ok else "unhealthy",
            "connection_test": connection_ok,
            "database_info": db_info,
            "pool_status": pool_status,
        }
        
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "error_type": type(e).__name__,
        }


logger.info("Módulo de banco carregado")
logger.info(f"URL do banco: {settings.get_database_url()}")