from fastapi import APIRouter, FastAPI, HTTPException, status
import uvicorn
import os
import logging
import asyncio
import time

# from models.api import routes_resume 
# from models.api import routes_jd     
from models.api.routes_matching import matching_router as matching_routes
from models.schemas.processing_payload import (
    ProcessingPayload,
    MatchingResult,
    OverallProcessingResponse
)
from models.services import matchingProcess
from config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CV AI Processing Service",
    description="API for processing CVs and Job Descriptions using AI.",
    version="1.0.0",
)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up AI service...")
    try:
        matchingProcess.load_doc2vec_model()
    except RuntimeError as e:
        logger.critical(f"FATAL: AI model failed to load during startup. {e}")
        raise 

# app.include_router(routes_resume)
# app.include_router(routes_jd)
app.include_router(matching_routes)

@app.get("/health/", status_code=status.HTTP_200_OK)
async def health_check():
    if matchingProcess._doc2vec_model is None:
        return {"status": "AI service is running, but model not loaded"}, status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "AI service is running and healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 