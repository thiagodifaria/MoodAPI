"""
Protocolos (interfaces) para tipagem estrutural.

Permite type hints mais precisos e facilita testes com mocks.
"""
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class CacheProtocol(Protocol):
    """Interface para serviços de cache."""
    
    async def get(self, key: str) -> Any | None:
        """Obtém valor do cache."""
        ...
    
    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Define valor no cache."""
        ...
    
    async def delete(self, key: str) -> bool:
        """Remove valor do cache."""
        ...
    
    async def ping(self) -> bool:
        """Testa conectividade."""
        ...
    
    async def get_stats(self) -> dict[str, Any]:
        """Retorna estatísticas."""
        ...
    
    async def close(self) -> None:
        """Fecha conexões."""
        ...


@runtime_checkable
class AnalyzerProtocol(Protocol):
    """Interface para analisadores de sentimento."""
    
    def analyze(self, text: str) -> dict[str, Any]:
        """Analisa sentimento de um texto."""
        ...
    
    def analyze_batch(self, texts: list[str]) -> list[dict[str, Any]]:
        """Analisa múltiplos textos."""
        ...
    
    def get_model_info(self) -> dict[str, Any]:
        """Retorna informações do modelo."""
        ...


@runtime_checkable
class RepositoryProtocol(Protocol):
    """Interface base para repositórios."""
    
    def get_by_id(self, id: str) -> Any | None:
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
    
    def authenticate(self, username: str, password: str) -> dict[str, Any] | None:
        """Autentica usuário."""
        ...
    
    def create_access_token(self, data: dict[str, Any]) -> str:
        """Cria token JWT."""
        ...
    
    def verify_token(self, token: str) -> dict[str, Any] | None:
        """Verifica e decodifica token."""
        ...
