from fastapi import FastAPI
import logging # Import module logging
from api import routes
from services.ai_service import AIService 

from database import models, database

models.Base.metadata.create_all(bind=database.engine)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("cv_ai_server_main")


app = FastAPI(title="CV Parser AI Server (LLM Only)") 

app.include_router(routes.router, prefix="/api")

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the CV Parser AI Server!"}

@app.get("/health", tags=["Monitoring"])
def health_check():
    """Kiểm tra trạng thái hoạt động của server AI."""
    return {"status": "ok", "message": "CV Parser AI server is running and LLM is ready."}

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the CV Parser AI Server (LLM Only)!"}

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up CV Parser AI Server...")
    try:
        AIService()
        logger.info("AI Service initialized successfully and LLM model loaded.")
    except Exception as e:
        logger.critical(f"Failed to initialize AI Service: {e}", exc_info=True)
        raise Exception(f"CRITICAL: AI Service failed to start. {e}")