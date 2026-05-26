from datetime import date, datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class HistoryFilter(BaseModel):
    """Filtros opcionais para consultas de histórico."""
    
    sentiment: Literal["positive", "negative", "neutral"] | None = Field(
        default=None,
        description="Filtrar por sentimento específico"
    )
    
    language: Annotated[
        str | None,
        Field(
            default=None,
            min_length=2,
            max_length=5,
            description="Filtrar por código de idioma (ex: 'pt', 'en')",
            examples=["pt", "en", "es"]
        )
    ] = None
    
    min_confidence: Annotated[
        float | None,
        Field(
            default=None,
            ge=0.0,
            le=1.0,
            description="Confiança mínima do modelo"
        )
    ] = None
    
    max_confidence: Annotated[
        float | None,
        Field(
            default=None,
            ge=0.0,
            le=1.0,
            description="Confiança máxima do modelo"
        )
    ] = None
    
    start_date: date | None = Field(
        default=None,
        description="Data inicial (YYYY-MM-DD)"
    )
    
    end_date: date | None = Field(
        default=None,
        description="Data final (YYYY-MM-DD)"
    )
    
    text_contains: Annotated[
        str | None,
        Field(
            default=None,
            min_length=2,
            max_length=100,
            description="Buscar texto que contenha esta substring"
        )
    ] = None
    
    @model_validator(mode="after")
    def validate_filters(self) -> "HistoryFilter":
        """Valida combinações de filtros."""
        if (
            self.min_confidence is not None 
            and self.max_confidence is not None 
            and self.min_confidence > self.max_confidence
        ):
            raise ValueError("min_confidence deve ser menor ou igual a max_confidence")
        
        if (
            self.start_date is not None 
            and self.end_date is not None 
            and self.start_date > self.end_date
        ):
            raise ValueError("start_date deve ser anterior ou igual a end_date")
        
        return self
    
    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True
    }


class PaginationParams(BaseModel):
    """Parâmetros de paginação com validação otimizada."""
    
    page: Annotated[
        int,
        Field(
            default=1,
            ge=1,
            le=10000,
            description="Número da página (1-based)"
        )
    ]
    
    limit: Annotated[
        int,
        Field(
            default=50,
            ge=1,
            le=500,
            description="Itens por página (máximo 500)"
        )
    ]
    
    @property
    def offset(self) -> int:
        """Calcula offset baseado na página."""
        return (self.page - 1) * self.limit
    
    @property
    def sql_limit(self) -> int:
        """Retorna limit para SQL."""
        return self.limit
    
    @property
    def sql_offset(self) -> int:
        """Retorna offset para SQL."""
        return self.offset
    
    model_config = {
        "extra": "forbid"
    }


class SortParams(BaseModel):
    """Parâmetros de ordenação."""
    
    sort_by: Literal["created_at", "confidence", "sentiment"] = Field(
        default="created_at",
        description="Campo para ordenação"
    )
    
    sort_order: Literal["asc", "desc"] = Field(
        default="desc",
        description="Direção da ordenação"
    )
    
    model_config = {
        "extra": "forbid"
    }


class HistoryItem(BaseModel):
    """Item individual do histórico de análises."""
    
    id: str = Field(description="ID único da análise")
    sentiment: Literal["positive", "negative", "neutral"]
    confidence: float = Field(ge=0.0, le=1.0)
    language: str = Field(min_length=2, max_length=5)
    text: str | None = Field(default=None, description="Texto ou preview para compatibilidade")
    text_preview: str = Field(description="Preview do texto analisado")
    text_length: int = Field(ge=0, description="Comprimento do texto original")
    created_at: datetime
    all_scores: list[dict[str, str | float]] = Field(default_factory=list)
    request_id: str | None = None
    model_name: str | None = None
    model_version: str | None = None
    processing_time_ms: float | None = Field(default=None, ge=0.0)
    cache_hit: bool = False
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }


class PaginationMeta(BaseModel):
    """Metadados de paginação."""
    
    total: int = Field(ge=0, description="Total de itens")
    page: int = Field(ge=1, description="Página atual")
    limit: int = Field(ge=1, description="Itens por página")
    pages: int = Field(ge=0, description="Total de páginas")
    has_next: bool = Field(description="Há próxima página")
    has_prev: bool = Field(description="Há página anterior")
    
    @classmethod
    def create(cls, total: int, page: int, limit: int) -> "PaginationMeta":
        """Factory para criar metadados de paginação."""
        pages = (total + limit - 1) // limit if total > 0 else 0
        return cls(
            total=total,
            page=page,
            limit=limit,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )


class HistoryResponse(BaseModel):
    """Response para consultas de histórico com paginação."""
    
    items: list[HistoryItem]
    pagination: PaginationMeta
    filters_applied: dict[str, Any] = Field(
        default_factory=dict,
        description="Filtros aplicados na consulta"
    )
    query_time_ms: float | None = Field(
        default=None,
        description="Tempo da consulta em milissegundos"
    )
    cached: bool = Field(default=False, description="Resultado obtido do cache")
    
    model_config = {
        "extra": "forbid"
    }


