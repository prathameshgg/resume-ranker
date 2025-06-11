from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from enum import Enum

class SeniorityLevel(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced" 
    EXPERT = "Expert"

class SkillWithSeniority(BaseModel):
    name: str
    seniority: SeniorityLevel = SeniorityLevel.BEGINNER

class Education(BaseModel):
    degree: str
    institution: str
    graduation_year: int
    gpa: Optional[float] = None
    field_of_study: Optional[str] = None

class Experience(BaseModel):
    title: str
    company: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: List[str] = []
    skills_used: List[str]

class ResumeData(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str]
    skills_with_seniority: List[SkillWithSeniority] = []
    experience: List[Experience]
    education: List[Education]
    certifications: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    github: Optional[str] = None
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None