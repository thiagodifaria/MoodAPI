"""
Serviço de autenticação JWT.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.auth.config import get_auth_config
from app.auth.models import User
from app.auth.schemas import TokenData, UserCreate
from app.core.exceptions import AuthenticationError, AuthorizationError

logger = logging.getLogger(__name__)
config = get_auth_config()

# Contexto de criptografia para senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Serviço para operações de autenticação."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================
    # Password Handling
    # ==================
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica se a senha está correta."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def hash_password(self, password: str) -> str:
        """Gera hash da senha."""
        return pwd_context.hash(password)
    
    # ==================
    # User Operations
    # ==================
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Busca usuário por username."""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Busca usuário por email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Busca usuário por ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def create_user(self, user_data: UserCreate, is_admin: bool = False) -> User:
        """Cria novo usuário."""
        # Verificar se já existe
        if self.get_user_by_username(user_data.username):
            raise AuthenticationError("Username já está em uso")
        
        if self.get_user_by_email(user_data.email):
            raise AuthenticationError("Email já está em uso")
        
        # Criar usuário
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=self.hash_password(user_data.password),
            full_name=user_data.full_name,
            is_admin=is_admin
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"Usuário criado: {user.username}")
        return user
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Autentica usuário por username e senha."""
        user = self.get_user_by_username(username)
        
        if not user:
            logger.debug(f"Usuário não encontrado: {username}")
            return None
        
        if not self.verify_password(password, user.hashed_password):
            logger.debug(f"Senha incorreta para: {username}")
            return None
        
        if not user.is_active:
            logger.debug(f"Usuário inativo: {username}")
            return None
        
        # Atualizar último login
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Usuário autenticado: {username}")
        return user
    
    # ==================
    # Token Operations
    # ==================
    
    def create_access_token(self, user: User) -> str:
        """Cria token JWT de acesso."""
        expire = datetime.utcnow() + timedelta(minutes=config.jwt_access_token_expire_minutes)
        
        to_encode = {
            "sub": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin,
            "exp": expire
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            config.jwt_secret_key,
            algorithm=config.jwt_algorithm
        )
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verifica e decodifica token JWT."""
        try:
            payload = jwt.decode(
                token,
                config.jwt_secret_key,
                algorithms=[config.jwt_algorithm]
            )
            
            user_id = payload.get("sub")
            if user_id is None:
                logger.debug("Token sem 'sub' claim")
                return None
            
            return TokenData(
                sub=user_id,
                username=payload.get("username", ""),
                email=payload.get("email", ""),
                is_admin=payload.get("is_admin", False),
                exp=datetime.fromtimestamp(payload.get("exp", 0))
            )
            
        except JWTError as e:
            logger.debug(f"Erro ao decodificar token: {e}")
            return None
    
    # ==================
    # Admin Operations
    # ==================
    
    def ensure_admin_exists(self) -> None:
        """Garante que existe um usuário admin."""
        admin = self.get_user_by_username(config.admin_username)
        
        if not admin:
            logger.info("Criando usuário admin padrão...")
            
            admin_data = UserCreate(
                username=config.admin_username,
                email=config.admin_email,
                password=config.admin_password,
                full_name="Administrator"
            )
            
            self.create_user(admin_data, is_admin=True)
            logger.info(f"Admin criado: {config.admin_username}")
        else:
            logger.debug("Usuário admin já existe")


def get_auth_service(db: Session) -> AuthService:
    """Factory para criar instância do AuthService."""
    return AuthService(db)
