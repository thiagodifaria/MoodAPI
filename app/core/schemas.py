from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from enum import Enum
from pydantic import BaseModel, Field, validator


class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class EmotionSet(BaseModel):
    joy: float = Field(0.0, ge=0.0, le=1.0)
    surprise: float = Field(0.0, ge=0.0, le=1.0)
    sadness: float = Field(0.0, ge=0.0, le=1.0)
    anger: float = Field(0.0, ge=0.0, le=1.0)
    fear: float = Field(0.0, ge=0.0, le=1.0)


class Entity(BaseModel):
    text: str
    type: str
    sentiment: str
    score: float = Field(ge=-1.0, le=1.0)


class SentimentResult(BaseModel):
    label: SentimentLabel
    score: float = Field(ge=-1.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)


class AnalysisBase(BaseModel):
    text: str
    language: Optional[str] = None


class BasicAnalysisRequest(AnalysisBase):
    pass


class DetailedAnalysisRequest(AnalysisBase):
    pass


class BatchAnalysisRequest(BaseModel):
    texts: List[str]
    language: Optional[str] = None
    analysis_type: str = "basic"

    @validator("analysis_type")
    def validate_analysis_type(cls, v):
        if v not in ["basic", "detailed"]:
            raise ValueError("analysis_type must be either 'basic' or 'detailed'")
        return v


class BasicAnalysisResponse(BaseModel):
    id: str
    timestamp: datetime
    text: str
    language: str
    sentiment: SentimentResult
    processing_time_ms: int

    class Config:
        from_attributes=True


class DetailedAnalysisResponse(BasicAnalysisResponse):
    emotions: Optional[EmotionSet] = None
    entities: Optional[List[Entity]] = None
    keywords: Optional[List[str]] = None


class HistoryItem(BaseModel):
    id: str
    timestamp: datetime
    text: str
    sentiment: str

    class Config:
        from_attributes=True


class HistoryResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: List[HistoryItem]


# Classes adicionadas para resolver o problema de importação
class SentimentDistribution(BaseModel):
    positive: int = 0
    negative: int = 0
    neutral: int = 0
    
    class Config:
        from_attributes=True


class LanguageDistribution(BaseModel):
    entries: Dict[str, int]
    
    class Config:
        from_attributes=True


class TimeframeStats(BaseModel):
    date: datetime
    requests_count: int
    avg_response_time_ms: float
    
    class Config:
        from_attributes=True


class StatsResponse(BaseModel):
    total_analyses: int
    sentiment_distribution: SentimentDistribution
    language_distribution: LanguageDistribution
    timeframe_stats: List[TimeframeStats]
    last_updated: datetime
    
    class Config:
        from_attributes=True


class ApiStatsResponse(BaseModel):
    date: datetime
    requests_count: int
    avg_response_time_ms: float
    error_count: int
    analysis_count: Dict[str, int]

    class Config:
        from_attributes=True

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: float
    database_connection: bool
    nlp_models_loaded: bool