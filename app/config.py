import os
from datetime import datetime
from typing import List

# Application settings
APP_NAME = "Sentiment Analysis API"
APP_VERSION = "1.0.0"
APP_START_TIME = datetime.now()
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")

# Server settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
WORKERS = int(os.getenv("WORKERS", "1"))

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sentiment_api.db")
DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "5"))
DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
DATABASE_POOL_TIMEOUT = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))

# CORS settings
CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")

# NLP settings
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.6"))
TEXT_MAX_LENGTH = int(os.getenv("TEXT_MAX_LENGTH", "5000"))
BATCH_MAX_SIZE = int(os.getenv("BATCH_MAX_SIZE", "20"))

# Api rate limiting
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "False").lower() in ("true", "1", "t")
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "100"))  # requests per hour

# Authentication
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "False").lower() in ("true", "1", "t")
API_KEY = os.getenv("API_KEY", "")  # For simple API key auth
JWT_SECRET = os.getenv("JWT_SECRET", "")  # For JWT auth
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION", "3600"))  # seconds

# Model paths and configurations
MODELS_DIR = os.getenv("MODELS_DIR", "./models")
SENTIMENT_MODEL = os.getenv("SENTIMENT_MODEL", "default")  # 'default' uses TextBlob
EMOTION_MODEL = os.getenv("EMOTION_MODEL", "default")  # 'default' uses rule-based approach
ENTITY_MODEL = os.getenv("ENTITY_MODEL", "default")  # 'default' uses NLTK