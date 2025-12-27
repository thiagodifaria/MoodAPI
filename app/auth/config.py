"""
Configuração de autenticação JWT.
"""
import logging
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class AuthConfig(BaseSettings):
    """Configurações de autenticação JWT."""
    
    model_config = SettingsConfigDict(
        env_prefix="MOODAPI_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # JWT Settings
    jwt_secret_key: str = Field(
        default="your-super-secret-key-change-in-production-immediately",
        description="Chave secreta para assinar tokens JWT"
    )
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = Field(
        default="HS256",
        description="Algoritmo de assinatura JWT"
    )
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        ge=5,
        le=1440,  # Máximo 24 horas
        description="Tempo de expiração do token de acesso em minutos"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Tempo de expiração do token de refresh em dias"
    )
    
    # Bcrypt Settings
    bcrypt_rounds: int = Field(
        default=12,
        ge=4,
        le=16,
        description="Número de rounds para hashing de senha"
    )
    
    # Admin Settings
    admin_username: str = Field(
        default="admin",
        description="Username do admin padrão"
    )
    admin_email: str = Field(
        default="admin@moodapi.local",
        description="Email do admin padrão"
    )
    admin_password: str = Field(
        default="changeme123",
        description="Senha do admin padrão (MUDE EM PRODUÇÃO!)"
    )
    
    # Feature Flags
    auth_enabled: bool = Field(
        default=True,
        description="Se autenticação está habilitada"
    )
    registration_enabled: bool = Field(
        default=True,
        description="Se registro de novos usuários está habilitado"
    )


@lru_cache()
def get_auth_config() -> AuthConfig:
    """Factory singleton para configuração de autenticação."""
    config = AuthConfig()
    
    # Aviso de segurança
    if "change" in config.jwt_secret_key.lower() or len(config.jwt_secret_key) < 32:
        logger.warning(
            "⚠️  JWT_SECRET_KEY não configurada ou muito curta! "
            "Configure MOODAPI_JWT_SECRET_KEY em .env para produção."
        )
    
    return config


logger.info("Módulo de configuração de autenticação carregado")
