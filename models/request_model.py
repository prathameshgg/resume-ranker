from pydantic import BaseModel
from models.response_model import ResumeData
from models.job_model import JobRequirement
from typing import List

class AnalyzeResumeRequest(BaseModel):
    resume_data: ResumeData
    job_requirement: JobRequirement

class BatchAnalyzeRequest(BaseModel):
    resumes: List[ResumeData]
    job_requirement: JobRequirement 