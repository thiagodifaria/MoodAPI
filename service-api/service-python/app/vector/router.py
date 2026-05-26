from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.sentiment.models import SentimentAnalysis
from app.vector.service import VectorDocument, VectorSearchService, get_vector_service

router = APIRouter(prefix="/api/v1/vector", tags=["vector-search"])


class SemanticSearchRequest(BaseModel):
    text: Annotated[str, Field(min_length=2, max_length=2000)]
    limit: Annotated[int, Field(ge=1, le=50)] = 10

    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)


@router.get("/health")
async def vector_health(
    service: VectorSearchService = Depends(get_vector_service),
) -> dict:
    return await service.health()


@router.post("/search")
async def semantic_search(
    request: SemanticSearchRequest,
    service: VectorSearchService = Depends(get_vector_service),
    db: Session = Depends(get_db_session),
) -> dict:
    health = await service.health()
    if health["status"] != "healthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector DB indisponivel ou desabilitado",
        )

    if await service.count() == 0:
        records = db.query(SentimentAnalysis).order_by(SentimentAnalysis.created_at.desc()).limit(200).all()
        documents = [
            VectorDocument(
                id=str(record.id),
                text=record.text,
                sentiment=record.sentiment,
                confidence=record.confidence,
                language=record.language,
                metadata={
                    "model_name": record.model_name,
                    "model_version": record.model_version,
                },
            )
            for record in records
        ]
        await service.upsert_many(documents)

    results = await service.search(request.text, limit=request.limit)
    return {"query": request.text, "results": results}


@router.get("/search")
async def semantic_search_get(
    text: Annotated[str, Query(min_length=2, max_length=2000)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    service: VectorSearchService = Depends(get_vector_service),
    db: Session = Depends(get_db_session),
) -> dict:
    return await semantic_search(SemanticSearchRequest(text=text, limit=limit), service, db)
