import spacy
import re
from datetime import datetime
from models.response_model import ResumeData, Education, Experience, SkillWithSeniority, SeniorityLevel
from typing import List, Dict, Any, Tuple
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResumeParser:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        
    def _extract_name(self, text: str) -> str:
        """Extract name from resume text."""
        doc = self.nlp(text[:1000])  # Look at first 1000 chars for name
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                return ent.text
        # Fallback: take first line if no name entity found
        return text.split('\n')[0].strip()
    
    def _extract_email(self, text: str) -> str:
        """Extract email from resume text."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else ""
    
    def _extract_phone(self, text: str) -> str:
        """Extract phone number from resume text."""
        phone_pattern = r'\b(?:\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b'
        match = re.search(phone_pattern, text)
        return match.group(0) if match else ""
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text."""
        # Common technical skills to look for
        common_skills = [
            "python", "java", "javascript", "html", "css", "sql", "react", "angular", 
            "vue", "node.js", "django", "flask", "spring", "docker", "kubernetes", 
            "aws", "azure", "gcp", "machine learning", "data science", "ai", 
            "devops", "ci/cd", "git", "agile", "scrum", "rest api", "graphql"
        ]
        
        skills = []
        text_lower = text.lower()
        
        for skill in common_skills:
            if skill in text_lower:
                skills.append(skill)
        
        return skills
    
    def _analyze_skill_seniority(self, skill: str, text: str, experience: List[Experience]) -> SeniorityLevel:
        """
        Analyze the seniority level of a skill based on context, frequency, and depth of detail.
        
        Factors considered:
        1. Skill frequency in resume
        2. Context of skill usage (leading, implementing, using)
        3. Years of experience using the skill
        4. Complexity of projects described
        """
        skill_lower = skill.lower()
        text_lower = text.lower()
        
        # Count skill mentions
        skill_count = text_lower.count(skill_lower)
        
        # Check for years of experience with the skill
        years_with_skill = 0
        for exp in experience:
            if skill in exp.skills_used:
                # Estimate duration based on experience
                if exp.start_date and exp.end_date:
                    delta = exp.end_date - exp.start_date
                    years_with_skill += delta.days / 365.25
                else:
                    # Default: add 1 year if dates unavailable
                    years_with_skill += 1
        
        # Check for leadership indicators
        leadership_terms = [
            f"led {skill_lower}", f"leading {skill_lower}", 
            f"architect", f"designed {skill_lower}", 
            f"mentored", f"trained", f"supervised"
        ]
        
        leadership_score = sum(1 for term in leadership_terms if term in text_lower)
        
        # Check for implementation indicators
        implementation_terms = [
            f"implemented {skill_lower}", f"developed {skill_lower}",
            f"built {skill_lower}", f"created {skill_lower}",
            f"optimized {skill_lower}", f"improved {skill_lower}"
        ]
        
        implementation_score = sum(1 for term in implementation_terms if term in text_lower)
        
        # Check for advanced usage indicators
        advanced_terms = [
            "advanced", "expert", "proficient", "specialized", 
            "optimized", "complex", "architecture"
        ]
        
        advanced_score = sum(1 for term in advanced_terms if term in text_lower)
        
        # Combine factors to determine seniority
        total_score = skill_count * 0.1 + leadership_score * 2 + implementation_score + advanced_score * 1.5
        
        # Adjust score based on years with skill
        if years_with_skill > 5:
            total_score += 5
        elif years_with_skill > 3:
            total_score += 3
        elif years_with_skill > 1:
            total_score += 1
        
        # Determine seniority level based on score
        if total_score >= 8:
            return SeniorityLevel.EXPERT
        elif total_score >= 5:
            return SeniorityLevel.ADVANCED
        elif total_score >= 2:
            return SeniorityLevel.INTERMEDIATE
        else:
            return SeniorityLevel.BEGINNER
    
    def _extract_skills_with_seniority(self, text: str, experience: List[Experience]) -> List[SkillWithSeniority]:
        """Extract skills with seniority levels."""
        skills = self._extract_skills(text)
        skills_with_seniority = []
        
        for skill in skills:
            seniority = self._analyze_skill_seniority(skill, text, experience)
            skills_with_seniority.append(SkillWithSeniority(
                name=skill,
                seniority=seniority
            ))
        
        return skills_with_seniority
    
    def _extract_education(self, text: str) -> List[Education]:
        """Extract education information from resume text."""
        education = []
        
        # Look for education section
        education_section = re.search(r'(?i)education(.*?)(?=\n\n|\Z)', text, re.DOTALL)
        if not education_section:
            return education
            
        education_text = education_section.group(1)
        
        # Extract degree and institution
        degree_pattern = r'(?i)(bachelor|master|phd|doctorate|associate|diploma|degree).*?(?=\n|$)'
        institution_pattern = r'(?i)(university|college|institute|school).*?(?=\n|$)'
        
        degrees = re.finditer(degree_pattern, education_text)
        institutions = re.finditer(institution_pattern, education_text)
        
        for degree_match, institution_match in zip(degrees, institutions):
            degree = degree_match.group(0).strip()
            institution = institution_match.group(0).strip()
            
            # Extract graduation year
            year_pattern = r'\b(19|20)\d{2}\b'
            year_match = re.search(year_pattern, education_text)
            graduation_year = int(year_match.group(0)) if year_match else 2023
            
            education.append(Education(
                degree=degree,
                institution=institution,
                graduation_year=graduation_year
            ))
            
        return education
    
    def _extract_experience(self, text: str) -> List[Experience]:
        """Extract work experience from resume text."""
        experience = []
        
        try:
            # Look for experience section
            experience_section = re.search(r'(?i)experience(.*?)(?=\n\n|\Z)', text, re.DOTALL)
            if not experience_section:
                # If no experience section found, add a default experience
                default_exp = Experience(
                    title="Default Position",
                    company="Default Company",
                    start_date=datetime.now().date(),
                    end_date=datetime.now().date(),
                    description=["Default description"],
                    skills_used=["Default Skill"]
                )
                experience.append(default_exp)
                return experience
                
            experience_text = experience_section.group(1)
            
            # Split into individual experiences
            experiences = re.split(r'\n(?=[A-Z])', experience_text)
            
            for exp_text in experiences:
                try:
                    # Skip empty experiences
                    if not exp_text.strip():
                        continue
                        
                    # Extract position and company
                    position_company = exp_text.strip().split('\n')[0]
                    position = ""
                    company = ""
                    
                    # Try to split position and company
                    if '|' in position_company:
                        parts = position_company.split('|')
                        position = parts[0].strip()
                        company = parts[1].strip()
                    elif '-' in position_company:
                        parts = position_company.split('-')
                        position = parts[0].strip()
                        company = parts[1].strip()
                    elif 'at' in position_company.lower():
                        parts = position_company.lower().split('at')
                        position = parts[0].strip()
                        company = parts[1].strip()
                    else:
                        # If we can't split, use the whole line as position
                        position = position_company
                    
                    # Extract dates
                    date_pattern = r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)[\s,]+\d{4}\b'
                    dates = re.findall(date_pattern, exp_text)
                    
                    start_date = datetime.now().date()
                    end_date = datetime.now().date()
                    
                    if len(dates) >= 2:
                        # If we have at least two dates, use them as start and end
                        try:
                            start_date = datetime.strptime(dates[0], '%B %Y').date()
                            end_date = datetime.strptime(dates[1], '%B %Y').date()
                        except:
                            # If parsing fails, use defaults
                            pass
                    
                    # Extract description
                    description = []
                    desc_lines = re.findall(r'(?m)^\s*[-•]\s*(.*?)$', exp_text)
                    for line in desc_lines:
                        if line.strip():
                            description.append(line.strip())
                    
                    # If no description found, add a default
                    if not description:
                        description = ["Default description"]
                    
                    # Extract skills used
                    skills_used = self._extract_skills(exp_text)
                    
                    # If no skills found, add a default
                    if not skills_used:
                        skills_used = ["Default Skill"]
                    
                    # Create experience object
                    exp = Experience(
                        title=position or "Default Position",
                        company=company or "Default Company",
                        start_date=start_date,
                        end_date=end_date,
                        description=description,
                        skills_used=skills_used
                    )
                    
                    experience.append(exp)
                except Exception as e:
                    logger.error(f"Error extracting experience: {e}")
                    # Add a default experience if extraction fails
                    default_exp = Experience(
                        title="Default Position",
                        company="Default Company",
                        start_date=datetime.now().date(),
                        end_date=datetime.now().date(),
                        description=["Default description"],
                        skills_used=["Default Skill"]
                    )
                    experience.append(default_exp)
                    continue
        except Exception as e:
            logger.error(f"Error in experience extraction: {e}")
            # Return a default experience if there's an error
            default_exp = Experience(
                title="Default Position",
                company="Default Company",
                start_date=datetime.now().date(),
                end_date=datetime.now().date(),
                description=["Default description"],
                skills_used=["Default Skill"]
            )
            experience.append(default_exp)
            
        return experience
    
    def parse_resume(self, text: str) -> ResumeData:
        """Parse resume text into structured data."""
        try:
            name = self._extract_name(text)
            email = self._extract_email(text)
            phone = self._extract_phone(text)
            
            # First extract experience
            experience = self._extract_experience(text)
            
            # Then extract skills and analyze seniority
            skills = self._extract_skills(text)
            skills_with_seniority = self._extract_skills_with_seniority(text, experience)
            
            education = self._extract_education(text)
            
            # Ensure we have at least one experience entry
            if not experience:
                logger.warning("No experience found in resume, adding a default entry")
                experience = [
                    Experience(
                        title="Default Position",
                        company="Default Company",
                        start_date=datetime.now().date(),
                        end_date=datetime.now().date(),
                        description=["Default description"],
                        skills_used=skills[:5] if skills else ["Default Skill"]
                    )
                ]
            
            return ResumeData(
                name=name,
                email=email,
                phone=phone,
                skills=skills,
                skills_with_seniority=skills_with_seniority,
                education=education,
                experience=experience
            )
        except Exception as e:
            logger.error(f"Error parsing resume: {e}")
            # Return a basic ResumeData object with default values if parsing fails
            return ResumeData(
                name="Unknown",
                email="unknown@example.com",
                phone="",
                skills=[],
                skills_with_seniority=[],
                education=[],
                experience=[
                    Experience(
                        title="Default Position",
                        company="Default Company",
                        start_date=datetime.now().date(),
                        end_date=datetime.now().date(),
                        description=["Default description"],
                        skills_used=["Default Skill"]
                    )
                ]
            )

