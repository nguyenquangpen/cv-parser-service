from pydantic import BaseModel, Field

class CVtextInput(BaseModel):
    cv_text: str = Field(..., description="The text content of the CV")

class CVtextOutput(BaseModel):
    name: str = Field(..., description="Extracted name from the CV")
    email: str = Field(..., description="Extracted email from the CV")
    phone: str = Field(..., description="Extracted phone number from the CV")
    skills: list[str] = Field(..., description="List of extracted skills from the CV")

class CVscoreInput(BaseModel):
    cv_text: str = Field(..., description="The text content of the CV")
    job_description: str = Field(..., description="The job description to match against")

class CVscoreOutput(BaseModel):
    score: float = Field(..., description="Matching score between CV and job description")
    