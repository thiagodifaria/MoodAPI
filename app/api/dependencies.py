"""
API dependencies for the sentiment analysis service.
This module provides dependencies for FastAPI, including:
- Authentication
- Rate limiting
- Service injection
- Request validation
"""
from typing import Optional, Dict, List, Callable, Any
import time
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import settings
from app.core.database import get_db
from app.services.analyzer import SentimentAnalyzer
from app.services.storage import StorageService

# Dependency for the sentiment analyzer service
def get_analyzer() -> SentimentAnalyzer:
    """
    Provides the sentiment analyzer service instance.
    
    Returns:
        SentimentAnalyzer instance
    """
    return SentimentAnalyzer()

# Dependency for the storage service
def get_storage_service(db=Depends(get_db)) -> StorageService:
    """
    Provides the storage service instance with DB session.
    
    Args:
        db: Database session from get_db dependency
        
    Returns:
        StorageService instance
    """
    return StorageService(db)

# Rate limiting dependency
class RateLimiter:
    """
    Rate limiter to prevent API abuse.
    
    Attributes:
        requests: Dictionary mapping client IPs to request history
        max_requests: Maximum number of requests allowed per time window
        window_size: Time window in seconds
    """
    def __init__(self, max_requests: int = 60, window_size: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in the time window
            window_size: Time window size in seconds
        """
        self.requests: Dict[str, List[float]] = {}
        self.max_requests = max_requests
        self.window_size = window_size
    
    def __call__(self, request: Request) -> None:
        """
        Check if request exceeds rate limit.
        
        Args:
            request: FastAPI request object
            
        Raises:
            HTTPException: If rate limit is exceeded
        """
        if not settings.RATE_LIMITING_ENABLED:
            return
            
        # Get client identifier (IP address or API key)
        client_id = self._get_client_id(request)
        
        # Get current timestamp
        now = time.time()
        
        # Initialize request history for new clients
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Remove requests outside the current time window
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if now - req_time <= self.window_size
        ]
        
        # Check if rate limit is exceeded
        if len(self.requests[client_id]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.max_requests} requests per {self.window_size} seconds."
            )
        
        # Add current request to history
        self.requests[client_id].append(now)
    
    def _get_client_id(self, request: Request) -> str:
        """
        Get client identifier from request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Client identifier (IP or API key)
        """
        # Use API key if available in headers
        api_key = request.headers.get("X-API-Key", "")
        if api_key:
            return api_key
        
        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            # Get first IP if multiple are provided
            return forwarded.split(",")[0].strip()
        
        # Use client host if no forwarded header
        return request.client.host if request.client else "unknown"

# Create instances of dependencies
rate_limiter = RateLimiter(
    max_requests=settings.RATE_LIMIT_MAX_REQUESTS,
    window_size=settings.RATE_LIMIT_WINDOW_SIZE
)

# Optional: API Key authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Optional: OAuth2 with JWT tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token", auto_error=False)

class TokenData(BaseModel):
    """Data model for JWT token claims."""
    username: Optional[str] = None
    exp: Optional[datetime] = None

# Authentication dependency
async def get_current_user(
    api_key: Optional[str] = Depends(api_key_header),
    token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[str]:
    """
    Authenticate the user based on API key or JWT token.
    
    Args:
        api_key: Optional API key from header
        token: Optional JWT token from OAuth2
        
    Returns:
        Username or API key identifier if authenticated, None otherwise
        
    Raises:
        HTTPException: If authentication fails and auth is required
    """
    if not settings.AUTH_REQUIRED:
        return None
    
    # Try API key authentication first
    if api_key and api_key in settings.API_KEYS:
        return f"api_key_{api_key[:8]}"
    
    # Fall back to JWT token
    if token:
        try:
            # Decode JWT token
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Extract username from payload
            username = payload.get("sub")
            if username:
                token_data = TokenData(username=username)
                return token_data.username
                
        except JWTError:
            pass
    
    # Authentication failed
    if settings.AUTH_REQUIRED:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return None

# Request size limiter
async def check_request_size(request: Request) -> None:
    """
    Check if request body exceeds maximum allowed size.
    
    Args:
        request: FastAPI request object
        
    Raises:
        HTTPException: If request body is too large
    """
    content_length = request.headers.get("content-length")
    if content_length:
        if int(content_length) > settings.MAX_REQUEST_SIZE_KB * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Request too large. Maximum size: {settings.MAX_REQUEST_SIZE_KB} KB"
            )

# Input text length limiter
def check_text_length(max_length: int = settings.MAX_TEXT_LENGTH) -> Callable:
    """
    Factory for dependencies that check text length.
    
    Args:
        max_length: Maximum allowed text length
        
    Returns:
        Dependency function
    """
    def validate_text_length(text: str) -> str:
        """
        Validate that text doesn't exceed maximum length.
        
        Args:
            text: Input text
            
        Returns:
            Original text if valid
            
        Raises:
            HTTPException: If text is too long
        """
        if len(text) > max_length:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Text too long. Maximum length: {max_length} characters"
            )
        return text
    
    return validate_text_length

# Batch size limiter
def check_batch_size(max_items: int = settings.MAX_BATCH_SIZE) -> Callable:
    """
    Factory for dependencies that check batch size.
    
    Args:
        max_items: Maximum allowed batch size
        
    Returns:
        Dependency function
    """
    def validate_batch_size(items: List[Any]) -> List[Any]:
        """
        Validate that batch doesn't exceed maximum size.
        
        Args:
            items: List of items
            
        Returns:
            Original items if valid
            
        Raises:
            HTTPException: If batch is too large
        """
        if len(items) > max_items:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Batch too large. Maximum size: {max_items} items"
            )
        return items
    
    return validate_batch_size