from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import uvicorn
from datetime import datetime

from app.api.routes import sentiment, history
from app.core.database import engine, create_tables, get_db
from app.services.analyzer import SentimentAnalyzer
from app.services.storage import StorageService
import app.config as config

# Create tables
create_tables()

# Initialize FastAPI app
app = FastAPI(
    title="Sentiment Analysis API",
    description="API for analyzing sentiment in text using natural language processing techniques",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware for request timing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Include routers
app.include_router(sentiment.router)
app.include_router(history.router)

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to the Sentiment Analysis API",
        "documentation": "/docs",
        "version": app.version,
    }

# Health check endpoint
@app.get("/api/v1/health", tags=["Health"], operation_id="check_api_health")
async def health_check(db=Depends(get_db)):
    # Check if analyzer service can be initialized
    try:
        analyzer = SentimentAnalyzer()
        models_loaded = True
    except Exception:
        models_loaded = False

    # Check database connection
    db_connected = True
    try:
        # Try a simple query to check database connection
        StorageService(db).get_total_analyses_count()
    except Exception:
        db_connected = False

    # Get uptime
    start_time = config.APP_START_TIME
    uptime_seconds = (datetime.now() - start_time).total_seconds()
    
    health_data = {
        "status": "healthy" if (models_loaded and db_connected) else "degraded",
        "version": app.version,
        "uptime_seconds": uptime_seconds,
        "database_connected": db_connected,
        "models_loaded": models_loaded,
        "timestamp": datetime.now().isoformat()
    }
    
    status_code = 200 if health_data["status"] == "healthy" else 503
    return JSONResponse(content=health_data, status_code=status_code)

# Run the application if executed directly
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        workers=config.WORKERS
    )