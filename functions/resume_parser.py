import json
from http.server import BaseHTTPRequestHandler
from parser.resume_parser import ResumeParser
from parser.resume_ranker import ResumeRanker

def handler(event, context):
    try:
        # Parse the request body
        body = json.loads(event['body'])
        resume_text = body.get('resume_text')
        job_requirements = body.get('job_requirements')

        if not resume_text:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Resume text is required'})
            }

        # Initialize parser and ranker
        parser = ResumeParser()
        ranker = ResumeRanker()

        # Parse resume
        resume_data = parser.parse_resume(resume_text)

        # If job requirements are provided, rank the resume
        if job_requirements:
            job_match = ranker.rank_resume(resume_data, job_requirements)
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'resume_data': resume_data.dict(),
                    'job_match': job_match.dict()
                })
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'resume_data': resume_data.dict()
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        } 