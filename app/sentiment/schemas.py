import uuid
from datetime import datetime
from typing import Annotated, Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class AnalysisRequest(BaseModel):
    """Request para análise individual de sentimento."""
    
    text: Annotated[
        str,
        Field(
            min_length=1,
            max_length=2000,
            description="Texto a ser analisado (1-2000 caracteres)",
            examples=["Eu amo este produto!", "Serviço terrível"]
        )
    ]
    
    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Valida e limpa o texto de entrada."""
        if not v or not v.strip():
            raise ValueError("Texto não pode estar vazio")
        
        cleaned = v.strip()
        if len(cleaned) < 1:
            raise ValueError("Texto deve ter pelo menos 1 caractere")
        
        return cleaned
    
    model_config = {
        "str_strip_whitespace": True,
        "validate_assignment": True,
        "extra": "forbid"
    }


class BatchRequest(BaseModel):
    """Request para análise em lote de sentimentos."""
    
    texts: Annotated[
        List[str],
        Field(
            min_length=1,
            max_length=50,
            description="Lista de textos para análise (máximo 50 itens)",
            examples=[["Ótimo produto!", "Péssimo atendimento", "Experiência média"]]
        )
    ]
    
    @field_validator("texts")
    @classmethod
    def validate_texts(cls, v: List[str]) -> List[str]:
        """Valida lista de textos."""
        if not v:
            raise ValueError("Lista de textos não pode estar vazia")
        
        if len(v) > 50:
            raise ValueError("Máximo de 50 textos por lote")
        
        cleaned_texts = []
        for i, text in enumerate(v):
            if not text or not text.strip():
                raise ValueError(f"Texto {i+1} está vazio")
            
            cleaned = text.strip()
            if len(cleaned) > 2000:
                raise ValueError(f"Texto {i+1} excede 2000 caracteres")
            
            cleaned_texts.append(cleaned)
        
        return cleaned_texts
    
    model_config = {
        "str_strip_whitespace": True,
        "validate_assignment": True,
        "extra": "forbid"
    }


class SentimentScore(BaseModel):
    """Score individual de sentimento."""
    
    label: Literal["positive", "negative", "neutral"]
    score: Annotated[
        float,
        Field(
            ge=0.0,
            le=1.0,
            description="Confiança do modelo (0.0 a 1.0)"
        )
    ]


class AnalysisResponse(BaseModel):
    """Response padrão para análise de sentimento."""
    
    id: Annotated[
        str,
        Field(description="ID único da análise")
    ] = Field(default_factory=lambda: str(uuid.uuid4()))
    
    text: Annotated[
        Optional[str],
        Field(description="Texto analisado (opcional por privacidade)")
    ] = None
    
    sentiment: Literal["positive", "negative", "neutral"] = Field(
        description="Sentimento identificado"
    )
    
    confidence: Annotated[
        float,
        Field(
            ge=0.0,
            le=1.0,
            description="Confiança do modelo"
        )
    ]
    
    language: Annotated[
        str,
        Field(
            min_length=2,
            max_length=5,
            description="Código ISO do idioma detectado"
        )
    ]
    
    all_scores: List[SentimentScore] = Field(
        default_factory=list,
        description="Scores detalhados de todos os sentimentos"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp da análise"
    )
    
    processing_time_ms: Annotated[
        Optional[float],
        Field(
            ge=0.0,
            description="Tempo de processamento em milissegundos"
        )
    ] = None
    
    cached: bool = Field(
        default=False,
        description="Se o resultado foi obtido do cache"
    )
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        },
        "extra": "forbid"
    }


class BatchResponse(BaseModel):
    """Response para análise em lote."""
    
    results: List[AnalysisResponse] = Field(
        description="Lista de resultados de análise"
    )
    
    total_processed: Annotated[
        int,
        Field(
            ge=0,
            description="Total de textos processados"
        )
    ]
    
    processing_time_ms: Annotated[
        Optional[float],
        Field(
            ge=0.0,
            description="Tempo total de processamento"
        )
    ] = None
    
    @model_validator(mode="after")
    def validate_consistency(self) -> "BatchResponse":
        """Valida consistência entre resultados e contadores."""
        if len(self.results) != self.total_processed:
            raise ValueError("Inconsistência entre resultados e contador")
        return self
    
    model_config = {
        "extra": "forbid"
    }


class HealthResponse(BaseModel):
    """Response para verificação de saúde."""
    
    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    services: Dict[str, Any] = Field(
        default_factory=dict,
        description="Status dos serviços"
    )
    
    model_info: Dict[str, Any] = Field(
        default_factory=dict,
        description="Informações do modelo ML"
    )
    
    version: str = Field(default="1.0.0")
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        },
        "extra": "allow"  # Permite campos adicionais para flexibilidade
    }


class ErrorDetail(BaseModel):
    """Detalhes de erro padronizado."""
    
    field: Optional[str] = Field(
        default=None,
        description="Campo que causou o erro"
    )
    
    message: str = Field(
        description="Mensagem de erro"
    )
    
    code: Optional[str] = Field(
        default=None,
        description="Código do erro"
    )


class ErrorResponse(BaseModel):
    """Response padronizada para erros."""
    
    error: str = Field(
        description="Tipo do erro"
    )
    
    message: str = Field(
        description="Mensagem descritiva do erro"
    )
    
    details: List[ErrorDetail] = Field(
        default_factory=list,
        description="Detalhes específicos do erro"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp do erro"
    )
    
    request_id: Optional[str] = Field(
        default=None,
        description="ID da requisição para rastreamento"
    )
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        },
        "extra": "forbid"
    }


# Aliases para compatibilidade e conveniência
SentimentRequest = AnalysisRequest
SentimentResponse = AnalysisResponse
BatchSentimentRequest = BatchRequest
BatchSentimentResponse = BatchResponse