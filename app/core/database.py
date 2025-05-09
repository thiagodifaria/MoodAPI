from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import os
from datetime import datetime

# Configuração do banco de dados
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sentiment_analysis.db")

# Criar engine do SQLAlchemy
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=False  # Definir como True para debug
)

# Criar sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos declarativos
Base = declarative_base()

def create_tables():
    """Cria todas as tabelas definidas nos modelos."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Fornece uma sessão de banco de dados."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    """Fornece um contexto de sessão de banco de dados."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """Inicializa o banco de dados com tabelas e dados iniciais."""
    create_tables()
    
    # Inicializa estatísticas da API
    from app.core.models import ApiStats
    
    with get_db_context() as db:
        # Verifica se já existem estatísticas
        stats = db.query(ApiStats).first()
        if not stats:
            # Cria estatísticas iniciais
            stats = ApiStats(
                requests_count=0,
                avg_response_time_ms=0.0,  # CORRIGIDO: nome correto do campo
                error_count=0,
                date=datetime.utcnow()  # CORRIGIDO: removido last_request, adicionado date
            )
            db.add(stats)