from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging
import time
from config import settings
from services import storage_service
from . import schemas
from database import models
from .dependencies import get_db
from api.schemas import GenerateJdRequest, GenerateJdResponse
from services.ai_service import ai_service_instance

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_FILE_TYPES = settings.ALLOWED_FILE_TYPES

# ================== Resume Endpoints ==================
@router.post("/resumes/upload/", response_model=List[schemas.Resume],status_code=status.HTTP_201_CREATED)
async def upload_resumes(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{file.content_type}' not allowed"
        )
    result = await storage_service.save_file_to_db(db, file=file, model_class=models.Resume)
    return [result]

@router.get("/resumes/", response_model=List[schemas.Resume])
def list_resumes(db: Session = Depends(get_db)):
    result = storage_service.get_all_files(db, model_class=models.Resume)
    return result

@router.delete("/resumes/{resume_id}/delete/", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    if not storage_service.delete_file_from_db(db, file_id=resume_id, model_class=models.Resume):
        raise HTTPException(status_code=404, detail="CV không tồn tại")
    return {"ok": True}

# ================== Job Description Endpoints ==================
@router.post("/jobdescriptions/upload/", response_model=schemas.JobDescription)
async def upload_job_description(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{file.content_type}' not allowed"
        )
    return await storage_service.save_file_to_db(db, file=file, model_class=models.JobDescription)

@router.get("/jobdescriptions/", response_model=List[schemas.JobDescription])
def list_job_descriptions(db: Session = Depends(get_db)):
    return storage_service.get_all_files(db, model_class=models.JobDescription)

@router.delete("/jobdescriptions/{jd_id}/delete/", status_code=status.HTTP_204_NO_CONTENT)
def delete_job_description(jd_id: int, db: Session = Depends(get_db)):
    if not storage_service.delete_file_from_db(db, file_id=jd_id, model_class=models.JobDescription):
        raise HTTPException(status_code=404, detail="JD không tồn tại")
    return {"ok": True}

@router.post("/process-with-ai/", response_model=schemas.ProcessAIResponse)
def process_with_ai(request_data: schemas.ProcessAIRequest, db: Session = Depends(get_db)):
    # Giả sử logic frontend chỉ gửi 1 JD
    if not request_data.job_description_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "needs at least one Job Description ID.")
    
    if not request_data.resume_ids:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "needs at least one Resume ID.")

    results = storage_service.process_matching(
        db, 
        resume_ids=request_data.resume_ids, 
        jd_id=request_data.job_description_id
    )

    return {"status": "success", "message": "Xử lý thành công.", "results": results}

@router.post(
    "/generate-jd-from-llm/",
    response_model=GenerateJdResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Job Description using LLM"
)
async def generate_jd_from_llm_route(request_body: GenerateJdRequest):
    """
    Endpoint để tạo mô tả công việc (JD) bằng cách sử dụng mô hình ngôn ngữ lớn (LLM) của Google Gemini.

    - **prompt_content**: Nội dung ban đầu cung cấp cho LLM để tạo JD.
    """
    logger.info(f"API route received generate JD request with prompt: {request_body.prompt_content[:100]}...")

    if not request_body.prompt_content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nội dung prompt không được để trống."
        )

    try:
        generated_jd_text = ai_service_instance.generate_job_description(request_body.prompt_content)

        if not generated_jd_text:
            logger.warning("AI service returned empty generated JD.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI không thể tạo ra mô tả công việc."
            )

        logger.info("Successfully generated JD via API route.")
        return GenerateJdResponse(generated_jd=generated_jd_text)

    except ValueError as e:
        logger.error(f"ValueError in generate_jd_from_llm_route: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except RuntimeError as e: 
        logger.error(f"RuntimeError in generate_jd_from_llm_route: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi hệ thống AI: {e}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in generate_jd_from_llm_route: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Đã xảy ra lỗi không mong muốn: {e}"
        )