class SentimentDistribution(BaseModel):
    """Distribuição de sentimentos."""
    
    positive: int = Field(ge=0)
    negative: int = Field(ge=0)
    neutral: int = Field(ge=0)


class LanguageDistribution(BaseModel):
    """Distribuição de idiomas."""
    
    language: str = Field(min_length=2, max_length=5)
    count: int = Field(ge=0)
    percentage: float = Field(ge=0.0, le=100.0)


class DailyVolume(BaseModel):
    """Volume diário de análises."""
    
    date: date
    count: int = Field(ge=0)
    avg_confidence: float = Field(ge=0.0, le=1.0)


class AnalyticsResponse(BaseModel):
    """Response para analytics e estatísticas."""
    
    sentiment_distribution: SentimentDistribution
    language_distribution: list[LanguageDistribution]
    daily_volume: list[DailyVolume] = Field(
        description="Volume dos últimos 30 dias"
    )
    avg_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confiança média geral"
    )
    total_analyses: int = Field(ge=0)
    date_range: dict[str, date] = Field(
        description="Intervalo de datas analisado"
    )
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp da geração"
    )
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }
    }


class StatsFilter(BaseModel):
    """Filtros para consultas de estatísticas."""
    
    period: Literal["7d", "30d", "90d", "1y"] = Field(
        default="30d",
        description="Período para estatísticas"
    )
    
    group_by: Literal["day", "week", "month"] = Field(
        default="day",
        description="Agrupamento temporal"
    )
    
    model_config = {
        "extra": "forbid"
    }


class TrendData(BaseModel):
    """Dados de tendência temporal."""
    
    period: str = Field(description="Período (ex: '2024-01-15')")
    sentiment_counts: dict[str, int] = Field(
        description="Contagens por sentimento"
    )
    total_count: int = Field(ge=0)
    avg_confidence: float = Field(ge=0.0, le=1.0)


class StatsResponse(BaseModel):
    """Response para estatísticas agregadas."""
    
    period: str = Field(description="Período analisado")
    group_by: str = Field(default="day", description="Agrupamento temporal usado")
    total_analyses: int = Field(ge=0)
    avg_confidence: float = Field(ge=0.0, le=1.0)
    top_languages: list[LanguageDistribution] = Field(
        description="Top 5 idiomas"
    )
    sentiment_trend: list[TrendData] = Field(
        description="Tendência de sentimentos no período"
    )
    high_confidence_percentage: float = Field(
        ge=0.0,
        le=100.0,
        description="% de análises com alta confiança (>0.8)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow
    )
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }


class AnalysisDetail(BaseModel):
    """Detalhes completos de uma análise específica."""
    
    id: str
    text: str = Field(description="Texto original completo")
    sentiment: Literal["positive", "negative", "neutral"]
    confidence: float = Field(ge=0.0, le=1.0)
    language: str = Field(min_length=2, max_length=5)
    all_scores: list[dict[str, str | float]]
    created_at: datetime
    updated_at: datetime | None = None
    request_id: str | None = None
    actor_id: str | None = None
    model_name: str | None = None
    model_version: str | None = None
    text_hash: str | None = None
    processing_time_ms: float | None = Field(default=None, ge=0.0)
    cache_hit: bool = False
    
    # Métricas derivadas
    is_high_confidence: bool = Field(
        description="Se tem alta confiança (>=0.8)"
    )
    
    confidence_level: Literal["high", "medium", "low"] = Field(
        description="Nível de confiança categorizado"
    )
    
    @field_validator("is_high_confidence", mode="before")
    @classmethod
    def compute_high_confidence(cls, v, info) -> bool:
        """Calcula se tem alta confiança."""
        if info.data and "confidence" in info.data:
            return info.data["confidence"] >= 0.8
        return False
    
    @field_validator("confidence_level", mode="before")
    @classmethod
    def compute_confidence_level(cls, v, info) -> str:
        """Calcula nível de confiança."""
        if info.data and "confidence" in info.data:
            confidence = info.data["confidence"]
            if confidence >= 0.8:
                return "high"
            elif confidence >= 0.6:
                return "medium"
            else:
                return "low"
        return "low"
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }


class DeleteResponse(BaseModel):
    """Response para operações de exclusão."""
    
    success: bool
    message: str
    deleted_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }


# Schemas auxiliares para validação de cache
class CacheKeyParams(BaseModel):
    """Parâmetros para geração de chave de cache."""
    
    endpoint: str
    filters: dict[str, Any] = Field(default_factory=dict)
    pagination: dict[str, int] | None = None
    
    def generate_key(self) -> str:
        """Gera chave de cache determinística."""
        import hashlib
        import json
        
        data = {
            "endpoint": self.endpoint,
            "filters": self.filters,
            "pagination": self.pagination
        }
        
        # Ordenar para garantir determinismo
        json_str = json.dumps(data, sort_keys=True, separators=(',', ':'), default=str)
        hash_obj = hashlib.md5(json_str.encode('utf-8'))
        return f"history:{hash_obj.hexdigest()}"


# Aliases para conveniência e compatibilidade
HistoryQueryParams = HistoryFilter
PaginationSettings = PaginationParams
AnalyticsData = AnalyticsResponse
StatsData = StatsResponse

