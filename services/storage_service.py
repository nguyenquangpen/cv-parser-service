from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from typing import List, Type
from database import models
from . import ai_service
import json

# wwork with database, call AI model here

async def save_file_to_db(db: Session, file: UploadFile, model_class: Type[models.Base]):
    content = await file.read()
    db_file = model_class(filename=file.filename, content=content)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def get_all_files(db: Session, model_class: Type[models.Base]):
    return db.query(model_class).order_by(model_class.upload_time.desc()).all()

def delete_file_from_db(db: Session, file_id: int, model_class: Type[models.Base]):
    db_file = db.query(model_class).filter(model_class.id == file_id).first()
    if db_file:
        db.delete(db_file)
        db.commit()
        return True
    return False

def process_matching(db: Session, resume_ids: List[int], jd_id: int):
    jd_record = db.query(models.JobDescription).filter(models.JobDescription.id == jd_id).first()
    if not jd_record:
        raise HTTPException(status_code=404, detail=f"JD với ID {jd_id} không tồn tại.")
    
    resumes = db.query(models.Resume).filter(models.Resume.id.in_(resume_ids)).all()

    print("\n" + "="*20 + " BẮT ĐẦU QUÁ TRÌNH KHỚP " + "="*20)
    print(f"1. Phân tích JD: '{jd_record.filename}'")

    jd_text = ai_service.extract_text_from_content(jd_record.content, jd_record.filename)
    jd_skills_data = ai_service.extract_skills_from_text(jd_text)
    required_skills = set(jd_skills_data.get("skills", []))
    print(f"   -> Yêu cầu {len(required_skills)} kỹ năng.")

    match_results = []
    for resume in resumes:
        print(f"\n--- 2. Đang xử lý CV: '{resume.filename}' ---")

        resume_text = ai_service.extract_text_from_content(resume.content, resume.filename)
        extracted_skills_data = ai_service.extract_skills_from_text(resume_text)

        candidate_info = ai_service.extract_candidate_info(resume_text)
        candidate_skills = set(extracted_skills_data.get("skills", []))

        match_score = ai_service.caculate_match_score(jd_text, resume_text)
        match_results.append({
            "resume_id": resume.id,
            "filename": resume.filename,
            "candidate_info": candidate_info,
            "candidate_skills": list(candidate_skills),
            "match_score": match_score
        })

    print("finished processing all resumes.")

    return match_results