# Create a global parser instance
parser = ResumeParser()

def extract_entities(text: str) -> ResumeData:
    """Extract structured data from resume text."""
    try:
        # Log the input text for debugging
        logging.debug(f"Input text for entity extraction: {text[:500]}...")
        
        # Extract name
        name = parser._extract_name(text)
        logging.debug(f"Extracted name: {name}")
        
        # Extract email
        email = parser._extract_email(text)
        logging.debug(f"Extracted email: {email}")
        
        # Extract phone
        phone = parser._extract_phone(text)
        logging.debug(f"Extracted phone: {phone}")
        
        # Extract experience first
        experience = parser._extract_experience(text)
        logging.debug(f"Extracted experience: {experience}")
        
        # Extract skills and analyze seniority levels
        skills = parser._extract_skills(text)
        logging.debug(f"Extracted skills: {skills}")
        
        skills_with_seniority = parser._extract_skills_with_seniority(text, experience)
        logging.debug(f"Skills with seniority: {skills_with_seniority}")
        
        # Extract education
        education = parser._extract_education(text)
        logging.debug(f"Extracted education: {education}")
        
        # Create ResumeData object
        resume_data = ResumeData(
            name=name,
            email=email,
            phone=phone,
            skills=skills,
            skills_with_seniority=skills_with_seniority,
            education=education,
            experience=experience
        )
        
        # Log the final ResumeData object for debugging
        logging.debug(f"Final ResumeData object: {resume_data}")
        
        return resume_data
    except Exception as e:
        logging.error(f"Error in entity extraction: {e}")
        # Return a basic ResumeData object with default values if extraction fails
        return ResumeData(
            name="Unknown",
            email="unknown@example.com",
            phone="",
            skills=[],
            skills_with_seniority=[],
            education=[],
            experience=[
                Experience(
                    title="Default Position",
                    company="Default Company",
                    start_date=datetime.now().date(),
                    end_date=datetime.now().date(),
                    description=["Default description"],
                    skills_used=["Default Skill"]
                )
            ]
        )
