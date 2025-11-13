from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
# dataset backend send
class FileResponse(BaseModel):
    id: int
    filename: str
    upload_time: datetime
    status: str

    class Config:
        from_attributes = True

class Resume(FileResponse):
    id: int
    filename: str
    upload_time: datetime
    status: str

class JobDescription(FileResponse):
    id: int
    filename: str
    upload_time: datetime
    status: str

class ProcessAIRequest(BaseModel):
    resume_ids: List[int]
    job_description_id: int

class ProcessAIResponse(BaseModel):
    status: str
    message: str
    results: Optional[List[dict]] = None

class GenerateJdRequest(BaseModel):
    prompt_content: str

class GenerateJdResponse(BaseModel):
    generated_jd: str