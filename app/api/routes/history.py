from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Path
from sqlalchemy.orm import Session
from datetime import date, datetime

from app.core.database import get_db
from app.core.schemas import (
    HistoryResponse, 
    HistoryItem, 
    StatsResponse, 
    SentimentDistribution,
    LanguageDistribution,
    TimeframeStats
)
from app.services.storage import StorageService

router = APIRouter(prefix="/api/v1", tags=["history"])

@router.get("/history", response_model=HistoryResponse)
async def get_history(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    language: Optional[str] = Query(None, description="Filter by language"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment (positive, negative, neutral)"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
):
    """
    Retrieve history of sentiment analyses with optional filters and pagination.
    """
    storage_service = StorageService(db)
    try:
        # Calcular o valor de "skip" com base na página e limite
        skip = (page - 1) * limit
        
        # Obter histórico e total
        analyses, total = await storage_service.get_analysis_history(
            db,
            skip=skip,
            limit=limit,
            language=language,
            sentiment=sentiment,
            start_date=start_date,
            end_date=end_date
        )
        
        # Converter objetos Analysis para HistoryItem
        items = [
            HistoryItem(
                id=str(analysis.id),
                timestamp=analysis.timestamp,
                text=analysis.text,
                sentiment=analysis.sentiment_label
            ) for analysis in analyses
        ]
        
        # Retornar objeto HistoryResponse
        return HistoryResponse(
            total=total,
            page=page,
            limit=limit,
            items=items
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")

@router.get("/history/{analysis_id}", response_model=dict)
async def get_analysis_by_id(
    analysis_id: str = Path(..., description="The ID of the analysis to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific analysis by its ID.
    """
    storage_service = StorageService(db)
    analysis = await storage_service.get_analysis_by_id(db, int(analysis_id))
    
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Analysis with ID {analysis_id} not found")
    
    # Converter para dict para retornar
    return {
        "id": str(analysis.id),
        "timestamp": analysis.timestamp,
        "text": analysis.text,
        "language": analysis.language,
        "sentiment_label": analysis.sentiment_label,
        "sentiment_score": analysis.sentiment_score,
        "sentiment_confidence": analysis.sentiment_confidence,
        "emotions": analysis.emotions,
        "entities": analysis.entities,
        "keywords": analysis.keywords,
        "processing_time_ms": analysis.processing_time_ms
    }

@router.delete("/history/{analysis_id}", status_code=204)
async def delete_analysis(
    analysis_id: str = Path(..., description="The ID of the analysis to delete"),
    db: Session = Depends(get_db)
):
    """
    Delete a specific analysis by its ID.
    """
    storage_service = StorageService(db)
    deleted = await storage_service.delete_analysis(db, int(analysis_id))
    
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Analysis with ID {analysis_id} not found")
    
    return {"status": "deleted"}

@router.get("/stats", response_model=StatsResponse)
async def get_api_stats(
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None, description="Start date for stats"),
    end_date: Optional[date] = Query(None, description="End date for stats")
):
    """
    Retrieve API usage statistics.
    """
    storage_service = StorageService(db)
    
    try:
        # Obter estatísticas da API
        api_stats = await storage_service.get_stats(db)
        
        # Obter distribuição de sentimentos
        sentiment_dist_dict = await storage_service.get_sentiment_distribution(db)
        sentiment_distribution = SentimentDistribution(
            positive=sentiment_dist_dict.get("positive", 0),
            negative=sentiment_dist_dict.get("negative", 0),
            neutral=sentiment_dist_dict.get("neutral", 0)
        )
        
        # Obter distribuição de idiomas
        language_dist = await storage_service.get_language_distribution(db)
        language_distribution = LanguageDistribution(
            entries=language_dist
        )
        
        # Como não temos implementação para timeframe_stats, vamos criar um item de exemplo
        timeframe_stats = [
            TimeframeStats(
                date=datetime.utcnow(),
                requests_count=api_stats.requests_count,
                avg_response_time_ms=api_stats.avg_response_time
            )
        ]
        
        # Retornar objeto StatsResponse
        return StatsResponse(
            total_analyses=api_stats.requests_count,
            sentiment_distribution=sentiment_distribution,
            language_distribution=language_distribution,
            timeframe_stats=timeframe_stats,
            last_updated=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve statistics: {str(e)}")