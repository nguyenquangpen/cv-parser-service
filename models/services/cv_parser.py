# contain the service logic for CV parsing

import os
import io 
import pickle
import logging
import random
from fastapi import HTTPException
from docx import Document
from pdfminer.high_level import extract_text as pdf_extract_text

from models.api.schemas import ..

logger = logging.getLogger(__name__)

# ??? take 2 model
def getModelPath():
        current_dir = os.path.dirname(os.path.abspath(__name__))
        model_path = os.path.join(current_dir, "models", "output")
        return os.listdir(model_path)

MODEL_PATH = os.path.join("/app", "models", "output", "cv_model.pkl")

class CVParserService:
    def __init__(self, model=None):
        self.model = model
    if model is None:
        logger.warning("No model provided, loading default model.")
    logger.info("CVParserService initialized.")

    async def load_model(self):
        # this function should only be called once when the server starts
        if self.model is None:
            if os.path.exists(MODEL_PATH):
                try:
                    with open(MODEL_PATH, "rb") as f:
                        self.model = pickle.load(f)
                    return self.model
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Error loading model: {e}")
            else:
                raise HTTPException(status_code=400, detail="Model already loaded.")
        return self.model

    async def extract_text_from_cv_file(self, file_content: bytes, filename: str) -> str:
        # Extract text from uploaded CV file (PDF, DOCX, TXT)
        if filename.lower().endswith(".pdf"):
            if pdf_extract_text is None:
                raise HTTPException(status_code=500, detail="PDF extraction library not available.")
            try:
                text = pdf_extract_text(io.BytesIO(file_content))
                return text
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error extracting text from PDF: {e}")
        elif filename.lower().endswith(".docx"):
            if Document is None:
                raise HTTPException(status_code=500, detail="DOCX extraction library not available.")
            try:
                doc = Document(io.BytesIO(file_content))
                text = "\n".join([para.text for para in doc.paragraphs])
                return text
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error extracting text from DOCX: {e}")
        elif filename.lower().endswith(".txt"):
            try:
                text = file_content.decode("utf-8", errors="ignore")
                return text
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error decoding TXT file: {e}")
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload PDF, DOCX, or TXT files.")
    

    # less other funtions which caculate score
    async def run_model_prediction(self, cv_text: str) -> CVtextOutput:
        if self.model is None:
            raise HTTPException(status_code=500, detail="Model not loaded.")
        
        logger.info("Running model prediction.")
        try:
            #... 
            #...
            prediction_result = self.model.predict([cv_text])
        
