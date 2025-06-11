import spacy
from typing import List, Dict, Any, Optional, Union
from models.response_model import ResumeData, Experience, Education
from models.job_model import JobRequirement, JobMatch, SkillFitment, CareerPathSuggestion, CareerForecast, TrajectoryPrediction, SkillGapForecast
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from datetime import datetime, date
from collections import defaultdict
import re
import logging

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ResumeRanker:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.vectorizer = TfidfVectorizer()
        
        # Initialize role categories and their typical requirements
        self.role_categories = {
            "Software Development": {
                "roles": ["Software Engineer", "Full Stack Developer", "Backend Developer", "Frontend Developer"],
                "core_skills": ["Python", "Java", "JavaScript", "SQL", "Git"],
                "market_demand": 0.9,
                "growth_potential": 0.85
            },
            "Data Science": {
                "roles": ["Data Scientist", "Machine Learning Engineer", "AI Engineer", "Data Analyst"],
                "core_skills": ["Python", "Machine Learning", "SQL", "Statistics", "Data Analysis"],
                "market_demand": 0.95,
                "growth_potential": 0.9
            },
            "DevOps": {
                "roles": ["DevOps Engineer", "Site Reliability Engineer", "Cloud Engineer", "Infrastructure Engineer"],
                "core_skills": ["AWS", "Docker", "Kubernetes", "CI/CD", "Linux"],
                "market_demand": 0.88,
                "growth_potential": 0.82
            }
        }
        
        # Market trends and skill relevance data
        self.market_trends = {
            "high_demand_skills": {
                "Cloud Computing": 0.95,
                "AI/ML": 0.92,
                "DevOps": 0.88,
                "Data Science": 0.90,
                "Cybersecurity": 0.89
            },
            "emerging_skills": {
                "Blockchain": 0.85,
                "Edge Computing": 0.82,
                "Quantum Computing": 0.75,
                "AR/VR": 0.78
            }
        }
        
        # Initialize recognized certifications dictionary
        self.recognized_certifications = {
            # Cloud
            "AWS Certified Solutions Architect": 0.95,
            "AWS Certified Developer": 0.90,
            "AWS Certified DevOps Engineer": 0.92,
            "Microsoft Azure Fundamentals": 0.85,
            "Microsoft Azure Administrator": 0.88,
            "Google Cloud Professional": 0.90,
            
            # Project Management
            "PMP": 0.95,  # Project Management Professional
            "PRINCE2": 0.90,
            "Scrum Master": 0.88,
            "Agile Certified Practitioner": 0.85,
            
            # Data
            "Google Data Analytics": 0.92,
            "IBM Data Science Professional": 0.90,
            "Microsoft Certified: Data Analyst Associate": 0.88,
            "Cloudera Certified Associate": 0.85,
            
            # IT & Security
            "CompTIA Security+": 0.90,
            "CISSP": 0.95,  # Certified Information Systems Security Professional
            "CEH": 0.90,    # Certified Ethical Hacker
            "ITIL Foundation": 0.85,
            
            # Programming & Development
            "Oracle Certified Java Programmer": 0.85,
            "Microsoft Certified: Azure Developer Associate": 0.88,
            "Certified Kubernetes Administrator": 0.90,
            "Terraform Associate": 0.85
        }
        
        # Update with additional certifications
        self.recognized_certifications.update({
    # Cloud & DevOps
    "AWS Certified Cloud Practitioner": 0.88,
    "AWS Certified SysOps Administrator": 0.89,
    "AWS Certified Advanced Networking": 0.87,
    "Google Associate Cloud Engineer": 0.88,
    "Google Cloud DevOps Engineer": 0.90,
    "Microsoft Certified: Azure Solutions Architect Expert": 0.92,
    "Microsoft Certified: Azure DevOps Engineer Expert": 0.91,
    "HashiCorp Certified: Vault Associate": 0.84,
    "Certified Jenkins Engineer": 0.82,
    "Docker Certified Associate": 0.87,
    "Red Hat Certified System Administrator (RHCSA)": 0.88,
    "Red Hat Certified Engineer (RHCE)": 0.90,
    "Ansible Automation Certification": 0.85,

    # CS50 (Harvard University)
    "CS50's Introduction to Computer Science from Harvard University": 0.92,
    "CS50's Web Programming with Python and JavaScript": 0.90,
    "CS50's Computer Science for Business Professionals": 0.88,
    "CS50's Introduction to Artificial Intelligence with Python": 0.91,
    "CS50's Introduction to Programming with Python": 0.87,
    "CS50's Computer Science for Lawyers": 0.85,
    "CS50's Introduction to Programming with Scratch": 0.83,
    "CS50's Introduction to Cybersecurity": 0.85,
    "CS50's Introduction to Databases with SQL": 0.86,
    "CS50's Introduction to Programming with R": 0.84,

    # Google Ads & Marketing Certifications
    "Google Ads Apps Certification": 0.84,
    "Google Ads – Measurement Certification": 0.85,
    "AI-Powered Shopping ads Certification": 0.83,
"Google Ads Creative Certification": 0.82,
"Google Ads Display Certification": 0.84,
"Google Ads Search Certification": 0.86,
"Grow Offline Sales Certification": 0.82,
"AI-Powered Performance Ads Certification": 0.83,
"Google Ads Video Certification": 0.84,
"Google Analytics Certification": 0.88,
"Fundamentals of Digital Marketing": 0.86,
"Google Play Store Listing Certificate": 0.82,

    #Google AI/Cloud Certificates
    "Introduction to Generative AI from Google": 0.88,
"Introduction to Responsible AI from Google": 0.85,
"Gmail from Google": 0.80,
"Google Sheets – Advanced Topics": 0.81,
"Introduction to Image Generation from Google": 0.82,
"Google Calendar": 0.80,
"Google Sheets": 0.80,
"Planetary Scale Earth Observation with Google Earth Engine": 0.84,
"Introduction to Large Language Models from Google": 0.86,
"Google Data Analytics Certificate": 0.92,
"Google IT Support Certificate": 0.88,
"Google Project Management Certificate": 0.89,
"Google UX Design Certificate": 0.89,
"Google Digital Marketing & E-commerce": 0.87,

    # Google Developer Learning Paths
    "Build your first web app with Firebase": 0.84,
"Get started with Google Maps Platform": 0.83,
"Build apps with Flutter": 0.85,
"Introduction to SQL": 0.85,
"Get data from the internet": 0.82,
"Adapt for different screen sizes": 0.81,
"Build Actions for Google Assistant": 0.82,
"Kotlin fundamentals": 0.84,

#University MOOC Certifications
"Giving 2.0: Stanford University": 0.84,
"ART of the MOOC: Activism and Social Movements: Duke": 0.83,
"Global Diplomacy: University of London": 0.84,
"Learning to Teach Online: UNSW Sydney": 0.83,
"Get Interactive: University of London": 0.82,
"Sports Marketing: Northwestern University": 0.84,
"Math Prep: University of North Texas": 0.80,
"How to Create an Online Course: University of Edinburgh": 0.82,
"Finding Your Professional Voice: University of London": 0.81,
"A life with ADHD: University of Geneva": 0.81,




    # Project Management & Agile
    "Certified Scrum Product Owner (CSPO)": 0.85,
    "SAFe Agilist (SA)": 0.87,
    "PMI Agile Certified Practitioner (PMI-ACP)": 0.89,
    "Lean Six Sigma Yellow Belt": 0.82,
    "Lean Six Sigma Green Belt": 0.87,
    "Lean Six Sigma Black Belt": 0.90,
    "Certified Project Director (CPD)": 0.88,
    "CompTIA Project+": 0.83,

    # Data & Analytics
    "SAS Certified Data Scientist": 0.88,
    "Cloudera Certified Professional Data Scientist": 0.87,
    "Databricks Certified Data Engineer Associate": 0.88,
    "Microsoft Certified: Azure Data Scientist Associate": 0.87,
    "Tableau Desktop Specialist": 0.85,
    "Power BI Data Analyst Associate": 0.88,
    "Alteryx Designer Core Certification": 0.82,
    "Snowflake SnowPro Core Certification": 0.85,
    "MongoDB Certified Developer Associate": 0.84,
    "Neo4j Certified Professional": 0.81,

    # Security
    "GIAC Security Essentials (GSEC)": 0.90,
    "Certified Cloud Security Professional (CCSP)": 0.92,
    "Certified Information Security Manager (CISM)": 0.91,
    "Certified in Risk and Information Systems Control (CRISC)": 0.88,
    "Offensive Security Certified Professional (OSCP)": 0.93,
    "CompTIA Cybersecurity Analyst (CySA+)": 0.88,
    "CompTIA PenTest+": 0.87,
    "Cisco Certified CyberOps Associate": 0.86,
    "Fortinet NSE 4": 0.85,

    # AI / ML / Data Science
    "TensorFlow Developer Certificate": 0.88,
    "DeepLearning.AI TensorFlow Developer": 0.87,
    "MIT Professional Certificate in ML & AI": 0.90,
    "HarvardX Data Science Professional Certificate": 0.88,
    "AWS Certified Machine Learning – Specialty": 0.91,
    "IBM AI Engineering Professional Certificate": 0.86,
    "NVIDIA Deep Learning Institute Certificate": 0.84,
    "Google Cloud ML Engineer": 0.89,

    # Networking & Infrastructure
    "Cisco Certified Network Associate (CCNA)": 0.88,
    "Cisco Certified Network Professional (CCNP)": 0.90,
    "Cisco Certified Internetwork Expert (CCIE)": 0.93,
    "Juniper Networks Certified Associate (JNCIA)": 0.84,
    "VMware Certified Professional (VCP)": 0.87,
    "Aruba Certified Switching Associate": 0.82,
    "CompTIA Network+": 0.86,
    "CompTIA A+": 0.84,

    # Development & Programming
    "Microsoft Certified: Power Platform Developer Associate": 0.84,
    "Oracle Application Developer Certification": 0.85,
    "Salesforce Certified Platform Developer I": 0.87,
    "Salesforce Certified Platform App Builder": 0.86,
    "Android Developer Certification by Google": 0.85,
    "Flutter Developer Certification": 0.83,
    "Meta Front-End Developer Certificate": 0.86,
    "Meta Back-End Developer Certificate": 0.86,
    "JetBrains Certified Kotlin Developer": 0.84,
    "Rust Programming Certification (Coursera/Udemy)": 0.80,

    # IT Support & Administration
    "Google IT Support Professional Certificate": 0.86,
    "Microsoft Certified: Modern Desktop Administrator Associate": 0.84,
    "Apple Certified Support Professional (ACSP)": 0.82,
    "CompTIA Server+": 0.83,
    "ITIL 4 Managing Professional": 0.88,
    "ServiceNow Certified System Administrator": 0.86,
    "Zendesk Support Admin Certification": 0.81
})

        # Initialize company values databases - common values for major companies
        self.company_values_db = {
            "Technology": {
                "Google": ["innovation", "collaboration", "impact", "creativity", "diversity", "inclusion"],
                "Microsoft": ["respect", "integrity", "accountability", "growth mindset", "customer-centric"],
                "Amazon": ["customer obsession", "ownership", "innovation", "high standards", "frugality"],
                "Apple": ["innovation", "simplicity", "quality", "privacy", "accessibility"],
                "Facebook/Meta": ["move fast", "be bold", "focus on impact", "build social value", "transparency"],
                "Netflix": ["judgment", "communication", "curiosity", "courage", "passion", "selflessness"],
                "Default": ["innovation", "teamwork", "excellence", "customer focus", "integrity"]
            },
            "Finance": {
                "Goldman Sachs": ["client service", "excellence", "integrity", "partnership", "innovation"],
                "JPMorgan Chase": ["integrity", "fairness", "respect", "responsibility", "diversity"],
                "Morgan Stanley": ["doing the right thing", "giving back", "diversity", "excellence"],
                "Default": ["integrity", "client focus", "excellence", "ethics", "teamwork"]
            },
            "Healthcare": {
                "Johnson & Johnson": ["patients first", "ethics", "innovation", "quality", "community"],
                "Pfizer": ["courage", "excellence", "equity", "innovation", "collaboration"],
                "Default": ["patient care", "innovation", "ethics", "quality", "teamwork"]
            },
            "Default": ["innovation", "teamwork", "integrity", "customer focus", "excellence"]
        }
        
        # Cultural fit keywords associated with common company values
        self.cultural_keywords = {
            "innovation": ["innovative", "creative", "disruptive", "pioneering", "cutting-edge", "breakthrough", 
                          "inventive", "forward-thinking", "experimental", "novel", "advanced", "revolutionize"],
            
            "teamwork": ["collaborative", "team player", "cross-functional", "partnership", "cooperation", 
                        "relationship-building", "synergy", "communication", "supportive", "contribute"],
            
            "integrity": ["ethical", "honest", "transparent", "accountable", "responsible", "trustworthy", 
                         "principled", "moral", "fair", "compliance", "ethics"],
            
            "customer focus": ["customer-centric", "client-focused", "user experience", "customer satisfaction", 
                              "service-oriented", "customer success", "client relations", "user-centric"],
            
            "excellence": ["high-quality", "exceptional", "best-in-class", "outstanding", "superior", 
                          "top-tier", "world-class", "exemplary", "meticulous", "rigorous"],
            
            "diversity": ["inclusive", "diverse perspectives", "multicultural", "equality", "equity", 
                         "cultural awareness", "belonging", "representation", "accessibility"],
            
            "learning": ["continuous learning", "growth mindset", "adaptable", "intellectual curiosity", 
                        "learning agility", "professional development", "skill development"],
            
            "agility": ["adaptable", "flexible", "nimble", "pivot", "responsive", "quick", "dynamic", 
                       "resilient", "evolving", "change-oriented"],
            
            "ownership": ["accountable", "responsible", "initiative", "self-starter", "proactive", 
                         "autonomous", "self-directed", "take charge", "leadership"],
            
            "impact": ["results-driven", "outcome-focused", "impactful", "influential", "effective", 
                      "transformative", "meaningful", "significant contribution"],
            
            "sustainability": ["sustainable", "environmental", "eco-friendly", "green initiatives", 
                              "carbon footprint", "conservation", "renewable", "responsible"],
            
            "community": ["social impact", "community service", "giving back", "corporate citizenship", 
                         "philanthropy", "outreach", "volunteering"]
        }
        
    def _preprocess_text(self, text: str) -> str:
        doc = self.nlp(text.lower())
        return " ".join([token.text for token in doc if not token.is_stop and not token.is_punct])
    
    def _calculate_skill_match(self, resume_skills: List[str], job_skills: List[str], preferred_skills: List[str] = None) -> Dict[str, float]:
        resume_skills_set = set(s.lower() for s in resume_skills)
        job_skills_set = set(s.lower() for s in job_skills)
        preferred_skills_set = set(s.lower() for s in preferred_skills) if preferred_skills else set()
        
        # Calculate required skills match with more granular scoring
        if not job_skills_set:
            required_match = 0.0
        else:
            matching_required = resume_skills_set.intersection(job_skills_set)
            # Calculate base match
            base_match = len(matching_required) / len(job_skills_set)
            
            # Add bonus for having more than minimum required skills
            if len(matching_required) > len(job_skills_set) * 0.5:
                skill_bonus = min(0.2, (len(matching_required) - len(job_skills_set) * 0.5) * 0.1)
                required_match = min(1.0, base_match + skill_bonus)
            else:
                required_match = base_match
        
        # Calculate preferred skills match with more granular scoring
        if not preferred_skills_set:
            preferred_match = 0.0
        else:
            matching_preferred = resume_skills_set.intersection(preferred_skills_set)
            # Calculate base match
            base_preferred = len(matching_preferred) / len(preferred_skills_set)
            
            # Add bonus for having more than half of preferred skills
            if len(matching_preferred) > len(preferred_skills_set) * 0.5:
                preferred_bonus = min(0.15, (len(matching_preferred) - len(preferred_skills_set) * 0.5) * 0.1)
                preferred_match = min(1.0, base_preferred + preferred_bonus)
            else:
                preferred_match = base_preferred
        
        # Calculate overall skill match with adjusted weights
        # Required skills are more important (80%) than preferred skills (20%)
        overall_match = (required_match * 0.8) + (preferred_match * 0.2)
        
        # Add bonus for having a diverse skill set
        total_skills = len(resume_skills_set)
        if total_skills > len(job_skills_set) + len(preferred_skills_set):
            diversity_bonus = min(0.1, (total_skills - (len(job_skills_set) + len(preferred_skills_set))) * 0.02)
            overall_match = min(1.0, overall_match + diversity_bonus)
        
        return {
            "required_match": required_match,
            "preferred_match": preferred_match,
            "overall_match": overall_match,
            "matching_required": list(matching_required) if 'matching_required' in locals() else [],
            "matching_preferred": list(matching_preferred) if 'matching_preferred' in locals() else [],
            "missing_required": list(job_skills_set - resume_skills_set),
            "missing_preferred": list(preferred_skills_set - resume_skills_set) if preferred_skills_set else []
        }
    
    def _calculate_experience_match(self, resume_experience: List[Union[Dict, Experience]], required_years: float) -> Dict[str, float]:
        """Calculate experience match score based on required years."""
        try:
            if not resume_experience:
                return {
                    "experience_match": 0.0,
                    "relevance_match": 0.0,
                    "industry_match": 0.0,
                    "total_years": 0.0,
                    "relevant_years": 0.0
                }

            # Calculate total years of experience
            total_years = sum(self._calculate_experience_duration(exp) for exp in resume_experience)
            
            # Calculate experience match score based on required years
            if required_years <= 0:
                experience_match = 1.0  # If no years required, perfect match
            else:
                # Score decreases if experience is too low or too high
                if total_years < required_years:
                    experience_match = total_years / required_years
                else:
                    # Cap the score at 1.0, but slightly reduce if overqualified
                    experience_match = 1.0 - min(0.2, (total_years - required_years) * 0.05)

            # Calculate relevance match based on job titles and descriptions
            relevance_scores = []
            for exp in resume_experience:
                # Extract job title and description safely
                title = exp.title if hasattr(exp, 'title') else exp.get('title', '')
                description = exp.description if hasattr(exp, 'description') else exp.get('description', '')
                
                # Convert to string and handle lists
                if isinstance(title, list):
                    title = ' '.join(str(t) for t in title)
                if isinstance(description, list):
                    description = ' '.join(str(d) for d in description)
                
                # Convert to lowercase safely, handling non-string types
                title = str(title).lower() if title else ''
                description = str(description).lower() if description else ''
                
                # Calculate relevance score for this experience
                title_relevance = 0.0
                desc_relevance = 0.0
                
                # Check for relevant keywords in title
                relevant_keywords = ['engineer', 'developer', 'analyst', 'manager', 'lead', 'architect', 'specialist']
                for keyword in relevant_keywords:
                    if keyword in title:
                        title_relevance += 0.2
                
                # Check for technical terms in description
                technical_terms = ['python', 'java', 'javascript', 'sql', 'aws', 'cloud', 'database', 
                                 'api', 'web', 'mobile', 'software', 'system', 'network', 'security']
                for term in technical_terms:
                    if term in description:
                        desc_relevance += 0.1
                
                # Combine scores for this experience
                exp_relevance = min(1.0, (title_relevance + desc_relevance) / 2)
                relevance_scores.append(exp_relevance)
            
            # Calculate average relevance match
            relevance_match = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
            
            # Calculate industry match (simplified)
            industry_match = 0.7  # Default to moderate industry match
            
            return {
                "experience_match": experience_match,
                "relevance_match": relevance_match,
                "industry_match": industry_match,
                "total_years": total_years,
                "relevant_years": total_years * relevance_match  # Weighted by relevance
            }
            
        except Exception as e:
            logger.error(f"Error in experience match calculation: {e}")
            return {
                "experience_match": 0.0,
                "relevance_match": 0.0,
                "industry_match": 0.0,
                "total_years": 0.0,
                "relevant_years": 0.0
            }
    
    def _calculate_experience_match_alt(self, resume_experience: List[Union[Dict, Experience]], required_years: float) -> Dict[str, float]:
        """Alternative method to calculate experience match score based on required years."""
        try:
            if not resume_experience:
                return {
                    "experience_match": 0.0,
                    "relevance_match": 0.0,
                    "industry_match": 0.7,  # Default industry match
                    "total_years": 0.0,
                    "relevant_years": 0.0
                }

            # Calculate total years using a simpler approach
            total_years = 0
            for exp in resume_experience:
                # Get duration directly from experience object if available
                if hasattr(exp, 'duration'):
                    total_years += float(exp.duration)
                elif isinstance(exp, dict) and 'duration' in exp:
                    total_years += float(exp['duration'])
                else:
                    # Default to 1 year if duration not specified
                    total_years += 1.0

            # Calculate experience match score
            if required_years <= 0:
                experience_match = 1.0
            else:
                # Simple ratio-based scoring
                experience_match = min(1.0, total_years / required_years)

            # Calculate relevance using a simpler keyword-based approach
            relevance_scores = []
            for exp in resume_experience:
                # Get title and description safely
                title = getattr(exp, 'title', '') if hasattr(exp, 'title') else exp.get('title', '')
                description = getattr(exp, 'description', '') if hasattr(exp, 'description') else exp.get('description', '')

                # Convert to string safely
                title = str(title) if title else ''
                description = str(description) if description else ''

                # Simple keyword matching
                title_score = 0
                desc_score = 0

                # Title keywords with weights
                title_keywords = {
                    'engineer': 0.3,
                    'developer': 0.3,
                    'analyst': 0.2,
                    'manager': 0.2,
                    'lead': 0.2,
                    'architect': 0.3,
                    'specialist': 0.2
                }

                # Description keywords with weights
                desc_keywords = {
                    'python': 0.1,
                    'java': 0.1,
                    'javascript': 0.1,
                    'sql': 0.1,
                    'aws': 0.1,
                    'cloud': 0.1,
                    'database': 0.1,
                    'api': 0.1,
                    'web': 0.1,
                    'mobile': 0.1,
                    'software': 0.1,
                    'system': 0.1,
                    'network': 0.1,
                    'security': 0.1
                }

                # Calculate title score
                for keyword, weight in title_keywords.items():
                    if keyword in title.lower():
                        title_score += weight

                # Calculate description score
                for keyword, weight in desc_keywords.items():
                    if keyword in description.lower():
                        desc_score += weight

                # Combine scores
                exp_relevance = min(1.0, (title_score + desc_score) / 2)
                relevance_scores.append(exp_relevance)

            # Calculate average relevance
            relevance_match = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0

            return {
                "experience_match": experience_match,
                "relevance_match": relevance_match,
                "industry_match": 0.7,  # Default industry match
                "total_years": total_years,
                "relevant_years": total_years * relevance_match
            }

        except Exception as e:
            logger.error(f"Error in alternative experience match calculation: {e}")
            return {
                "experience_match": 0.0,
                "relevance_match": 0.0,
                "industry_match": 0.7,
                "total_years": 0.0,
                "relevant_years": 0.0
            }

    def _calculate_education_match(self, resume_education: List[Dict], required_level: str) -> Dict[str, Any]:
        """Calculate education match score based on required level."""
        try:
            education_levels = {
                "High School": 1,
                "Associate's Degree": 2,
                "Bachelor's Degree": 3,
                "Master's Degree": 4,
                "Doctorate": 5
            }
            
            required_level_value = education_levels.get(required_level, 0)
            
            if not resume_education:
                return {
                    "education_match": False,
                    "highest_degree": "Unknown",
                    "institution": "Unknown",
                    "graduation_year": 2023
                }
            
            # Find highest education level
            try:
                highest_education = max(resume_education, key=lambda x: education_levels.get(x.degree, 0))
                highest_level_value = education_levels.get(highest_education.degree, 0)
                
                # Check if education level meets requirements
                education_match = highest_level_value >= required_level_value
                
                return {
                    "education_match": education_match,
                    "highest_degree": highest_education.degree,
                    "institution": highest_education.institution,
                    "graduation_year": highest_education.graduation_year
                }
            except Exception as e:
                logger.error(f"Error calculating education match: {e}")
                # Return default values if there's an error
                return {
                    "education_match": False,
                    "highest_degree": "Unknown",
                    "institution": "Unknown",
                    "graduation_year": 2023
                }
        except Exception as e:
            logger.error(f"Error in education match calculation: {e}")
            # Return default values if there's an error
            return {
                "education_match": False,
                "highest_degree": "Unknown",
                "institution": "Unknown",
                "graduation_year": 2023
            }
    
    def _calculate_skill_fitment(self, candidate_skills: List[str], experience: List[Dict]) -> List[SkillFitment]:
        skill_fitment = []
        skill_usage = defaultdict(float)
        
        # Calculate skill usage and proficiency from experience
        for exp in experience:
            years = self._calculate_experience_duration(exp)
            for skill in exp.skills_used:
                skill_usage[skill] += years
        
        for skill in candidate_skills:
            # Calculate proficiency based on years of usage
            proficiency = min(1.0, skill_usage[skill] / 5.0)  # Cap at 5 years
            
            # Calculate market relevance
            relevance = 0.5  # Default relevance
            if skill in self.market_trends["high_demand_skills"]:
                relevance = self.market_trends["high_demand_skills"][skill]
            elif skill in self.market_trends["emerging_skills"]:
                relevance = self.market_trends["emerging_skills"][skill]
            
            skill_fitment.append(SkillFitment(
                skill_name=skill,
                proficiency_level=proficiency,
                relevance_score=relevance
            ))
        
        return skill_fitment

    def _identify_strength_areas(self, skill_fitment: List[SkillFitment]) -> List[str]:
        # Identify top skills based on combined proficiency and market relevance
        scored_skills = [(sf.skill_name, sf.proficiency_level * sf.relevance_score) 
                        for sf in skill_fitment]
        scored_skills.sort(key=lambda x: x[1], reverse=True)
        return [skill for skill, score in scored_skills[:5]]

    def _suggest_career_paths(self, skill_fitment: List[SkillFitment], 
                            experience_years: float) -> List[CareerPathSuggestion]:
        suggestions = []
        
        for category, details in self.role_categories.items():
            for role in details["roles"]:
                # Calculate skill match
                required_skills = set(details["core_skills"])
                candidate_skills = {sf.skill_name for sf in skill_fitment}
                matching_skills = required_skills.intersection(candidate_skills)
                skills_match_score = len(matching_skills) / len(required_skills)
                
                # Calculate overall fitment
                fitment_score = (
                    skills_match_score * 0.4 +
                    details["market_demand"] * 0.3 +
                    details["growth_potential"] * 0.3
                )
                
                # Identify skill gaps
                skill_gap = list(required_skills - candidate_skills)
                
                # Generate next steps
                next_steps = [
                    f"Learn {skill}" for skill in skill_gap[:3]
                ]
                if experience_years < 3:
                    next_steps.append("Gain more industry experience")
                if len(matching_skills) / len(required_skills) < 0.7:
                    next_steps.append("Focus on core skills for this role")
                
                suggestions.append(CareerPathSuggestion(
                    role_title=role,
                    fitment_score=fitment_score,
                    required_skills_match=skills_match_score,
                    market_demand=details["market_demand"],
                    growth_potential=details["growth_potential"],
                    skill_gap=skill_gap,
                    next_steps=next_steps
                ))
        
        # Sort by fitment score and return top suggestions
        suggestions.sort(key=lambda x: x.fitment_score, reverse=True)
        return suggestions[:5]

    def _calculate_market_alignment(self, skill_fitment: List[SkillFitment]) -> float:
        if not skill_fitment:
            return 0.0
            
        # Calculate market alignment based on high-demand and emerging skills
        high_demand_skills = [sf for sf in skill_fitment if sf.relevance_score >= 0.85]
        emerging_skills = [sf for sf in skill_fitment if 0.75 <= sf.relevance_score < 0.85]
        
        # Weight high-demand skills more heavily
        high_demand_score = sum(sf.relevance_score for sf in high_demand_skills) * 0.7 if high_demand_skills else 0
        emerging_score = sum(sf.relevance_score for sf in emerging_skills) * 0.3 if emerging_skills else 0
        
        total_score = high_demand_score + emerging_score
        total_skills = len(high_demand_skills) + len(emerging_skills)
        
        return total_score / total_skills if total_skills > 0 else 0.0

    def _calculate_experience_duration(self, experience) -> float:
        """Calculate the duration of an experience in years."""
        try:
            # Extract start and end dates safely
            start_date = experience.start_date if hasattr(experience, 'start_date') else experience.get('start_date')
            end_date = experience.end_date if hasattr(experience, 'end_date') else experience.get('end_date')
            
            # Handle different date formats
            if isinstance(start_date, str):
                try:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                except ValueError:
                    return 1.0  # Default to 1 year if can't parse
            
            if end_date and isinstance(end_date, str) and end_date.lower() not in ['present', 'current', 'now']:
                if isinstance(end_date, datetime) or isinstance(end_date, date):
                    end_date = end_date
                else:
                    end_date = datetime.strptime(end_date, '%Y-%m-%d')
            elif end_date and (isinstance(end_date, datetime) or isinstance(end_date, date)):
                end_date = end_date
            else:
                end_date = datetime.now()
            
            # If either date is None, use defaults
            if not start_date:
                start_date = datetime.now().date()
            if not end_date:
                end_date = datetime.now().date()
            
            # Calculate duration in years
            duration = (end_date - start_date).days / 365.25
            
            # Ensure duration is not negative
            return max(0.0, duration)
            
        except Exception as e:
            logger.error(f"Error calculating experience duration: {e}")
            return 1.0  # Default to 1 year if calculation fails

    def _calculate_certification_match(self, resume_certifications: List[str], required_certifications: List[str]) -> Dict[str, Any]:
        """
        Calculate certification relevance score by matching resume certifications to job requirements.
        Prioritizes industry-recognized certifications.
        
        Args:
            resume_certifications: List of certifications from the resume
            required_certifications: List of certifications required for the job
            
        Returns:
            Dictionary with match score and details
        """
        if not resume_certifications:
            return {
                "certification_match_score": 0.0,
                "matching_certifications": [],
                "missing_certifications": required_certifications if required_certifications else [],
                "has_industry_recognized": False
            }
            
        if not required_certifications:
            # If no specific certifications are required, we'll score based on having industry-recognized certs
            has_recognized = any(cert in self.recognized_certifications for cert in resume_certifications)
            recognized_certs = [cert for cert in resume_certifications if cert in self.recognized_certifications]
            
            if has_recognized:
                # Calculate average weight of recognized certifications
                avg_weight = sum(self.recognized_certifications.get(cert, 0.5) for cert in recognized_certs) / len(recognized_certs)
                return {
                    "certification_match_score": avg_weight,
                    "matching_certifications": [],  # No specific requirements to match
                    "missing_certifications": [],
                    "has_industry_recognized": True,
                    "recognized_certifications": recognized_certs
                }
            else:
                return {
                    "certification_match_score": 0.3,  # Some credit for having any certifications
                    "matching_certifications": [],
                    "missing_certifications": [],
                    "has_industry_recognized": False
                }
        
        # Standardize certification names for better matching
        resume_certs_lower = [cert.lower() for cert in resume_certifications]
        required_certs_lower = [cert.lower() for cert in required_certifications]
        
        # Find exact matches
        matching_certs = []
        for req_cert in required_certs_lower:
            for res_cert in resume_certs_lower:
                # Check for exact match or if the required cert is contained in the resume cert
                if req_cert == res_cert or req_cert in res_cert:
                    matching_certs.append(req_cert)
                    break
        
        # Calculate base match score
        if not required_certs_lower:
            base_score = 0.0
        else:
            base_score = len(matching_certs) / len(required_certs_lower)
        
        # Bonus for having industry-recognized certifications
        has_recognized = any(cert in self.recognized_certifications for cert in resume_certifications)
        recognized_bonus = 0.2 if has_recognized else 0.0
        
        # Calculate final score (capped at 1.0)
        final_score = min(1.0, base_score + recognized_bonus)
        
        # Get original case for matched certifications
        matching_originals = []
        for match in matching_certs:
            for cert in required_certifications:
                if match == cert.lower():
                    matching_originals.append(cert)
                    break
        
        # Missing certifications
        missing_certs = [cert for cert in required_certifications if cert.lower() not in matching_certs]
        
        return {
            "certification_match_score": final_score,
            "matching_certifications": matching_originals,
            "missing_certifications": missing_certs,
            "has_industry_recognized": has_recognized
        }

    def _calculate_cultural_fit(self, resume_data: ResumeData, job_requirement: JobRequirement) -> Dict[str, Any]:
        """
        Calculate a cultural fit score based on how well the resume's tone and keywords align with company values
        """
        # Get company values - either from job requirements or use defaults based on industry
        company_values = []
        if job_requirement.company_values and len(job_requirement.company_values) > 0:
            company_values = job_requirement.company_values
        else:
            # Use industry defaults if available
            industry = job_requirement.industry
            if industry in self.company_values_db:
                company_values = self.company_values_db.get(industry, {}).get("Default", [])
            else:
                company_values = self.company_values_db.get("Default", [])
        
        if not company_values:
            return {
                "cultural_fit_score": 0.0,  # Changed from 0.5 to 0.0 for no values
                "cultural_fit_details": {
                    "matched_values": [],
                    "matched_keywords": [],
                    "improvement_suggestions": ["No company values provided for cultural fit assessment"]
                },
                "company_values": []
            }
        
        # Extract text from different parts of the resume
        resume_text = ""
        
        # Add experience descriptions
        for exp in resume_data.experience:
            if hasattr(exp, 'description') and exp.description:
                if isinstance(exp.description, list):
                    resume_text += " ".join(exp.description) + " "
                else:
                    resume_text += exp.description + " "
        
        # Add skills (as these often contain soft skills)
        if resume_data.skills:
            resume_text += " ".join(resume_data.skills) + " "
            
        # Preprocess the text
        resume_text = self._preprocess_text(resume_text.lower())
        
        # Track matched values and keywords
        matched_values = []
        matched_keywords = []
        
        # For each company value, check if related keywords appear in the resume
        value_scores = []
        for value in company_values:
            value_lower = value.lower()
            # Direct value match (the value itself appears)
            direct_match = value_lower in resume_text
            
            # Check for related keywords
            related_keywords = self.cultural_keywords.get(value_lower, [])
            if not related_keywords:
                # If no predefined keywords, use the value itself as a keyword
                related_keywords = [value_lower]
            
            keyword_matches = []
            for keyword in related_keywords:
                if keyword.lower() in resume_text:
                    keyword_matches.append(keyword)
            
            # Calculate score for this value (0.0 to 1.0)
            # Direct match gives 0.8, each keyword adds up to 0.2 more
            value_score = 0.0
            if direct_match:
                value_score += 0.8
                matched_values.append(value)
            
            if keyword_matches:
                # Add up to 0.2 based on percentage of keywords matched
                keyword_score = min(0.2, (len(keyword_matches) / len(related_keywords)) * 0.2)
                value_score += keyword_score
                matched_keywords.extend(keyword_matches)
            
            if value_score > 0:
                value_scores.append(value_score)
        
        # Calculate overall cultural fit score (average of value scores)
        if value_scores:
            cultural_fit_score = sum(value_scores) / len(company_values)
        else:
            cultural_fit_score = 0.0
        
        # Generate improvement suggestions for values with no matches
        improvement_suggestions = []
        for value in company_values:
            if value not in matched_values:
                keywords = self.cultural_keywords.get(value.lower(), [])[:3]  # Get top 3 keywords
                if keywords:
                    suggestion = f"Highlight experience demonstrating '{value}' (keywords: {', '.join(keywords)})"
                    improvement_suggestions.append(suggestion)
        
        # Remove duplicates
        matched_values = list(set(matched_values))
        matched_keywords = list(set(matched_keywords))
        
        # Create cultural fit badge based on score
        fit_badge = ""
        if cultural_fit_score >= 0.7:
            fit_badge = "✅ High Fit"
        elif cultural_fit_score >= 0.4:
            fit_badge = "⚠️ Moderate Fit"
        else:
            fit_badge = "❌ Low Fit"
        
        # Add explanation for the score
        score_explanation = []
        if cultural_fit_score == 0.0:
            score_explanation.append("No cultural values matched in the resume")
        elif cultural_fit_score < 0.4:
            score_explanation.append("Limited alignment with company values")
        elif cultural_fit_score < 0.7:
            score_explanation.append("Moderate alignment with company values")
        else:
            score_explanation.append("Strong alignment with company values")
            
        if matched_values:
            score_explanation.append(f"Matched values: {', '.join(matched_values)}")
        if improvement_suggestions:
            score_explanation.append("Areas for improvement: " + "; ".join(improvement_suggestions[:2]))
        
        # Return the results
        return {
            "cultural_fit_score": cultural_fit_score,
            "cultural_fit_details": {
                "matched_values": matched_values,
                "matched_keywords": matched_keywords,
                "improvement_suggestions": improvement_suggestions,
                "fit_badge": fit_badge,
                "score_explanation": " | ".join(score_explanation)
            },
            "company_values": company_values
        }

    def _analyze_career_progression(self, experiences: List[Union[Dict, Experience]]) -> Dict[str, Any]:
        """Analyze career progression, including promotion trajectory, job switching, and employment gaps."""
        
        # Sort experiences by start date in descending order (most recent first)
        sorted_experiences = sorted(
            experiences,
            key=lambda exp: exp.start_date if hasattr(exp, 'start_date') else exp.get('start_date', ''),
            reverse=True
        )
        
        # Prepare data for analysis
        promotion_trajectory = []
        job_changes = []
        employment_gaps = []
        
        # Track positions for promotion analysis
        last_level = None
        last_company = None
        last_end_date = None
        
        # Define keywords that indicate seniority levels
        entry_level_keywords = ['intern', 'trainee', 'junior', 'assistant', 'associate', 'entry']
        mid_level_keywords = ['senior', 'lead', 'manager', 'supervisor', 'head', 'principal']
        executive_keywords = ['director', 'chief', 'vp', 'president', 'executive', 'ceo', 'cto', 'cfo', 'coo']
        
        # Process each experience
        for i, exp in enumerate(sorted_experiences):
            # Extract data safely
            title = exp.title if hasattr(exp, 'title') else exp.get('title', '')
            company = exp.company if hasattr(exp, 'company') else exp.get('company', '')
            start_date_str = exp.start_date if hasattr(exp, 'start_date') else exp.get('start_date', '')
            end_date_str = exp.end_date if hasattr(exp, 'end_date') else exp.get('end_date', '')
            
            # Standardize date formats
            try:
                if isinstance(start_date_str, datetime) or isinstance(start_date_str, date):
                    start_date = start_date_str
                else:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                    
                if end_date_str and isinstance(end_date_str, str) and end_date_str.lower() not in ['present', 'current', 'now']:
                    if isinstance(end_date_str, datetime) or isinstance(end_date_str, date):
                        end_date = end_date_str
                    else:
                        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                elif end_date_str and (isinstance(end_date_str, datetime) or isinstance(end_date_str, date)):
                    end_date = end_date_str
                else:
                    end_date = datetime.now()
            except (ValueError, TypeError):
                # Skip this experience if dates can't be parsed
                continue
            
            # Determine seniority level based on job title
            title_lower = title.lower()
            
            if any(keyword in title_lower for keyword in executive_keywords):
                current_level = "Executive"
            elif any(keyword in title_lower for keyword in mid_level_keywords):
                current_level = "Mid-level"
            elif any(keyword in title_lower for keyword in entry_level_keywords):
                current_level = "Entry-level"
            else:
                current_level = "Unknown"
            
            # Add to promotion trajectory if this is not the first experience
            if last_level is not None:
                # Only add meaningful promotions (skip if titles or companies are empty or 'Unknown')
                from_title = sorted_experiences[i-1].title if i > 0 and hasattr(sorted_experiences[i-1], 'title') else sorted_experiences[i-1].get('title', '') if i > 0 else "Previous Role"
                to_title = title
                from_company = last_company
                to_company = company
                from_level = last_level
                to_level = current_level
                if (from_title and to_title and from_title != 'Unknown' and to_title != 'Unknown' and
                    from_company and to_company and from_company != 'Unknown' and to_company != 'Unknown' and
                    from_level != 'Unknown' and to_level != 'Unknown'):
                    promotion = {
                        "from_title": from_title,
                        "to_title": to_title,
                        "from_company": from_company,
                        "to_company": to_company,
                        "from_level": from_level,
                        "to_level": to_level,
                        "is_promotion": self._is_promotion(from_level, to_level),
                        "is_company_change": from_company != to_company
                    }
                    promotion_trajectory.append(promotion)
                # Add to job changes (only if meaningful)
                if (from_title and to_title and from_title != 'Unknown' and to_title != 'Unknown' and
                    from_company and to_company and from_company != 'Unknown' and to_company != 'Unknown'):
                    job_changes.append({
                        "from_position": from_title,
                        "to_position": to_title,
                        "from_company": from_company,
                        "to_company": to_company,
                        "date": start_date
                    })
            
            # Check for employment gap
            if last_end_date and (start_date - last_end_date).days > 180:  # 6 months gap
                gap = {
                    "start_date": last_end_date,
                    "end_date": start_date,
                    "duration_months": round((start_date - last_end_date).days / 30),
                    "previous_position": sorted_experiences[i-1].title if i > 0 and hasattr(sorted_experiences[i-1], 'title') 
                                        else sorted_experiences[i-1].get('title', '') if i > 0 else "Previous Role",
                    "next_position": title
                }
                employment_gaps.append(gap)
            
            # Update last values
            last_level = current_level
            last_company = company
            last_end_date = end_date
        
        # Calculate job switch frequency
        total_years = sum(self._calculate_experience_duration(exp) for exp in experiences)
        num_job_changes = len(job_changes)
        
        # Determine frequency tag
        switch_frequency = {
            "total_switches": num_job_changes,
            "years_of_experience": round(total_years, 1),
            "switches_per_year": round(num_job_changes / max(total_years, 1), 2),
            "frequency_tag": "Stable"  # Default tag
        }
        
        if switch_frequency["switches_per_year"] > 0.5:
            switch_frequency["frequency_tag"] = "Frequent Switcher"
        elif switch_frequency["switches_per_year"] > 0.3:
            switch_frequency["frequency_tag"] = "Moderate Switcher"
        else:
            switch_frequency["frequency_tag"] = "Stable"
        
        # Return the complete analysis
        return {
            "promotion_trajectory": promotion_trajectory,
            "job_switch_frequency": switch_frequency,
            "employment_gaps": employment_gaps,
            "has_upward_mobility": any(p["is_promotion"] for p in promotion_trajectory) if promotion_trajectory else False,
            "has_significant_gaps": any(gap["duration_months"] >= 6 for gap in employment_gaps)
        }
    
    def _is_promotion(self, previous_level: str, current_level: str) -> bool:
        """Determine if a level change constitutes a promotion."""
        level_ranking = {
            "Entry-level": 1,
            "Mid-level": 2,
            "Executive": 3,
            "Unknown": 0
        }
        
        return level_ranking.get(current_level, 0) > level_ranking.get(previous_level, 0)

    def _forecast_career_trajectory(self, resume_data: ResumeData, job_requirement: JobRequirement) -> CareerForecast:
        """
        Forecast a candidate's career trajectory using sequence modeling techniques.
        This simulates a trained ML model for trajectory prediction.
        
        Args:
            resume_data: The candidate's resume data
            job_requirement: The job requirements
            
        Returns:
            CareerForecast object with 3-year prediction
        """
        # In a real implementation, this would use a trained sequence model
        # Here we'll simulate predictions based on existing data
        
        # Extract key features from resume for prediction
        current_skills = set(resume_data.skills)
        
        # Determine the current career level based on most recent position
        current_position = None
        if resume_data.experience and len(resume_data.experience) > 0:
            current_position = resume_data.experience[0]  # Most recent position
        
        current_title = current_position.title if current_position else "Unknown"
        current_company = current_position.company if current_position else "Unknown"
        
        # Determine seniority level
        entry_level_keywords = ['intern', 'trainee', 'junior', 'assistant', 'associate', 'entry']
        mid_level_keywords = ['senior', 'lead', 'manager', 'supervisor', 'head', 'principal']
        executive_keywords = ['director', 'chief', 'vp', 'president', 'executive', 'ceo', 'cto', 'cfo', 'coo']
        
        current_level = "Unknown"
        title_lower = current_title.lower()
        if any(keyword in title_lower for keyword in executive_keywords):
            current_level = "Executive"
        elif any(keyword in title_lower for keyword in mid_level_keywords):
            current_level = "Mid-level"
        elif any(keyword in title_lower for keyword in entry_level_keywords):
            current_level = "Entry-level"
        
        # Always use a valid level for progression
        if current_level == "Unknown":
            current_level = "Entry-level"
        
        # Calculate total experience
        total_exp_years = sum(self._calculate_experience_duration(exp) for exp in resume_data.experience)
        
        # Define industry-specific role progressions (simplified)
        role_progressions = {
            "Software Development": {
                "Entry-level": ["Software Engineer", "Senior Software Engineer", "Lead Engineer"],
                "Mid-level": ["Engineering Manager", "Solutions Architect", "Technical Director"],
                "Executive": ["CTO", "VP of Engineering", "Chief Architect"]
            },
            "Data Science": {
                "Entry-level": ["Data Analyst", "Data Scientist", "Senior Data Scientist"],
                "Mid-level": ["Lead Data Scientist", "ML Engineer", "Data Science Manager"],
                "Executive": ["Chief Data Officer", "Director of Data Science", "AI Research Director"]
            },
            "Marketing": {
                "Entry-level": ["Marketing Associate", "Marketing Specialist", "Senior Marketing Specialist"],
                "Mid-level": ["Marketing Manager", "Brand Manager", "Marketing Director"],
                "Executive": ["CMO", "VP of Marketing", "Chief Brand Officer"]
            },
            "Default": {
                "Entry-level": ["Specialist", "Senior Specialist", "Team Lead"],
                "Mid-level": ["Manager", "Senior Manager", "Director"],
                "Executive": ["Senior Director", "VP", "C-Suite Executive"]
            }
        }
        
        # Get progression based on industry or use default
        industry = job_requirement.industry
        progression = role_progressions.get(industry, role_progressions["Default"])
        
        # Start with the appropriate track based on current level
        track = progression.get(current_level, progression["Entry-level"])
        
        # Determine starting point within the track based on experience
        starting_index = 0
        if current_level == "Entry-level":
            if total_exp_years > 3:
                starting_index = 1
            if total_exp_years > 5:
                starting_index = 2
        elif current_level == "Mid-level":
            if total_exp_years > 8:
                starting_index = 1
            if total_exp_years > 12:
                starting_index = 2
        elif current_level == "Executive":
            if total_exp_years > 15:
                starting_index = 1
            if total_exp_years > 20:
                starting_index = 2
        
        # Create trajectory predictions
        timeline = []
        confidence_base = 0.85  # Base confidence
        confidence_decay = 0.1  # Decrease per year to reflect increasing uncertainty
        
        # Define industry-specific required skills for different roles
        industry_skills = {
            "Software Development": {
                "Entry-level": ["Programming", "Data Structures", "Algorithms", "Version Control", "Unit Testing"],
                "Mid-level": ["System Design", "Architecture", "Team Leadership", "Code Reviews", "Performance Optimization"],
                "Executive": ["Technical Strategy", "Team Building", "Business Acumen", "Stakeholder Management"]
            },
            "Data Science": {
                "Entry-level": ["Statistics", "Python", "Data Visualization", "SQL", "Machine Learning Basics"],
                "Mid-level": ["Advanced ML", "Feature Engineering", "Model Deployment", "Project Management", "Deep Learning"],
                "Executive": ["AI Strategy", "Business Value Creation", "Cross-functional Leadership", "Research Direction"]
            },
            "Default": {
                "Entry-level": ["Communication", "Technical Skills", "Problem Solving", "Time Management"],
                "Mid-level": ["Leadership", "Project Management", "Strategic Thinking", "Mentoring"],
                "Executive": ["Vision Setting", "Organizational Leadership", "Business Strategy", "Change Management"]
            }
        }
        
        # Get required skills based on industry
        industry_required_skills = industry_skills.get(industry, industry_skills["Default"])
        
        # Create forecasted trajectory for the next 3 years
        for year in range(3):
            # Index for the role to predict, capped at the last role in the track
            role_index = min(starting_index + year, len(track) - 1)
            predicted_role = track[role_index]
            
            # Adjust level if progression moves to next level
            adjusted_level = current_level
            if starting_index + year >= len(track):
                # Find the next level's track
                levels = list(progression.keys())
                current_level_index = levels.index(current_level) if current_level in levels else 0
                next_level_index = min(current_level_index + 1, len(levels) - 1)
                adjusted_level = levels[next_level_index]
                predicted_role = progression[adjusted_level][0]  # Start at beginning of next level
            
            # Define alternative roles
            alternative_roles = []
            # Look at other industries for alternatives
            for alt_industry, alt_progression in role_progressions.items():
                if alt_industry != industry:
                    if adjusted_level in alt_progression:
                        alt_role_index = min(role_index, len(alt_progression[adjusted_level]) - 1)
                        alternative_role = alt_progression[adjusted_level][alt_role_index]
                        alternative_roles.append(alternative_role)
            
            # Trim to just 2-3 alternatives
            alternative_roles = alternative_roles[:3]
            
            # Calculate confidence score with decay over time
            confidence_score = max(0.6, confidence_base - (year * confidence_decay))
            
            # Identify skill gaps for this role
            relevant_skills = industry_required_skills[adjusted_level]
            missing_skills = [skill for skill in relevant_skills if skill not in current_skills]
            
            # Create skill gap forecasts
            skill_gaps = []
            for i, skill in enumerate(missing_skills):
                priority = "High" if i < 2 else "Medium" if i < 4 else "Low"
                timeframe = f"Year {year + 1}"
                
                # Add some learning resources for key skills
                resources = None
                if skill in ["Python", "Machine Learning", "Statistics", "Programming"]:
                    resources = ["Coursera Specialization", "Udemy Course", "Technical Book"]
                elif skill in ["Leadership", "Management", "Communication"]:
                    resources = ["Leadership Workshop", "Management Book", "Communication Seminar"]
                
                gap = SkillGapForecast(
                    skills_needed=[skill],
                    priority_level=priority,
                    timeframe=timeframe,
                    relevance_score=0.9 if priority == "High" else 0.7 if priority == "Medium" else 0.5,
                    learning_resources=resources
                )
                skill_gaps.append(gap)
            
            # Calculate market demand score
            market_demand = 0.8  # Default score
            if industry == job_requirement.industry:
                market_demand = 0.9  # Higher for current industry
            
            # Add salary range
            salary_range = None
            if adjusted_level == "Entry-level":
                salary_range = {"min": 60000, "max": 85000}
            elif adjusted_level == "Mid-level":
                salary_range = {"min": 90000, "max": 130000}
            elif adjusted_level == "Executive":
                salary_range = {"min": 150000, "max": 250000}
            
            # Create trajectory prediction for this year
            prediction = TrajectoryPrediction(
                timepoint=f"Year {year + 1}",
                predicted_role=predicted_role,
                confidence_score=confidence_score,
                alternative_roles=alternative_roles,
                skill_gaps=skill_gaps,
                salary_range=salary_range,
                market_demand_score=market_demand
            )
            timeline.append(prediction)
        
        # Extract most critical skills to acquire across the timeline
        all_skills = []
        for prediction in timeline:
            for gap in prediction.skill_gaps:
                all_skills.extend([(skill, gap.priority_level, gap.relevance_score) for skill in gap.skills_needed])
        
        # Sort by priority and relevance
        priority_value = {"High": 3, "Medium": 2, "Low": 1}
        all_skills.sort(key=lambda x: (priority_value[x[1]], x[2]), reverse=True)
        
        # Extract top skills (unique)
        top_skills = []
        seen_skills = set()
        for skill, _, _ in all_skills:
            if skill not in seen_skills:
                top_skills.append(skill)
                seen_skills.add(skill)
                if len(top_skills) >= 5:  # Limit to top 5
                    break
        
        # Calculate industry alignment score
        industry_alignment = 0.7  # Default
        # Adjust based on matching skills with industry requirements
        industry_skills_flat = []
        for skills_by_level in industry_required_skills.values():
            industry_skills_flat.extend(skills_by_level)
        
        matching_industry_skills = sum(1 for skill in current_skills if skill in industry_skills_flat)
        if industry_skills_flat:
            industry_alignment = min(0.95, 0.6 + (matching_industry_skills / len(industry_skills_flat)) * 0.35)
        
        # Create the career forecast
        forecast = CareerForecast(
            forecast_timeline=timeline,
            baseline_accuracy=0.7,  # Simulated baseline accuracy
            ml_model_accuracy=0.85,  # Simulated ML model accuracy
            model_type="LSTM",       # Pretend we're using an LSTM model
            top_skills_to_acquire=top_skills,
            industry_alignment_score=industry_alignment
        )
        
        return forecast

    def rank_resume(self, resume_data: ResumeData, job_requirement: JobRequirement) -> JobMatch:
        """Rank a resume against job requirements."""
        
        try:
            # Calculate skill match
            skill_match = self._calculate_skill_match(
                resume_data.skills, 
                job_requirement.required_skills,
                job_requirement.preferred_skills
            )
            
            # Use the alternative experience match calculation
            experience_match = self._calculate_experience_match_alt(
                resume_data.experience,
                job_requirement.experience_years
            )
            
            # Calculate education match
            education_match = self._calculate_education_match(
                resume_data.education,
                job_requirement.education_level
            )
            
            # Calculate certification match score
            certification_match = self._calculate_certification_match(
                resume_data.certifications if resume_data.certifications else [],
                job_requirement.required_certifications if job_requirement.required_certifications else []
            )
            
            # Calculate skill fitment
            skill_fitment = self._calculate_skill_fitment(
                resume_data.skills,
                resume_data.experience
            )
            
            # Identify strength areas
            strength_areas = self._identify_strength_areas(skill_fitment)
            
            # Calculate total experience years (approximately)
            total_exp_years = sum(self._calculate_experience_duration(exp) for exp in resume_data.experience)
            
            # Suggest career paths
            career_suggestions = self._suggest_career_paths(skill_fitment, total_exp_years)
            
            # Calculate market alignment
            market_alignment = self._calculate_market_alignment(skill_fitment)
            
            # Calculate cultural fit
            cultural_fit = self._calculate_cultural_fit(resume_data, job_requirement)
            
            # Analyze career progression
            career_progression = self._analyze_career_progression(resume_data.experience)
            
            # Generate career trajectory forecast
            career_forecast = self._forecast_career_trajectory(resume_data, job_requirement)
            
            # Calculate overall match score (weighted average)
            # Skill match: 35%, Experience match: 25%, Education match: 15%, Certification match: 10%, Cultural fit: 15%
            if education_match.get("education_match", False):
                education_score = 1.0
            else:
                education_score = 0.5  # Partial credit even if education doesn't match exactly
                
            # Calculate weighted components with more granular scoring
            skill_component = skill_match["overall_match"] * 0.35
            
            # Experience component now considers both years and relevance
            experience_component = (
                experience_match["experience_match"] * 0.15 +  # Base experience match
                experience_match["relevance_match"] * 0.10     # Relevance of experience
            )
            
            education_component = education_score * 0.15
            certification_component = certification_match["certification_match_score"] * 0.10
            cultural_component = cultural_fit["cultural_fit_score"] * 0.15
            
            # Calculate overall match with more granular scoring
            overall_match = (
                skill_component +
                experience_component +
                education_component +
                certification_component +
                cultural_component
            )
            
            # Add bonus for having relevant experience
            if experience_match["relevant_years"] > 0:
                experience_bonus = min(0.1, experience_match["relevant_years"] * 0.02)
                overall_match = min(1.0, overall_match + experience_bonus)
            
            # Add bonus for having required certifications
            if certification_match["matching_certifications"]:
                cert_bonus = min(0.05, len(certification_match["matching_certifications"]) * 0.01)
                overall_match = min(1.0, overall_match + cert_bonus)
            
            # Add bonus for having high cultural fit
            if cultural_fit["cultural_fit_score"] > 0.7:
                cultural_bonus = min(0.05, (cultural_fit["cultural_fit_score"] - 0.7) * 0.1)
                overall_match = min(1.0, overall_match + cultural_bonus)
            
            # Add bonus for having high market alignment
            if market_alignment > 0.7:
                market_bonus = min(0.05, (market_alignment - 0.7) * 0.1)
                overall_match = min(1.0, overall_match + market_bonus)
            
            # Add bonus for having strong career progression
            if career_progression.get("has_upward_mobility", False):
                progression_bonus = 0.05
                overall_match = min(1.0, overall_match + progression_bonus)
            
            # Add bonus for having diverse skill set
            if len(resume_data.skills) > len(job_requirement.required_skills):
                diversity_bonus = min(0.05, (len(resume_data.skills) - len(job_requirement.required_skills)) * 0.01)
                overall_match = min(1.0, overall_match + diversity_bonus)
            
            # Add penalty for employment gaps
            if career_progression.get("employment_gaps"):
                gap_penalty = min(0.1, len(career_progression["employment_gaps"]) * 0.02)
                overall_match = max(0.0, overall_match - gap_penalty)
            
            # Add penalty for frequent job switching
            if career_progression.get("job_switch_frequency", {}).get("frequency_tag") == "Frequent Switcher":
                switch_penalty = 0.05
                overall_match = max(0.0, overall_match - switch_penalty)
            
            # Calculate overall fitment score (different from overall match)
            # This considers skill proficiency, career progression, and cultural fit
            skill_proficiency = sum(sf.proficiency_level for sf in skill_fitment) / len(skill_fitment) if skill_fitment else 0
            
            # Career stability factor (0.0 to 1.0)
            career_stability = 1.0 - (len(career_progression.get("employment_gaps", [])) * 0.15)
            career_stability = max(0.0, min(1.0, career_stability))  # Clamp between 0 and 1
            
            # Calculate overall fitment with new weights and bonuses
            overall_fitment = (
                skill_proficiency * 0.4 +           # Skill proficiency has highest weight
                career_stability * 0.3 +            # Career stability is second
                cultural_fit["cultural_fit_score"] * 0.3  # Cultural fit is equally important
            )
            
            # Add bonus for having high market alignment
            if market_alignment > 0.7:
                market_bonus = min(0.1, (market_alignment - 0.7) * 0.2)
                overall_fitment = min(1.0, overall_fitment + market_bonus)
            
            # Add bonus for having strong career progression
            if career_progression.get("has_upward_mobility", False):
                progression_bonus = 0.05
                overall_fitment = min(1.0, overall_fitment + progression_bonus)
            
            # Identify growth opportunities (missing skills + next steps)
            growth_opportunities = skill_match["missing_required"] + skill_match["missing_preferred"]
            
            # Include missing certifications in growth opportunities if relevant
            if certification_match["missing_certifications"]:
                growth_opportunities.extend([f"Obtain {cert} certification" for cert in certification_match["missing_certifications"]])
            
            # Include cultural fit improvement suggestions in growth opportunities
            if cultural_fit["cultural_fit_details"]["improvement_suggestions"]:
                growth_opportunities.extend(cultural_fit["cultural_fit_details"]["improvement_suggestions"][:2])  # Add top 2 suggestions
            
            # Get top 3 best matched roles
            best_matched_roles = sorted(career_suggestions, key=lambda x: x.fitment_score, reverse=True)[:3]
            
            # Return the job match result
            return JobMatch(
                job_title=job_requirement.title,
                match_score=overall_match,
                matching_skills=skill_match["matching_required"] + skill_match["matching_preferred"],
                missing_skills=skill_match["missing_required"] + skill_match["missing_preferred"],
                experience_match=experience_match["experience_match"],
                education_match=education_match["education_match"],
                suggested_roles=[s.role_title for s in career_suggestions],
                match_details={
                    "skill_match": skill_match,
                    "experience_match": experience_match,
                    "education_match": education_match,
                    "certification_match": certification_match,
                    "cultural_fit": cultural_fit
                },
                overall_fitment_score=overall_fitment,
                skill_fitment=skill_fitment,
                career_path_suggestions=career_suggestions,
                market_alignment_score=market_alignment,
                strength_areas=strength_areas,
                growth_opportunities=growth_opportunities[:5],  # Limit to top 5
                best_matched_roles=best_matched_roles,
                certification_match_score=certification_match["certification_match_score"],
                matching_certifications=certification_match["matching_certifications"],
                missing_certifications=certification_match["missing_certifications"],
                cultural_fit_score=cultural_fit["cultural_fit_score"],
                cultural_fit_details=cultural_fit["cultural_fit_details"],
                company_values=cultural_fit["company_values"],
                # Add career progression analysis results
                career_progression=career_progression,
                promotion_trajectory=career_progression["promotion_trajectory"],
                job_switch_frequency=career_progression["job_switch_frequency"],
                employment_gaps=career_progression["employment_gaps"],
                # Add career forecast
                career_forecast=career_forecast
            )
        except Exception as e:
            logger.error(f"Error in ranking resume: {e}")
            # Return a default job match with error details
            return JobMatch(
                job_title=job_requirement.title,
                match_score=0.5,
                matching_skills=[],
                missing_skills=[],
                experience_match=0.5,
                education_match=False,
                suggested_roles=[],
                match_details={"error": str(e)},
                overall_fitment_score=0.5,
                skill_fitment=[],
                career_path_suggestions=[],
                market_alignment_score=0.5,
                strength_areas=[],
                growth_opportunities=[],
                best_matched_roles=[]
            ) 