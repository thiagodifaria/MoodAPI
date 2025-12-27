"""
TypedDicts para retornos estruturados com tipagem precisa.

Substitui Dict[str, Any] por tipos explícitos para melhor documentação e IDE support.
"""
from datetime import datetime
from typing import List, Literal, Optional, TypedDict


class SentimentScore(TypedDict):
    """Score individual de sentimento."""
    label: Literal["positive", "negative", "neutral"]
    score: float


class AnalysisResult(TypedDict):
    """Resultado de análise de sentimento."""
    sentiment: Literal["positive", "negative", "neutral"]
    confidence: float
    language: str
    all_scores: List[SentimentScore]


class AnalysisResultFull(AnalysisResult):
    """Resultado completo com metadados."""
    text: str
    cached: bool
    response_time_ms: float
    timestamp: str
    record_id: Optional[str]


class BatchAnalysisResult(TypedDict):
    """Resultado de análise em lote."""
    results: List[AnalysisResult]
    total_processed: int
    processing_time_ms: float


class ModelInfo(TypedDict):
    """Informações do modelo ML."""
    model_name: str
    model_loaded: bool
    device: str
    max_text_length: int
    min_text_length: int
    batch_size: int
    transformers_compatibility: str


class CacheStats(TypedDict):
    """Estatísticas de cache."""
    hits: int
    misses: int
    sets: int
    deletes: int
    errors: int
    fallback_operations: int
    hit_rate: float


class ServiceStats(TypedDict):
    """Estatísticas do serviço."""
    cache_hits: int
    cache_misses: int
    analyses_performed: int
    errors: int


class HealthStatus(TypedDict):
    """Status de saúde do serviço."""
    status: Literal["healthy", "degraded", "unhealthy"]
    services: dict
    model_info: ModelInfo
