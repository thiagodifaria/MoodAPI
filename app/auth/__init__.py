"""
Módulo de autenticação JWT para MoodAPI.

Implementa:
- Registro e login de usuários
- Tokens JWT para autenticação
- Proteção de endpoints
"""
from app.auth.config import AuthConfig, get_auth_config
from app.auth.dependencies import get_current_user, get_current_active_user, require_admin
from app.auth.router import router as auth_router

__all__ = [
    "AuthConfig",
    "get_auth_config",
    "get_current_user",
    "get_current_active_user",
    "require_admin",
    "auth_router",
]
