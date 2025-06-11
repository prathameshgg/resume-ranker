# AI Resume Parser and Ranker

An intelligent system that automatically parses resumes, extracts key information, and ranks candidates based on job requirements.

## Features

- **Resume Parsing**: Extract structured data from PDF and DOCX resumes
- **Intelligent Ranking**: Score candidates based on skills, experience, and education
- **Multi-Resume Ranking**: Upload and rank multiple resumes (2-20) from best to worst match
- **Alternative Role Suggestions**: Suggest better job roles for candidates
- **Batch Processing**: Analyze multiple resumes at once
- **User-Friendly Interface**: Simple web interface for easy interaction

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd resume-parser
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Download the spaCy model:

```bash
python -m spacy download en_core_web_sm
```

## Usage

1. Start the server:

```bash
uvicorn main:app --reload
```

2. Open your browser and navigate to:

```
http://localhost:8000
```

3. Use the web interface to:
   - Upload multiple resumes (PDF or DOCX) - up to 20 files
   - Define job requirements
   - Analyze and rank all candidates from best to worst match

## API Endpoints

- `POST /upload-resume`: Upload and parse a resume
- `POST /analyze-resume`: Analyze a resume against job requirements
- `POST /batch-analyze`: Analyze multiple resumes and rank them from best to worst

## Example Job Requirements

```json
{
  "title": "Senior Python Developer",
  "required_skills": ["Python", "Django", "REST API", "PostgreSQL"],
  "preferred_skills": ["Docker", "AWS", "CI/CD"],
  "experience_years": 5.0,
  "education_level": "Bachelor's Degree",
  "industry": "Technology",
  "keywords": ["backend", "web development", "api"]
}
```

## How It Works

1. **Resume Parsing**:

   - Extract text from PDF/DOCX files
   - Identify key sections (education, experience, skills)
   - Extract structured data using NLP

2. **Ranking Algorithm**:

   - Skill match (40% weight)
     - Required skills (70% of skill score)
     - Preferred skills (30% of skill score)
   - Experience match (30% weight)
     - Years of experience
     - Relevance of experience
   - Education match (20% weight)
   - Experience relevance (10% weight)

3. **Multi-Resume Ranking**:

   - Process multiple resumes in batch
   - Calculate match scores for each candidate
   - Sort candidates from highest to lowest match
   - Display detailed comparison

4. **Alternative Role Suggestions**:
   - Analyze skill sets
   - Match with predefined role requirements
   - Suggest better-fitting positions

## License

MIT
