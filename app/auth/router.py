"""
Router de autenticação com endpoints de login e registro.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.config import get_auth_config
from app.auth.dependencies import RequiredUser
from app.auth.schemas import (
    LoginRequest,
    MessageResponse,
    PasswordChangeRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.auth.service import get_auth_service
from app.dependencies import get_db_session

logger = logging.getLogger(__name__)
config = get_auth_config()

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["authentication"],
    responses={
        401: {"description": "Não autenticado"},
        403: {"description": "Acesso negado"}
    }
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar novo usuário",
    description="Cria uma nova conta de usuário"
)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db_session)
) -> UserResponse:
    """
    Registra um novo usuário.
    
    - **username**: Nome de usuário único (3-50 caracteres, alfanumérico)
    - **email**: Email válido
    - **password**: Senha forte (mín. 8 chars, maiúscula, minúscula, número)
    - **full_name**: Nome completo (opcional)
    """
    if not config.registration_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registro de novos usuários desabilitado"
        )
    
    auth_service = get_auth_service(db)
    
    try:
        user = auth_service.create_user(user_data)
        logger.info(f"Novo usuário registrado: {user.username}")
        return UserResponse.model_validate(user)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Fazer login",
    description="Autentica usuário e retorna token JWT"
)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db_session)
) -> TokenResponse:
    """
    Autentica usuário e retorna token de acesso.
    
    - **username**: Nome de usuário
    - **password**: Senha
    
    Retorna token JWT válido por 30 minutos (configurável).
    """
    auth_service = get_auth_service(db)
    
    user = auth_service.authenticate_user(
        username=login_data.username,
        password=login_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    access_token = auth_service.create_access_token(user)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=config.jwt_access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user)
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Dados do usuário atual",
    description="Retorna informações do usuário autenticado"
)
async def get_current_user_info(
    current_user: RequiredUser
) -> UserResponse:
    """
    Retorna dados do usuário autenticado.
    
    Requer token JWT válido no header Authorization.
    """
    return UserResponse.model_validate(current_user)


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Alterar senha",
    description="Altera a senha do usuário autenticado"
)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: RequiredUser,
    db: Session = Depends(get_db_session)
) -> MessageResponse:
    """
    Altera a senha do usuário autenticado.
    
    - **current_password**: Senha atual
    - **new_password**: Nova senha (mesmas regras de força)
    """
    auth_service = get_auth_service(db)
    
    # Verificar senha atual
    if not auth_service.verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta"
        )
    
    # Atualizar senha
    current_user.hashed_password = auth_service.hash_password(password_data.new_password)
    db.commit()
    
    logger.info(f"Senha alterada para usuário: {current_user.username}")
    
    return MessageResponse(
        message="Senha alterada com sucesso",
        success=True
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Fazer logout",
    description="Invalida a sessão atual (client-side)"
)
async def logout(
    current_user: RequiredUser
) -> MessageResponse:
    """
    Logout do usuário.
    
    Nota: JWT é stateless, o logout real deve ser feito client-side
    removendo o token. Este endpoint apenas confirma a ação.
    """
    logger.info(f"Logout: {current_user.username}")
    
    return MessageResponse(
        message="Logout realizado com sucesso",
        success=True
    )


@router.get(
    "/verify",
    response_model=MessageResponse,
    summary="Verificar token",
    description="Verifica se o token JWT é válido"
)
async def verify_token(
    current_user: RequiredUser
) -> MessageResponse:
    """
    Verifica se o token JWT é válido.
    
    Retorna sucesso se o token for válido, erro 401 caso contrário.
    """
    return MessageResponse(
        message=f"Token válido para usuário: {current_user.username}",
        success=True
    )
