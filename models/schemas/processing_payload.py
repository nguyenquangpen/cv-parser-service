from pydantic import BaseModel
from typing import List, Optional

# dataset backend send
class ProcessingPayload(BaseModel):
    resume_ids: List[str]
    job_ids: List[str]

class ProcessingResult(BaseModel):
    id: str
    status: str
    message: Optional[str] = None

class JDProcessingResult(BaseModel):
    id: str
    status: str
    message: Optional[str] = None

class MatchingResult(BaseModel):
    resume_id: str
    job_description_id: str
    score: float
    status: str = "completed"
    message: Optional[str] = None

class OverallProcessingResponse(BaseModel):
    message: str
    matching_results: List[MatchingResult]
    status_code: int = 200