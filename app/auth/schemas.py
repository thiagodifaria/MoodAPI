"""
Schemas Pydantic para autenticação.
"""
from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Schema base para usuário."""
    username: Annotated[
        str,
        Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    ]
    email: EmailStr
    full_name: Optional[str] = Field(default=None, max_length=100)


class UserCreate(UserBase):
    """Schema para criação de usuário."""
    password: Annotated[
        str,
        Field(min_length=8, max_length=100, description="Senha deve ter no mínimo 8 caracteres")
    ]
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Valida força da senha."""
        if not any(c.isupper() for c in v):
            raise ValueError("Senha deve conter pelo menos uma letra maiúscula")
        if not any(c.islower() for c in v):
            raise ValueError("Senha deve conter pelo menos uma letra minúscula")
        if not any(c.isdigit() for c in v):
            raise ValueError("Senha deve conter pelo menos um número")
        return v


class UserUpdate(BaseModel):
    """Schema para atualização de usuário."""
    full_name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[EmailStr] = None


class UserResponse(UserBase):
    """Schema de resposta para usuário."""
    id: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }


class UserInDB(UserResponse):
    """Schema de usuário com dados do banco."""
    hashed_password: str


# Schemas de autenticação

class LoginRequest(BaseModel):
    """Schema para requisição de login."""
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=100)


class TokenResponse(BaseModel):
    """Schema de resposta com token JWT."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Tempo de expiração em segundos")
    user: UserResponse


class TokenData(BaseModel):
    """Dados decodificados do token JWT."""
    sub: str  # user_id
    username: str
    email: str
    is_admin: bool = False
    exp: datetime


class RefreshTokenRequest(BaseModel):
    """Schema para refresh de token."""
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    """Schema para mudança de senha."""
    current_password: str = Field(min_length=1)
    new_password: Annotated[
        str,
        Field(min_length=8, max_length=100)
    ]
    
    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Valida força da nova senha."""
        if not any(c.isupper() for c in v):
            raise ValueError("Senha deve conter pelo menos uma letra maiúscula")
        if not any(c.islower() for c in v):
            raise ValueError("Senha deve conter pelo menos uma letra minúscula")
        if not any(c.isdigit() for c in v):
            raise ValueError("Senha deve conter pelo menos um número")
        return v


class MessageResponse(BaseModel):
    """Schema genérico para mensagens."""
    message: str
    success: bool = True
