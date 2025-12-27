"""
Dependencies de autenticação para FastAPI.
"""
import logging
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.config import get_auth_config
from app.auth.models import User
from app.auth.service import AuthService, get_auth_service
from app.dependencies import get_db_session

logger = logging.getLogger(__name__)
config = get_auth_config()

# Security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Session = Depends(get_db_session)
) -> Optional[User]:
    """
    Obtém usuário atual do token JWT.
    
    Retorna None se não houver token (endpoints opcionalmente protegidos).
    """
    if not config.auth_enabled:
        return None
    
    if not credentials:
        return None
    
    token = credentials.credentials
    auth_service = get_auth_service(db)
    
    token_data = auth_service.verify_token(token)
    if not token_data:
        return None
    
    user = auth_service.get_user_by_id(token_data.sub)
    if not user or not user.is_active:
        return None
    
    return user


async def get_current_active_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Session = Depends(get_db_session)
) -> User:
    """
    Obtém usuário atual ativo (obrigatório).
    
    Levanta HTTPException se não autenticado.
    """
    if not config.auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Autenticação desabilitada"
        )
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    auth_service = get_auth_service(db)
    
    token_data = auth_service.verify_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = auth_service.get_user_by_id(token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário desativado"
        )
    
    return user


async def require_admin(
    user: User = Depends(get_current_active_user)
) -> User:
    """
    Requer que usuário seja administrador.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Privilégios de administrador requeridos"
        )
    
    return user


# Type aliases para injeção de dependências
CurrentUser = Annotated[Optional[User], Depends(get_current_user)]
RequiredUser = Annotated[User, Depends(get_current_active_user)]
AdminUser = Annotated[User, Depends(require_admin)]
