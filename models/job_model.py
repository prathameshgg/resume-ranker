from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class JobRequirement(BaseModel):
    title: str
    required_skills: List[str]
    preferred_skills: List[str]
    experience_years: float
    education_level: str
    industry: str
    location: Optional[str] = None
    keywords: List[str]
    required_certifications: Optional[List[str]] = None  # New field for required certifications
    company_values: Optional[List[str]] = None  # New field for company values/culture

class SkillFitment(BaseModel):
    skill_name: str
    proficiency_level: float  # 0-1 score based on experience and usage
    relevance_score: float    # How relevant this skill is to current job market

class CareerPathSuggestion(BaseModel):
    role_title: str
    fitment_score: float
    required_skills_match: float
    market_demand: float      # Score indicating job market demand
    growth_potential: float   # Score indicating career growth potential
    skill_gap: List[str]     # Skills needed to improve fitment
    next_steps: List[str]    # Recommended actions to improve candidacy

# New model for skill gaps in career trajectory forecasting
class SkillGapForecast(BaseModel):
    skills_needed: List[str]
    priority_level: str  # "High", "Medium", "Low"
    timeframe: str       # When this skill should be acquired (e.g., "Year 1")
    relevance_score: float
    learning_resources: Optional[List[str]] = None

# New model for individual career trajectory prediction
class TrajectoryPrediction(BaseModel):
    timepoint: str      # e.g., "Year 1", "Year 2", "Year 3"
    predicted_role: str
    confidence_score: float
    alternative_roles: List[str]
    skill_gaps: List[SkillGapForecast]
    salary_range: Optional[Dict[str, float]] = None
    market_demand_score: float

# New model for overall career forecast
class CareerForecast(BaseModel):
    forecast_timeline: List[TrajectoryPrediction]
    baseline_accuracy: float  # How accurate the baseline heuristic model is
    ml_model_accuracy: float  # How accurate the ML model is
    model_type: str          # "LSTM", "Transformer", etc.
    top_skills_to_acquire: List[str]
    industry_alignment_score: float

class JobMatch(BaseModel):
    job_title: str
    match_score: float
    matching_skills: List[str]
    missing_skills: List[str]
    experience_match: float
    education_match: bool
    suggested_roles: List[str]
    match_details: Dict[str, Any]
    
    # New fields for enhanced fitment analysis
    overall_fitment_score: float
    skill_fitment: List[SkillFitment]
    career_path_suggestions: List[CareerPathSuggestion]
    market_alignment_score: float  # How well the candidate's profile aligns with market trends
    strength_areas: List[str]      # Candidate's strongest skills/areas
    growth_opportunities: List[str] # Areas where candidate can improve
    best_matched_roles: List[CareerPathSuggestion]  # Top 3 roles the candidate is best suited for
    certification_match_score: Optional[float] = None  # New field for certification match score
    matching_certifications: Optional[List[str]] = None  # New field for matching certifications
    missing_certifications: Optional[List[str]] = None  # New field for missing certifications
    
    # New Cultural Fit fields
    cultural_fit_score: Optional[float] = None  # Score from 0 to 1 indicating cultural fit
    cultural_fit_details: Optional[Dict[str, Any]] = None  # Details about the cultural fit match
    company_values: Optional[List[str]] = None  # Company values used for assessment
    
    # New Career Progression Analysis fields
    career_progression: Optional[Dict[str, Any]] = None  # Details about career progression analysis
    promotion_trajectory: Optional[List[Dict[str, Any]]] = None  # List of career movements showing progression
    job_switch_frequency: Optional[Dict[str, Any]] = None  # Info about job switching patterns
    employment_gaps: Optional[List[Dict[str, Any]]] = None  # Information about gaps in employment 
    
    # New Career Trajectory Forecasting field
    career_forecast: Optional[CareerForecast] = None  # ML-based career trajectory prediction 