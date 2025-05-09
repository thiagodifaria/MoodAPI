from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import List, Optional, Union
from uuid import UUID
import time
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.schemas import (
    BasicAnalysisRequest,
    DetailedAnalysisRequest,
    BatchAnalysisRequest,
    BasicAnalysisResponse,
    DetailedAnalysisResponse,
    HealthResponse,
    SentimentResult
)
from app.core.database import get_db
from app.services.analyzer import SentimentAnalyzer
from app.services.storage import StorageService


router = APIRouter(prefix="/api/v1", tags=["sentiment"])

# Initialize services
analyzer = SentimentAnalyzer()
storage_service = StorageService()


@router.post("/analyze/basic", response_model=BasicAnalysisResponse)
async def analyze_basic_sentiment(
    request: BasicAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Analyze the sentiment of a text and return a basic classification.
    
    Returns:
        BasicAnalysisResponse: The sentiment analysis result with basic classification.
    """
    start_time = time.time()
    
    try:
        # Detect language if not provided
        if not request.language:
            request.language = analyzer.detect_language(request.text)
        
        # Analyze sentiment
        result = analyzer.analyze_basic(request.text, request.language)
        
        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)
        
        # Extrair o objeto sentiment do resultado
        sentiment_data = result["sentiment"]
        sentiment_obj = SentimentResult(
            label=sentiment_data["label"],
            score=sentiment_data["score"],
            confidence=sentiment_data["confidence"]
        )
        
        # Create response
        response = BasicAnalysisResponse(
            id=result["id"],
            timestamp=datetime.fromisoformat(result["timestamp"]),
            text=request.text,
            language=result["language"],
            sentiment=sentiment_obj,
            processing_time_ms=processing_time
        )
        
        # Store the analysis in background
        background_tasks.add_task(
            storage_service.store_analysis,
            db=db,
            analysis_data=response.dict(),
            analysis_type="basic"
        )
        
        return response
    
    except Exception as e:
        # Log the error
        print(f"Error in basic sentiment analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze/detailed", response_model=DetailedAnalysisResponse)
async def analyze_detailed_sentiment(
    request: DetailedAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Analyze the sentiment of a text and return a detailed classification
    with emotions, entities, and keywords.
    
    Returns:
        DetailedAnalysisResponse: The detailed sentiment analysis result.
    """
    start_time = time.time()
    
    try:
        # Detect language if not provided
        if not request.language:
            request.language = analyzer.detect_language(request.text)
        
        # Analyze sentiment with detailed analysis
        result = analyzer.analyze_detailed(request.text, request.language)
        
        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)
        
        # Extrair o objeto sentiment do resultado
        sentiment_data = result["sentiment"]
        sentiment_obj = SentimentResult(
            label=sentiment_data["label"],
            score=sentiment_data["score"],
            confidence=sentiment_data["confidence"]
        )
        
        # Create response
        response = DetailedAnalysisResponse(
            id=result["id"],
            timestamp=datetime.fromisoformat(result["timestamp"]),
            text=request.text,
            language=result["language"],
            sentiment=sentiment_obj,
            emotions=result.get("emotions"),
            entities=result.get("entities"),
            keywords=result.get("keywords"),
            processing_time_ms=processing_time
        )
        
        # Store the analysis in background
        background_tasks.add_task(
            storage_service.store_analysis,
            db=db,
            analysis_data=response.dict(),
            analysis_type="detailed"
        )
        
        return response
    
    except Exception as e:
        # Log the error
        print(f"Error in detailed sentiment analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/analyze/batch", response_model=List[Union[BasicAnalysisResponse, DetailedAnalysisResponse]])
async def analyze_batch(
    request: BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Process multiple texts in a single request.
    
    Returns:
        List[Union[BasicAnalysisResponse, DetailedAnalysisResponse]]: A list of analysis results.
    """
    if not request.texts:
        raise HTTPException(status_code=400, detail="No texts provided for analysis")
    
    if len(request.texts) > 100:  # Limit batch size
        raise HTTPException(status_code=400, detail="Maximum batch size is 100 texts")
    
    results = []
    
    for text in request.texts:
        start_time = time.time()
        
        try:
            # Create a single text request
            single_request = BasicAnalysisRequest(text=text, language=request.language)
            
            # Process according to requested analysis type
            if request.analysis_type == "basic":
                # Use the basic analysis logic
                if not single_request.language:
                    single_request.language = analyzer.detect_language(text)
                
                result = analyzer.analyze_basic(text, single_request.language)
                
                # Calculate processing time
                processing_time = int((time.time() - start_time) * 1000)
                
                # Extrair o objeto sentiment do resultado
                sentiment_data = result["sentiment"]
                sentiment_obj = SentimentResult(
                    label=sentiment_data["label"],
                    score=sentiment_data["score"],
                    confidence=sentiment_data["confidence"]
                )
                
                # Create response
                response = BasicAnalysisResponse(
                    id=result["id"],
                    timestamp=datetime.fromisoformat(result["timestamp"]),
                    text=text,
                    language=result["language"],
                    sentiment=sentiment_obj,
                    processing_time_ms=processing_time
                )
            else:  # detailed
                # Use the detailed analysis logic
                if not single_request.language:
                    single_request.language = analyzer.detect_language(text)
                
                result = analyzer.analyze_detailed(text, single_request.language)
                
                # Calculate processing time
                processing_time = int((time.time() - start_time) * 1000)
                
                # Extrair o objeto sentiment do resultado
                sentiment_data = result["sentiment"]
                sentiment_obj = SentimentResult(
                    label=sentiment_data["label"],
                    score=sentiment_data["score"],
                    confidence=sentiment_data["confidence"]
                )
                
                # Create response
                response = DetailedAnalysisResponse(
                    id=result["id"],
                    timestamp=datetime.fromisoformat(result["timestamp"]),
                    text=text,
                    language=result["language"],
                    sentiment=sentiment_obj,
                    emotions=result.get("emotions"),
                    entities=result.get("entities"),
                    keywords=result.get("keywords"),
                    processing_time_ms=processing_time
                )
            
            # Store the analysis in background
            background_tasks.add_task(
                storage_service.store_analysis,
                db=db,
                analysis_data=response.dict(),
                analysis_type=request.analysis_type
            )
            
            results.append(response)
            
        except Exception as e:
            # Log the error but continue with other texts
            print(f"Error processing text in batch: {str(e)}")
            # Add a placeholder for failed analysis
            results.append({
                "text": text[:50] + "..." if len(text) > 50 else text,
                "error": f"Analysis failed: {str(e)}"
            })
    
    return results


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Check the health status of the API.
    
    Returns:
        HealthResponse: The health status of the API.
    """
    start_time = time.time()
    
    # Check database connection
    db_connection = True
    try:
        # Simple query to check database connection
        db.execute("SELECT 1").fetchone()
    except Exception:
        db_connection = False
    
    # Check if NLP models are loaded
    nlp_models_loaded = analyzer.check_models_loaded()
    
    # Calculate uptime (in a real system, you'd track the actual start time)
    uptime = time.time() - start_time  # This is just a placeholder
    
    return HealthResponse(
        status="operational" if db_connection and nlp_models_loaded else "degraded",
        version="0.1.0",  # This would come from your config in a real system
        uptime=uptime,
        database_connection=db_connection,
        nlp_models_loaded=nlp_models_loaded
    )