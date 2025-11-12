from sqlalchemy import Column, Integer, String, DateTime, LargeBinary, func
from .database import Base

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    content = Column(LargeBinary) 
    upload_time = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="uploaded")

class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True) 
    content = Column(LargeBinary) 
    upload_time = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="uploaded")
    