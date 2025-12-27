import logging
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseModel):
    url: str = Field(default="sqlite:///./data/sentiments.db")
    pool_size: int = Field(default=10, ge=1, le=50)
    max_overflow: int = Field(default=20, ge=0, le=100)
    pool_timeout: int = Field(default=30, ge=5, le=300)
    pool_recycle: int = Field(default=3600, ge=300, le=86400)
    echo: bool = Field(default=False)

    @field_validator("url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v:
            raise ValueError("URL do banco de dados não pode estar vazia")
        if v.startswith("sqlite:///"):
            db_path = Path(v.replace("sqlite:///", ""))
            db_path.parent.mkdir(parents=True, exist_ok=True)
        return v


class CacheConfig(BaseModel):
    url: str = Field(default="redis://localhost:6379/0")
    max_connections: int = Field(default=20, ge=1, le=100)
    socket_timeout: float = Field(default=5.0, ge=1.0, le=30.0)
    socket_connect_timeout: float = Field(default=5.0, ge=1.0, le=30.0)
    retry_on_timeout: bool = Field(default=True)
    health_check_interval: int = Field(default=30, ge=10, le=300)
    default_ttl: int = Field(default=3600, ge=60, le=86400)
    key_prefix: str = Field(default="moodapi:")

    @field_validator("url")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        if not v.startswith(("redis://", "rediss://")):
            raise ValueError("URL do Redis deve começar com redis:// ou rediss://")
        return v


class MLConfig(BaseModel):
    model_name: str = Field(default="cardiffnlp/twitter-roberta-base-sentiment-latest")
    model_cache_dir: Optional[str] = Field(default="./models")
    max_text_length: int = Field(default=2000, ge=10, le=10000)
    min_text_length: int = Field(default=1, ge=1, le=100)
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    batch_size: int = Field(default=32, ge=1, le=128)
    device: Literal["auto", "cpu", "cuda"] = Field(default="auto")

    @field_validator("model_cache_dir")
    @classmethod
    def validate_model_cache_dir(cls, v: Optional[str]) -> Optional[str]:
        if v:
            Path(v).mkdir(parents=True, exist_ok=True)
        return v


class RateLimitConfig(BaseModel):
    requests_per_minute: int = Field(default=100, ge=1, le=10000)
    requests_per_hour: int = Field(default=1000, ge=1, le=100000)
    burst_size: int = Field(default=10, ge=1, le=100)
    enabled: bool = Field(default=True)


class ServerConfig(BaseModel):
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1024, le=65535)
    workers: int = Field(default=1, ge=1, le=16)
    reload: bool = Field(default=False)


class Settings(BaseSettings):
    """Configurações principais da aplicação MoodAPI."""
    
    model_config = SettingsConfigDict(
        env_prefix="MOODAPI_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_assignment=True,
    )
    
    # Configurações da aplicação
    app_name: str = Field(default="MoodAPI")
    app_version: str = Field(default="1.0.0")
    app_description: str = Field(default="API multilíngue de análise de sentimentos")
    debug: bool = Field(default=False)
    environment: Literal["development", "staging", "production"] = Field(default="development")
    
    # Configurações por domínio
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    ml: MLConfig = Field(default_factory=MLConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    
    # Configurações de logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")
    log_format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Configurações de segurança - CORS dinâmico baseado em ambiente
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"]
    )
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: list[str] = Field(default=["GET", "POST", "DELETE", "PUT", "PATCH", "OPTIONS"])
    cors_allow_headers: list[str] = Field(default=["*"])
    
    # Domínios permitidos em produção (configurável via env)
    cors_production_origins: list[str] = Field(
        default_factory=lambda: ["https://moodapi.example.com"]
    )
    
    @property
    def effective_cors_origins(self) -> list[str]:
        """Retorna CORS origins baseado no ambiente."""
        if self.is_production:
            return self.cors_production_origins
        return self.cors_origins

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        level = v.upper()
        if level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(f"Nível de log inválido: {v}")
        logging.basicConfig(
            level=getattr(logging, level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        return level

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    def get_database_url(self) -> str:
        return self.database.url

    def get_cache_url(self) -> str:
        return self.cache.url

    def get_cache_key(self, key: str) -> str:
        return f"{self.cache.key_prefix}{key}"


@lru_cache()
def get_settings() -> Settings:
    """Factory para obter instância singleton das configurações."""
    return Settings()


# Instância global das configurações
settings = get_settings()

# Logger
logger = logging.getLogger(__name__)
logger.info(f"Configurações carregadas - Ambiente: {settings.environment}")