"""
Protocolos (interfaces) para tipagem estrutural.

Permite type hints mais precisos e facilita testes com mocks.
"""
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class CacheProtocol(Protocol):
    """Interface para serviços de cache."""
    
    async def get(self, key: str) -> Optional[Any]:
        """Obtém valor do cache."""
        ...
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Define valor no cache."""
        ...
    
    async def delete(self, key: str) -> bool:
        """Remove valor do cache."""
        ...
    
    async def ping(self) -> bool:
        """Testa conectividade."""
        ...
    
    async def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas."""
        ...
    
    async def close(self) -> None:
        """Fecha conexões."""
        ...


@runtime_checkable
class AnalyzerProtocol(Protocol):
    """Interface para analisadores de sentimento."""
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """Analisa sentimento de um texto."""
        ...
    
    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Analisa múltiplos textos."""
        ...
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retorna informações do modelo."""
        ...


@runtime_checkable
class RepositoryProtocol(Protocol):
    """Interface base para repositórios."""
    
    def get_by_id(self, id: str) -> Optional[Any]:
        """Busca por ID."""
        ...
    
    def create(self, entity: Any) -> Any:
        """Cria nova entidade."""
        ...
    
    def delete(self, id: str) -> bool:
        """Remove entidade."""
        ...


@runtime_checkable
class AuthServiceProtocol(Protocol):
    """Interface para serviços de autenticação."""
    
    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Autentica usuário."""
        ...
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Cria token JWT."""
        ...
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verifica e decodifica token."""
        ...
