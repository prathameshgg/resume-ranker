from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from parser.extract_text import extract_text_from_pdf, extract_text_from_docx
from parser.extract_entities import extract_entities
from parser.resume_ranker import ResumeRanker
from models.response_model import ResumeData, Experience
from models.job_model import JobRequirement, JobMatch
from models.request_model import AnalyzeResumeRequest, BatchAnalyzeRequest
import os
from typing import List
import logging

app = FastAPI(title="AI Resume Parser and Ranker")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create static directory if it doesn't exist
os.makedirs("static", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

ranker = ResumeRanker()

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Resume Parser and Ranker</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                /* Light theme (default) */
                --bg-primary: #f9f9fb;
                --bg-secondary: #ffffff;
                --bg-tertiary: #f3f4f6;
                --bg-card: #ffffff;
                --bg-input: #ffffff;
                --bg-button-primary: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                --bg-button-secondary: #ffffff;
                --text-primary: #0f172a;
                --text-secondary: #4b5563;
                --text-tertiary: #6b7280;
                --text-inverted: #ffffff;
                --border-color: #e5e7eb;
                --shadow-color: rgba(0, 0, 0, 0.05);
                --hover-color: rgba(99, 102, 241, 0.05);
                --active-color: rgba(99, 102, 241, 0.1);
                --accent-color: #6366f1;
                --accent-secondary: #4f46e5;
                --success-color: #059669;
                --success-bg: #dcfce7;
                --error-color: #b91c1c;
                --error-bg: #fee2e2;
                --warning-color: #ea580c;
                --warning-bg: #ffedd5;
            }
            
            /* Dark theme */
            [data-theme="dark"] {
                --bg-primary: #1a1a2e;
                --bg-secondary: #16213e;
                --bg-tertiary: #0f172a;
                --bg-card: #1e293b;
                --bg-input: #1e293b;
                --bg-button-primary: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                --bg-button-secondary: #334155;
                --text-primary: #f3f4f6;
                --text-secondary: #d1d5db;
                --text-tertiary: #9ca3af;
                --text-inverted: #0f172a;
                --border-color: #334155;
                --shadow-color: rgba(0, 0, 0, 0.3);
                --hover-color: rgba(99, 102, 241, 0.15);
                --active-color: rgba(99, 102, 241, 0.2);
                --accent-color: #818cf8;
                --accent-secondary: #6366f1;
                --success-color: #10b981;
                --success-bg: #064e3b;
                --error-color: #ef4444;
                --error-bg: #7f1d1d;
                --warning-color: #f97316;
                --warning-bg: #7c2d12;
            }
        
        
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }

            @keyframes slideIn {
                from { transform: translateX(-20px); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }

            @keyframes scaleIn {
                from { transform: scale(0.95); opacity: 0; }
                to { transform: scale(1); opacity: 1; }
            }

            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.05); }
                100% { transform: scale(1); }
            }

            @keyframes float {
                0% { transform: translateY(0px); }
                50% { transform: translateY(-10px); }
                100% { transform: translateY(0px); }
            }

            @keyframes shimmer {
                0% { background-position: -1000px 0; }
                100% { background-position: 1000px 0; }
            }
            
            html, body {
                height: 100vh;
                width: 100vw;
                overflow-x: hidden;
                font-family: 'Poppins', sans-serif;
                line-height: 1.6;
                background-color: var(--bg-primary);
                color: var(--text-primary);
                transition: all 0.3s ease;
            }

            body {
                display: flex;
                flex-direction: column;
                min-height: 100vh;
            }

            h1 {
                font-family: 'Poppins', sans-serif;
                color: var(--text-primary);
                text-align: center;
                margin: 28px 0;
                font-size: 2.5rem;
                border-bottom: none;
                padding-bottom: 10px;
                letter-spacing: 0.5px;
                font-weight: 700;
                animation: fadeIn 0.8s ease-out;
            }
            
            /* Theme toggle styles */
            .theme-switch-wrapper {
                display: flex;
                align-items: center;
                position: absolute;
                top: 20px;
                right: 20px;
                z-index: 100;
            }
            
            .theme-switch {
                display: inline-block;
                height: 34px;
                position: relative;
                width: 60px;
            }
            
            .theme-switch input {
                display: none;
            }
            
            .slider {
                background-color: var(--bg-tertiary);
                bottom: 0;
                cursor: pointer;
                left: 0;
                position: absolute;
                right: 0;
                top: 0;
                transition: .4s;
                border-radius: 34px;
                border: 1px solid var(--border-color);
            }
            
            .slider:before {
                background-color: var(--bg-secondary);
                bottom: 4px;
                content: "";
                height: 24px;
                left: 4px;
                position: absolute;
                transition: .4s;
                width: 24px;
                border-radius: 50%;
                box-shadow: 0 2px 4px var(--shadow-color);
            }
            
            input:checked + .slider {
                background-color: var(--accent-color);
            }
            
            input:checked + .slider:before {
                transform: translateX(26px);
            }
            
            .theme-icon {
                margin: 0 10px;
                font-size: 18px;
            }

            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 32px;
                animation: fadeIn 1s ease-out;
            }

            .layout-section {
                display: none;
            }

            .active-section {
                display: block;
                animation: fadeIn 0.5s ease-out;
            }

            .full-width-card {
                width: 100%;
                margin-bottom: 40px;
            }

            .section-nav {
                display: flex;
                justify-content: space-between;
                margin-bottom: 30px;
                border-radius: 16px;
                overflow: hidden;
                background-color: var(--bg-secondary);
                box-shadow: 0 4px 12px var(--shadow-color);
            }

            .nav-item {
                flex: 1;
                text-align: center;
                padding: 16px;
                cursor: pointer;
                transition: all 0.3s ease;
                border-bottom: 3px solid transparent;
                color: var(--text-tertiary);
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 8px;
            }

            .nav-item:hover {
                background-color: var(--hover-color);
            }

            .nav-item.active {
                background-color: var(--active-color);
                color: var(--accent-color);
                border-bottom: 3px solid var(--accent-color);
                font-weight: 500;
            }

            .nav-icon {
                font-size: 24px;
                margin-bottom: 5px;
            }

            .nav-text {
                font-size: 14px;
            }

            .section-nav-buttons {
                display: flex;
                justify-content: flex-end;
                margin-top: 30px;
                gap: 15px;
            }

            .nav-button {
                padding: 12px 24px;
                border-radius: 12px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 500;
                transition: all 0.3s ease;
                box-shadow: 0 4px 6px var(--shadow-color);
            }

            .next-button {
                background: var(--bg-button-primary);
                color: var(--text-inverted);
                border: none;
            }

            .next-button:hover {
                box-shadow: 0 6px 8px rgba(99, 102, 241, 0.25);
                transform: translateY(-2px);
            }

            .prev-button {
                background: var(--bg-button-secondary);
                color: var(--text-secondary);
                border: 1px solid var(--border-color);
            }

            .prev-button:hover {
                box-shadow: 0 6px 8px var(--shadow-color);
                transform: translateY(-2px);
                background-color: var(--bg-tertiary);
            }

            .primary-button {
                background: var(--bg-button-primary);
                color: var(--text-inverted);
                border: none;
                padding: 12px 24px;
                border-radius: 12px;
                cursor: pointer;
                font-size: 1rem;
                font-weight: 500;
                transition: all 0.3s ease;
                box-shadow: 0 4px 6px var(--shadow-color);
                display: inline-block;
                margin-top: 16px;
            }

            .primary-button:hover {
                box-shadow: 0 6px 8px rgba(99, 102, 241, 0.25);
                transform: translateY(-2px);
            }

            .input-button {
                background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                color: white;
                border: none;
                padding: 12px 16px;
                border-radius: 12px;
                cursor: pointer;
                font-size: 0.9rem;
                font-weight: 500;
                transition: all 0.3s ease;
                box-shadow: 0 4px 6px rgba(99, 102, 241, 0.15);
            }

            .input-button:hover {
                box-shadow: 0 6px 8px rgba(99, 102, 241, 0.25);
                transform: translateY(-2px);
            }

            .accordion {
                margin-top: 24px;
                margin-bottom: 24px;
            }

            .accordion-item {
                margin-bottom: 16px;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                background-color: white;
                border: 1px solid #e5e7eb;
            }

            .accordion-header {
                background-color: #f9fafb;
                padding: 16px 20px;
                cursor: pointer;
                font-weight: 500;
                color: #0f172a;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: space-between;
                border-bottom: 1px solid #e5e7eb;
            }

            .accordion-header:after {
                content: '▼';
                font-size: 12px;
                color: #6366f1;
                transition: all 0.3s ease;
            }

            .accordion-item.active .accordion-header:after {
                transform: rotate(180deg);
            }

            .accordion-content {
                padding: 20px;
                display: none;
            }

            .accordion-item.active .accordion-content {
                display: block;
                animation: fadeIn 0.5s ease-out;
            }

            .upload-progress {
                display: flex;
                align-items: center;
                margin-top: 4px;
                color: #10b981;
                font-size: 0.9rem;
            }

            .success-icon {
                color: #10b981;
                margin-right: 8px;
                font-size: 16px;
            }

            .file-item {
                position: relative;
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 16px;
                background-color: #ffffff;
                border-radius: 8px;
                margin-bottom: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.03);
                border-left: 3px solid #6366f1;
            }

            .file-item.success {
                border-left-color: #10b981;
            }

            .file-item.error {
                border-left-color: #ef4444;
            }

            .file-status {
                position: absolute;
                right: 48px;
                font-size: 14px;
            }

            .side-by-side-container {
                display: flex;
                gap: 40px;
                margin-bottom: 40px;
                flex: 1;
                min-height: 0;
            }

            .side-by-side-container .card {
                flex: 1;
                display: flex;
                flex-direction: column;
                overflow: hidden;
                animation: scaleIn 0.5s ease-out;
            }

            .card {
                border: none;
                border-radius: 24px;
                padding: 32px;
                box-shadow: 0 10px 25px var(--shadow-color);
                background-color: var(--bg-card);
                transition: transform 0.3s ease, box-shadow 0.3s ease, background-color 0.3s ease;
                height: 100%;
                display: flex;
                flex-direction: column;
            }

            .card:hover {
                transform: translateY(-5px);
                box-shadow: 0 15px 35px var(--shadow-color);
            }

            .card-content {
                flex: 1;
                overflow-y: auto;
                padding-right: 15px;
            }

            .card-content::-webkit-scrollbar {
                width: 8px;
            }

            .card-content::-webkit-scrollbar-track {
                background: var(--bg-tertiary);
                border-radius: 4px;
            }

            .card-content::-webkit-scrollbar-thumb {
                background: var(--border-color);
                border-radius: 4px;
            }

            .card-content::-webkit-scrollbar-thumb:hover {
                background: var(--text-tertiary);
            }

            .card h2 {
                font-family: 'Poppins', sans-serif;
                color: var(--text-primary);
                margin-top: 0;
                border-bottom: 2px solid var(--border-color);
                padding-bottom: 16px;
                font-size: 1.8rem;
                letter-spacing: 0.3px;
                font-weight: 600;
                animation: slideIn 0.5s ease-out;
            }

            .section-description {
                background-color: var(--bg-tertiary);
                border-left: 4px solid var(--accent-color);
                padding: 16px 20px;
                margin-bottom: 24px;
                border-radius: 0 12px 12px 0;
                font-size: 0.95rem;
                color: var(--text-secondary);
                animation: fadeIn 0.6s ease-out;
            }

            .form-group {
                margin-bottom: 28px;
                animation: fadeIn 0.7s ease-out;
            }

            .form-group label {
                display: block;
                margin-bottom: 10px;
                font-weight: 500;
                color: var(--text-primary);
            }

            .form-group input, .form-group select, .form-group textarea {
                width: 100%;
                padding: 12px 16px;
                border: 1px solid var(--border-color);
                border-radius: 12px;
                font-size: 1rem;
                font-family: 'Poppins', sans-serif;
                transition: all 0.3s ease;
                background-color: var(--bg-input);
                color: var(--text-primary);
            }

            .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
                border-color: var(--accent-color);
                outline: none;
                box-shadow: 0 0 0 3px var(--hover-color);
                transform: translateY(-2px);
                background-color: var(--bg-input);
            }

            .form-group textarea {
                min-height: 100px;
                resize: vertical;
            }

            .input-group {
                display: flex;
                gap: 12px;
                margin-bottom: 14px;
            }

            .input-group input {
                flex: 1;
            }

            .input-group button {
                padding: 12px 20px;
                background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                color: white;
                border: none;
                border-radius: 12px;
                cursor: pointer;
                font-family: 'Poppins', sans-serif;
                font-weight: 500;
                transition: all 0.3s ease;
                box-shadow: 0 4px 6px rgba(99, 102, 241, 0.15);
            }

            .input-group button:hover {
                box-shadow: 0 6px 8px rgba(99, 102, 241, 0.25);
                transform: translateY(-2px);
            }

            .remove-skill {
                background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                color: white;
                border: none;
                border-radius: 50%;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                font-size: 14px;
                font-family: 'Poppins', sans-serif;
                transition: all 0.3s ease;
                box-shadow: 0 2px 4px rgba(239, 68, 68, 0.15);
            }

            .remove-skill:hover {
                background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
                box-shadow: 0 3px 6px rgba(239, 68, 68, 0.25);
                transform: rotate(90deg);
            }

            .skills-container {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-top: 14px;
            }

            .skill-tag {
                background-color: #eef2ff;
                color: #4f46e5;
                padding: 6px 14px;
                border-radius: 20px;
                font-size: 0.9rem;
                font-family: 'Poppins', sans-serif;
                display: flex;
                align-items: center;
                gap: 8px;
                animation: scaleIn 0.3s ease-out;
                box-shadow: 0 2px 4px rgba(79, 70, 229, 0.1);
            }

            .file-upload {
                border: 2px dashed #6366f1;
                border-radius: 16px;
                padding: 40px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s ease;
                margin-bottom: 24px;
                animation: float 3s ease-in-out infinite;
                background-color: rgba(99, 102, 241, 0.03);
            }

            .file-upload:hover {
                background-color: rgba(99, 102, 241, 0.05);
                transform: scale(1.02);
            }

            .file-upload.dragover {
                background-color: rgba(99, 102, 241, 0.1);
                border-color: #4f46e5;
                transform: scale(1.05);
            }

            .file-upload input[type="file"] {
                display: none;
            }

            .file-upload-icon {
                font-size: 48px;
                color: #6366f1;
                margin-bottom: 20px;
                animation: pulse 2s infinite;
            }

            .file-upload-text {
                color: #6b7280;
                margin-bottom: 15px;
                font-family: 'Poppins', sans-serif;
            }

            .file-list {
                margin-top: 24px;
                max-height: 200px;
                overflow-y: auto;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                padding: 14px;
                background-color: #f9fafb;
            }

            .file-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 16px;
                background-color: #ffffff;
                border-radius: 8px;
                margin-bottom: 10px;
                animation: slideIn 0.3s ease-out;
                box-shadow: 0 2px 4px rgba(0,0,0,0.03);
            }

            .file-item:last-child {
                margin-bottom: 0;
            }

            .file-name {
                flex: 1;
                margin-right: 12px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                font-family: 'Poppins', sans-serif;
                color: #4b5563;
            }

            .remove-file {
                background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                color: white;
                border: none;
                border-radius: 50%;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                font-size: 14px;
                font-family: 'Poppins', sans-serif;
                transition: all 0.3s ease;
                box-shadow: 0 2px 4px rgba(239, 68, 68, 0.15);
            }

            .remove-file:hover {
                background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
                box-shadow: 0 3px 6px rgba(239, 68, 68, 0.25);
                transform: rotate(90deg);
            }

            .candidate-card {
                border: none;
                border-radius: 16px;
                padding: 28px;
                margin-bottom: 30px;
                transition: all 0.3s ease, background-color 0.3s ease;
                animation: scaleIn 0.5s ease-out;
                background-color: var(--bg-card);
                box-shadow: 0 5px 15px var(--shadow-color);
                position: relative;
                border-top: 6px solid var(--accent-color);
            }

            .candidate-card.high-score {
                border-top-color: #10b981;
            }

            .candidate-card.medium-score {
                border-top-color: #f59e0b;
            }

            .candidate-card.low-score {
                border-top-color: #ef4444;
            }

            .candidate-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 25px var(--shadow-color);
            }

            .candidate-summary {
                display: flex;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 15px;
                margin: 20px 0;
                padding: 15px;
                background-color: var(--bg-tertiary);
                border-radius: 12px;
                transition: background-color 0.3s ease;
            }

            .summary-item {
                text-align: center;
                flex: 1;
                min-width: 100px;
            }

            .summary-label {
                font-size: 0.85rem;
                color: var(--text-tertiary);
                margin-bottom: 5px;
                transition: color 0.3s ease;
            }

            .summary-value {
                font-size: 1.1rem;
                font-weight: 600;
                color: var(--text-primary);
                transition: color 0.3s ease;
            }

            .candidate-details {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 28px;
                margin-bottom: 24px;
            }

            .skill-section {
                margin-bottom: 20px;
            }

            .skill-section h4 {
                font-size: 0.95rem;
                color: var(--text-secondary);
                margin-bottom: 10px;
                font-weight: 500;
                transition: color 0.3s ease;
            }

            .no-skills {
                color: var(--text-tertiary);
                font-style: italic;
                font-size: 0.9rem;
                transition: color 0.3s ease;
            }

            .career-stats {
                display: flex;
                gap: 20px;
                margin-bottom: 20px;
            }

            .stat-item {
                background-color: var(--bg-tertiary);
                padding: 10px 15px;
                border-radius: 10px;
                flex: 1;
                transition: background-color 0.3s ease;
            }

            .stat-label {
                font-size: 0.85rem;
                color: var(--text-tertiary);
                margin-bottom: 5px;
                transition: color 0.3s ease;
            }

            .stat-value {
                font-size: 1.1rem;
                font-weight: 600;
                color: var(--text-primary);
                transition: color 0.3s ease;
            }

            .strengths-list {
                margin-bottom: 20px;
            }

            .career-insights {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 28px;
                margin-top: 24px;
                padding-top: 24px;
                border-top: 1px solid var(--border-color);
                transition: border-color 0.3s ease;
            }

            .insights-section h3 {
                font-size: 1.1rem;
                color: var(--accent-color);
                margin-bottom: 15px;
                font-weight: 600;
                transition: color 0.3s ease;
            }

            .roles-list {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
            }

            .role-item {
                background-color: var(--hover-color);
                color: var(--accent-color);
                padding: 8px 16px;
                border-radius: 10px;
                font-size: 0.9rem;
                box-shadow: 0 2px 4px var(--shadow-color);
                transition: background-color 0.3s ease, color 0.3s ease, box-shadow 0.3s ease;
            }

            .growth-list {
                list-style-type: none;
                padding: 0;
                margin: 0;
            }

            .growth-list li {
                margin-bottom: 8px;
            }

            .growth-item {
                background-color: var(--bg-tertiary);
                color: var(--text-secondary);
                padding: 6px 12px;
                border-radius: 10px;
                font-size: 0.9rem;
                display: inline-block;
                transition: background-color 0.3s ease, color 0.3s ease;
            }

            .error-message {
                background-color: #fee2e2;
                color: #b91c1c;
                padding: 16px;
                border-radius: 12px;
                margin-top: 20px;
                animation: fadeIn 0.5s ease-out;
            }
            
            /* Scoring Configuration Styles */
            .scoring-config {
                animation: fadeIn 0.7s ease-out;
            }
            
            .weight-item {
                margin-bottom: 24px;
            }
            
            .weight-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            }
            
            .weight-header label {
                font-weight: 500;
                color: #0f172a;
                flex: 1;
            }
            
            .weight-percentage {
                font-weight: 600;
                color: #4f46e5;
                min-width: 48px;
                text-align: right;
                padding-left: 10px;
            }
            
            .weight-slider {
                -webkit-appearance: none;
                width: 100%;
                height: 8px;
                border-radius: 10px;
                background: #e5e7eb;
                outline: none;
            }
            
            .weight-slider::-webkit-slider-thumb {
                -webkit-appearance: none;
                appearance: none;
                width: 20px;
                height: 20px;
                border-radius: 50%;
                background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                cursor: pointer;
                box-shadow: 0 2px 5px rgba(79, 70, 229, 0.3);
                transition: all 0.2s ease;
            }
            
            .weight-slider::-webkit-slider-thumb:hover {
                transform: scale(1.1);
                box-shadow: 0 3px 7px rgba(79, 70, 229, 0.4);
            }
            
            .weight-slider::-moz-range-thumb {
                width: 20px;
                height: 20px;
                border-radius: 50%;
                background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                cursor: pointer;
                box-shadow: 0 2px 5px rgba(79, 70, 229, 0.3);
                transition: all 0.2s ease;
                border: none;
            }
            
            .weight-slider::-moz-range-thumb:hover {
                transform: scale(1.1);
                box-shadow: 0 3px 7px rgba(79, 70, 229, 0.4);
            }
            
            .weight-slider::-webkit-slider-runnable-track {
                width: 100%;
                height: 8px;
                cursor: pointer;
                border-radius: 10px;
            }
            
            .info-tooltip {
                position: relative;
                display: inline-block;
                margin-left: 8px;
            }
            
            .info-icon {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 18px;
                height: 18px;
                background-color: #e5e7eb;
                color: #6b7280;
                font-size: 12px;
                border-radius: 50%;
                cursor: help;
            }
            
            .tooltip-text {
                visibility: hidden;
                width: 200px;
                background-color: #1f2937;
                color: #fff;
                text-align: center;
                border-radius: 8px;
                padding: 8px 12px;
                position: absolute;
                z-index: 1;
                bottom: 125%;
                left: 50%;
                transform: translateX(-50%);
                opacity: 0;
                transition: opacity 0.3s;
                font-size: 0.85rem;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
            }
            
            .tooltip-text::after {
                content: "";
                position: absolute;
                top: 100%;
                left: 50%;
                margin-left: -5px;
                border-width: 5px;
                border-style: solid;
                border-color: #1f2937 transparent transparent transparent;
            }
            
            .info-tooltip:hover .tooltip-text {
                visibility: visible;
                opacity: 1;
            }
            
            .total-weight {
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-weight: 600;
                padding: 12px 16px;
                background-color: #f3f4f6;
                border-radius: 12px;
                margin: 20px 0;
            }
            
            #totalWeightPercentage {
                color: #4f46e5;
            }
            
            #totalWeightPercentage.error {
                color: #ef4444;
                animation: pulse 1s infinite;
            }
            
            /* Score Breakdown Styles */
            .score-breakdown {
                margin: 20px 0;
                padding: 20px;
                background-color: var(--bg-tertiary);
                border-radius: 12px;
                animation: fadeIn 0.7s ease-out;
                transition: background-color 0.3s ease;
            }
            
            .score-breakdown h4 {
                font-size: 1.1rem;
                margin-bottom: 15px;
                color: var(--text-primary);
                font-weight: 600;
                transition: color 0.3s ease;
            }
            
            .breakdown-item {
                margin-bottom: 12px;
            }
            
            .breakdown-label {
                display: flex;
                justify-content: space-between;
                margin-bottom: 6px;
                font-size: 0.9rem;
                color: var(--text-secondary);
                transition: color 0.3s ease;
            }
            
            .breakdown-bar {
                height: 10px;
                background-color: var(--border-color);
                border-radius: 10px;
                overflow: hidden;
                margin-bottom: 3px;
                transition: background-color 0.3s ease;
            }
            
            .breakdown-fill {
                height: 100%;
                border-radius: 10px;
                transition: width 1s ease-out;
                box-shadow: 0 1px 3px var(--shadow-color);
            }
            
            .skill-fill {
                background: linear-gradient(90deg, #6366f1, #4f46e5);
            }
            
            .experience-fill {
                background: linear-gradient(90deg, #10b981, #059669);
            }
            
                                .tech-fill {
                        background: linear-gradient(90deg, #f59e0b, #d97706);
                    }
                    
                    .culture-fill {
                        background: linear-gradient(90deg, #8b5cf6, #7c3aed);
                    }
            
            .breakdown-value {
                text-align: right;
                font-size: 0.85rem;
                color: var(--text-tertiary);
                font-weight: 500;
                transition: color 0.3s ease;
            }
            
            /* Weights Summary Styles */
            .weights-summary {
                background-color: var(--bg-card);
                border-radius: 16px;
                padding: 20px 24px;
                margin-bottom: 30px;
                box-shadow: 0 4px 12px var(--shadow-color);
                animation: fadeIn 0.5s ease-out;
                border-left: 5px solid var(--accent-color);
                transition: background-color 0.3s ease, box-shadow 0.3s ease;
            }
            
            .weights-summary h3 {
                font-size: 1.3rem;
                margin-bottom: 16px;
                color: var(--text-primary);
                font-weight: 600;
                transition: color 0.3s ease;
            }
            
            .weights-summary-content {
                display: flex;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 20px;
            }
            
            .weight-summary-item {
                flex: 1;
                min-width: 150px;
                padding: 16px;
                background-color: var(--bg-tertiary);
                border-radius: 12px;
                text-align: center;
                transition: background-color 0.3s ease;
            }
            
            .weight-summary-label {
                font-size: 0.9rem;
                color: var(--text-tertiary);
                margin-bottom: 8px;
                transition: color 0.3s ease;
            }
            
            .weight-summary-value {
                font-size: 1.5rem;
                font-weight: 600;
                color: var(--accent-color);
                transition: color 0.3s ease;
            }
            
            /* Missing Certifications Styles */
            .missing-cert-btn {
                margin-top: 6px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 5px 10px;
                font-size: 0.8rem;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
                box-shadow: 0 2px 4px rgba(234, 88, 12, 0.2);
                margin-left: auto;
                margin-right: auto;
            }
            
            .missing-cert-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 6px rgba(234, 88, 12, 0.3);
            }
            
            .cert-badge {
                background-color: white;
                color: #ea580c;
                border-radius: 50%;
                width: 18px;
                height: 18px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-size: 0.7rem;
                font-weight: 600;
                margin-right: 5px;
            }
            
            /* Modal Styles */
            .modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
                z-index: 1000;
                overflow: auto;
                animation: fadeIn 0.3s ease-out;
            }
            
            .modal-content {
                background-color: var(--bg-card);
                margin: 5% auto;
                width: 90%;
                max-width: 800px;
                border-radius: 16px;
                box-shadow: 0 10px 25px var(--shadow-color);
                overflow: hidden;
                animation: scaleIn 0.4s ease-out;
                max-height: 90vh;
                display: flex;
                flex-direction: column;
                transition: background-color 0.3s ease;
            }
            
            .modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 20px 24px;
                background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
                color: white;
            }
            
            .modal-header h3 {
                margin: 0;
                font-size: 1.4rem;
                font-weight: 600;
            }
            
            .close-modal {
                font-size: 1.6rem;
                font-weight: 600;
                color: white;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .close-modal:hover {
                transform: rotate(90deg);
            }
            
            .modal-body {
                padding: 24px;
                max-height: 70vh;
                overflow-y: auto;
            }
            
            .cert-count {
                margin: 12px 0;
                font-size: 1rem;
                color: #4b5563;
                background-color: #f3f4f6;
                padding: 8px 16px;
                border-radius: 8px;
                display: inline-block;
            }
            
            .cert-list-container {
                max-height: 400px;
                overflow-y: auto;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            
            .cert-list {
                list-style-type: none;
                padding: 0;
                margin: 0;
            }
            
            .cert-item {
                background-color: #f9fafb;
                border-radius: 12px;
                padding: 16px;
                margin: 12px;
                border-left: 4px solid #f97316;
                animation: fadeIn 0.5s ease-out;
                display: flex;
                align-items: center;
                flex-wrap: wrap;
                position: relative;
            }
            
            .cert-number {
                position: absolute;
                top: 8px;
                right: 8px;
                background-color: #f97316;
                color: white;
                width: 24px;
                height: 24px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 0.7rem;
                font-weight: bold;
            }
            
            .cert-name {
                font-size: 1.1rem;
                font-weight: 600;
                color: #0f172a;
                margin-bottom: 8px;
            }
            
            .cert-relevance {
                font-size: 0.9rem;
                color: #4b5563;
                margin-bottom: 12px;
                line-height: 1.5;
            }
            
            .cert-link {
                display: inline-block;
                background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                color: white;
                text-decoration: none;
                padding: 8px 16px;
                border-radius: 8px;
                font-size: 0.85rem;
                font-weight: 500;
                transition: all 0.2s ease;
                box-shadow: 0 2px 4px rgba(99, 102, 241, 0.2);
            }
            
            .cert-link:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 6px rgba(99, 102, 241, 0.3);
            }
            
            .alternatives-section {
                margin-top: 24px;
                padding-top: 20px;
                border-top: 1px solid #e5e7eb;
            }
            
            .alternatives-section h4 {
                font-size: 1.1rem;
                color: #0f172a;
                margin-bottom: 16px;
                font-weight: 600;
            }
            
            .alt-cert-item {
                display: flex;
                align-items: center;
                background-color: #eef2ff;
                border-radius: 10px;
                padding: 12px;
                margin-bottom: 10px;
                transition: all 0.2s ease;
            }
            
            .alt-cert-item:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            }
            
            .alt-cert-icon {
                background-color: #6366f1;
                color: white;
                width: 28px;
                height: 28px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-right: 12px;
                font-size: 14px;
            }
            
            .alt-cert-details {
                flex: 1;
            }
            
            .alt-cert-name {
                font-weight: 500;
                color: #4f46e5;
                margin-bottom: 2px;
            }
            
            /* Missing Certifications Toggle Styles */
            .missing-certs-container {
                margin-top: 8px;
                margin-bottom: 15px;
                padding: 12px;
                background-color: #fff1f1;
                border-radius: 6px;
                border-left: 3px solid #ea580c;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                animation: fadeIn 0.3s ease-out;
            }
            
            .missing-certs-header h4 {
                margin: 0 0 8px 0;
                color: #ea580c;
                font-size: 0.95rem;
            }
            
            .missing-certs-desc {
                font-size: 0.85rem;
                margin: 0 0 10px 0;
                color: #4b5563;
            }
            
            .missing-certs-list {
                list-style-type: none;
                padding: 0;
                margin: 0;
            }
            
            .missing-cert-item {
                display: flex;
                padding: 6px 10px;
                margin-bottom: 6px;
                background-color: #ffede2;
                border-radius: 4px;
                font-size: 0.85rem;
            }
            
            .missing-cert-name {
                font-weight: 500;
                color: #ea580c;
            }
            
            .alt-cert-desc {
                font-size: 0.8rem;
                color: #6b7280;
            }

            @media (max-width: 768px) {
                .side-by-side-container {
                    flex-direction: column;
                }
                
                .candidate-details, 
                .career-insights {
                    grid-template-columns: 1fr;
                }
                
                .summary-item {
                    min-width: 80px;
                }
                
                .container {
                    padding: 20px;
                }
                
                .section-nav {
                    flex-direction: column;
                }
                
                .card {
                    padding: 24px;
                }
                
                .section-nav-buttons {
                    flex-direction: column;
                }
                
                .nav-button {
                    width: 100%;
                    margin-bottom: 10px;
                }
            }

            /* Custom styles for the Career Forecast section */
            .career-forecast-section {
                background-color: white;
                border-radius: 16px;
                padding: 24px;
                margin-bottom: 30px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            }
            
            .forecast-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }
            
            .forecast-header h3 {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 1.4rem;
                margin: 0;
                color: #1e293b;
            }
            
            .info-tooltip {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 20px;
                height: 20px;
                border-radius: 50%;
                background-color: #e0e7ff;
                color: #4f46e5;
                font-size: 0.9rem;
                cursor: help;
            }
            
            .model-info {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            
            .model-badge {
                display: flex;
                align-items: center;
                gap: 6px;
                background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
                color: white;
                padding: 6px 12px;
                border-radius: 12px;
                font-size: 0.9rem;
                font-weight: 500;
                box-shadow: 0 2px 4px rgba(99, 102, 241, 0.2);
            }
            
            .model-icon {
                font-style: normal;
            }
            
            .model-accuracy {
                display: flex;
                gap: 10px;
                font-size: 0.85rem;
            }
            
            .accuracy-item {
                display: flex;
                align-items: center;
                gap: 5px;
            }
            
            .accuracy-label {
                color: #64748b;
            }
            
            .accuracy-value {
                font-weight: 600;
                color: #0f172a;
            }
            
            .forecast-timeline {
                margin: 40px 0;
            }
            
            .timeline-year {
                display: flex;
                margin-bottom: 30px;
            }
            
            .timeline-connector {
                width: 2px;
                background-color: #cbd5e1;
                height: 50px;
                margin-left: 150px;
                position: relative;
            }
            
            .year-marker {
                width: 150px;
                flex-shrink: 0;
                position: relative;
                padding-right: 20px;
            }
            
            .year-marker::after {
                content: '';
                position: absolute;
                top: 15px;
                right: 0;
                width: 20px;
                height: 2px;
                background-color: #cbd5e1;
            }
            
            .year-marker.current::before {
                content: '';
                position: absolute;
                top: 10px;
                right: -6px;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background-color: #6366f1;
                z-index: 1;
            }
            
            .year-label {
                font-weight: 600;
                font-size: 1.1rem;
                color: #0f172a;
                margin-bottom: 10px;
            }
            
            .year-confidence {
                margin-top: 10px;
            }
            
            .confidence-bar {
                height: 6px;
                background-color: #e2e8f0;
                border-radius: 3px;
                margin-bottom: 5px;
                overflow: hidden;
            }
            
            .confidence-fill {
                height: 100%;
                background: linear-gradient(90deg, #10b981 0%, #34d399 100%);
                border-radius: 3px;
            }
            
            .confidence-value {
                font-size: 0.75rem;
                color: #64748b;
            }
            
            .prediction-card {
                flex: 1;
                background-color: #f8fafc;
                border-radius: 12px;
                padding: 20px;
                border-left: 3px solid #6366f1;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
            }
            
            .prediction-role {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }
            
            .role-title {
                font-size: 1.2rem;
                font-weight: 600;
                color: #0f172a;
            }
            
            .role-salary {
                font-size: 0.9rem;
                color: #64748b;
                font-weight: 500;
            }
            
            .alternative-roles {
                margin-bottom: 15px;
            }
            
            .alt-roles-label, .skill-gaps-label, .demand-label {
                font-size: 0.85rem;
                font-weight: 500;
                color: #64748b;
                margin-bottom: 5px;
            }
            
            .alt-roles-list {
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
            }
            
            .alt-role {
                font-size: 0.85rem;
                padding: 4px 10px;
                background-color: #f1f5f9;
                border-radius: 8px;
                color: #334155;
            }
            
            .skill-gaps-container {
                margin-bottom: 15px;
            }
            
            .skill-gaps-list {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }
            
            .skill-gap-item {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 6px 12px;
                border-radius: 8px;
                font-size: 0.85rem;
            }
            
            .skill-gap-item.high-priority {
                background-color: #fee2e2;
                color: #b91c1c;
            }
            
            .skill-gap-item.medium-priority {
                background-color: #fef9c3;
                color: #ca8a04;
            }
            
            .skill-gap-item.low-priority {
                background-color: #e0f2fe;
                color: #0284c7;
            }
            
            .gap-priority {
                font-size: 0.75rem;
                padding: 2px 6px;
                background-color: rgba(255, 255, 255, 0.5);
                border-radius: 4px;
            }
            
            .gap-resources {
                cursor: help;
            }
            
            .resource-icon {
                font-style: normal;
            }
            
            .market-demand {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .demand-gauge {
                flex: 1;
                height: 8px;
                background-color: #e2e8f0;
                border-radius: 4px;
                overflow: hidden;
            }
            
            .demand-fill {
                height: 100%;
                background: linear-gradient(90deg, #6366f1, #8b5cf6);
                border-radius: 4px;
            }
            
            .demand-value {
                font-size: 0.85rem;
                font-weight: 500;
                color: #334155;
                width: 40px;
                text-align: right;
            }
            
            .forecast-summary {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                margin-top: 30px;
                border-top: 1px solid #e2e8f0;
                padding-top: 20px;
            }
            
            .top-skills-section, .industry-alignment {
                flex: 1;
                min-width: 250px;
            }
            
            .top-skills-section h4, .industry-alignment h4 {
                font-size: 1rem;
                margin-bottom: 15px;
                color: #334155;
            }
            
            .top-skills-list {
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            
            .top-skill-item {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 0.95rem;
                color: #334155;
            }
            
            .top-skill-icon {
                font-style: normal;
            }
            
            .alignment-score {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            
            .alignment-gauge {
                flex: 1;
                height: 12px;
                background-color: #e2e8f0;
                border-radius: 6px;
                overflow: hidden;
            }
            
            .alignment-fill {
                height: 100%;
                background: linear-gradient(90deg, #10b981 0%, #34d399 100%);
                border-radius: 6px;
            }
            
            .alignment-value {
                font-size: 1.1rem;
                font-weight: 600;
                color: #10b981;
                width: 50px;
                text-align: right;
            }
            
            .forecast-explainer {
                flex-basis: 100%;
                margin-top: 20px;
                padding: 15px;
                background-color: #f8fafc;
                border-radius: 8px;
                border-left: 3px solid #6366f1;
            }
            
            .forecast-explainer p {
                font-size: 0.9rem;
                color: #475569;
                margin: 0;
            }
            
            .no-forecast {
                text-align: center;
                padding: 40px;
                color: #64748b;
                font-style: italic;
            }
            
            /* Tooltip styles */
            .tooltip {
                position: absolute;
                background-color: #1e293b;
                color: white;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 0.85rem;
                max-width: 280px;
                z-index: 1000;
                pointer-events: none;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                opacity: 0.95;
                text-align: center;
                transition: opacity 0.2s ease-in-out;
            }
            
            .tooltip::after {
                content: '';
                position: absolute;
                bottom: -5px;
                left: 50%;
                transform: translateX(-50%);
                width: 0;
                height: 0;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid #1e293b;
            }

                                .skill-badge {
                        background-color: var(--hover-color);
                        color: var(--accent-color);
                        padding: 5px 12px;
                        border-radius: 10px;
                        font-size: 0.85rem;
                        display: inline-block;
                        margin: 0 5px 5px 0;
                        box-shadow: 0 2px 4px var(--shadow-color);
                        transition: background-color 0.3s ease, color 0.3s ease, box-shadow 0.3s ease;
                    }
                    
                    .badge-success {
                        background-color: var(--success-bg);
                        color: var(--success-color);
                        transition: background-color 0.3s ease, color 0.3s ease;
                    }
                    
                    .missing-skill {
                        background-color: var(--error-bg);
                        color: var(--error-color);
                        transition: background-color 0.3s ease, color 0.3s ease;
                    }
                    
                    /* Skill seniority badges */
                    .skill-beginner {
                        background-color: #dcfce7;
                        color: #059669;
                        padding-left: 7px;
                    }
                    
                    .skill-intermediate {
                        background-color: #dbeafe;
                        color: #1d4ed8;
                        padding-left: 7px;
                    }
                    
                    .skill-advanced {
                        background-color: #f5d0fe;
                        color: #7e22ce;
                        padding-left: 7px;
                    }
                    
                    .skill-expert {
                        background-color: #ffedd5;
                        color: #c2410c;
                        padding-left: 7px;
                    }
                    
                    .seniority-icon {
                        margin-right: 5px;
                    }
                    
                    .skill-legend {
                        display: flex;
                        gap: 12px;
                        margin-top: 10px;
                        padding: 8px;
                        background-color: #f8fafc;
                        border-radius: 8px;
                        font-size: 0.8rem;
                        color: #64748b;
                    }
            
            .skill-list {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin-bottom: 15px;
            }

            /* Career Progression Analysis Styles */
            .career-progression-section {
                background-color: var(--bg-tertiary);
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 6px var(--shadow-color);
                transition: background-color 0.3s ease, box-shadow 0.3s ease;
            }
            
            .career-progression-tabs {
                display: flex;
                border-bottom: 1px solid var(--border-color);
                margin-bottom: 15px;
                transition: border-color 0.3s ease;
            }
            
            .career-tab {
                padding: 10px 15px;
                cursor: pointer;
                font-weight: 500;
                color: var(--text-tertiary);
                border-bottom: 2px solid transparent;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                gap: 6px;
            }
            
            .career-tab.active {
                color: var(--accent-color);
                border-bottom: 2px solid var(--accent-color);
            }
            
            .career-tab:hover:not(.active) {
                color: var(--text-secondary);
                background-color: var(--hover-color);
            }
        </style>
    </head>
    <body>
        <div class="theme-switch-wrapper">
            <span class="theme-icon">☀️</span>
            <label class="theme-switch">
                <input type="checkbox" id="theme-toggle">
                <span class="slider"></span>
            </label>
            <span class="theme-icon">🌙</span>
        </div>
        <h1>AI Resume Parser and Ranker</h1>
        <div class="container">
            <div class="section-nav">
                <div class="nav-item active" data-section="upload-section">
                    <div class="nav-icon">🗂</div>
                    <div class="nav-text">Upload Resumes</div>
                </div>
                <div class="nav-item" data-section="requirements-section">
                    <div class="nav-icon">🧾</div>
                    <div class="nav-text">Job Requirements</div>
                </div>
                <div class="nav-item" data-section="results-section">
                    <div class="nav-icon">📊</div>
                    <div class="nav-text">Ranking Results</div>
                </div>
            </div>

            <!-- Upload Resumes Section -->
            <section id="upload-section" class="layout-section active-section">
                <div class="card full-width-card">
                    <h2>Upload Resumes</h2>
                    <div class="section-description">
                        Upload multiple resumes (PDF or DOCX) to be analyzed and ranked. The system will extract key information and match it against job requirements.
                    </div>
                    <div class="file-upload" id="dropZone">
                        <div class="file-upload-icon">📄</div>
                        <div class="file-upload-text">Drag and drop resumes here or click to browse</div>
                        <input type="file" id="fileInput" multiple accept=".pdf,.docx">
                    </div>
                    <div class="file-count" id="fileCount">0 files selected</div>
                    <div class="file-preview" id="filePreview"></div>
                    <div class="file-list" id="fileList">No files selected</div>
                    <button onclick="uploadResumes()" class="primary-button">Upload and Parse All</button>
                    <div id="uploadResult"></div>
                    <div class="loading" id="uploadLoading">
                        <div class="loading-spinner"></div>
                        <p>Processing resumes...</p>
                    </div>
                    <div class="section-nav-buttons">
                        <button onclick="showSection('requirements-section')" class="nav-button next-button">Next →</button>
                    </div>
                </div>
            </section>
            
            <!-- Job Requirements Section -->
            <section id="requirements-section" class="layout-section">
                <div class="card full-width-card">
                    <h2>Job Requirements</h2>
                    <div class="section-description">
                        Define the job requirements to match against candidate resumes. The system will use these criteria to rank candidates and suggest alternative roles that might be a better fit for their skills.
                    </div>
                    
                    <div class="accordion">
                        <div class="accordion-item">
                            <div class="accordion-header">Basic Information</div>
                            <div class="accordion-content">
                                <div class="form-group">
                                    <label for="jobTitle">Job Title:</label>
                                    <div class="custom-dropdown">
                                        <select id="jobTitleDropdown" onchange="handleJobTitleChange()">
                                            <option value="">Select a job title</option>
                                            <option value="Software Engineer">Software Engineer</option>
                                            <option value="Full Stack Developer">Full Stack Developer</option>
                                            <option value="Backend Developer">Backend Developer</option>
                                            <option value="Frontend Developer">Frontend Developer</option>
                                            <option value="Data Scientist">Data Scientist</option>
                                            <option value="Machine Learning Engineer">Machine Learning Engineer</option>
                                            <option value="DevOps Engineer">DevOps Engineer</option>
                                            <option value="Product Manager">Product Manager</option>
                                            <option value="UI/UX Designer">UI/UX Designer</option>
                                            <option value="other">Other (specify)</option>
                                        </select>
                                    </div>
                                    <div class="other-input-container" id="jobTitleOther">
                                        <input type="text" id="jobTitle" placeholder="Enter job title">
                                    </div>
                                </div>
                                
                                <div class="form-group">
                                    <label for="experienceYears">Required Experience (years):</label>
                                    <div class="custom-dropdown">
                                        <select id="experienceYearsDropdown" onchange="handleExperienceYearsChange()">
                                            <option value="">Select experience level</option>
                                            <option value="0">Entry Level (0-1 years)</option>
                                            <option value="1">Junior (1-2 years)</option>
                                            <option value="3">Mid-Level (3-5 years)</option>
                                            <option value="5">Senior (5-8 years)</option>
                                            <option value="8">Expert (8+ years)</option>
                                            <option value="other">Other (specify)</option>
                                        </select>
                                    </div>
                                    <div class="other-input-container" id="experienceYearsOther">
                                        <input type="number" id="experienceYears" min="0" step="0.5" placeholder="Enter years of experience">
                                    </div>
                                </div>
                                
                                <div class="form-group">
                                    <label for="educationLevel">Required Education Level:</label>
                                    <div class="custom-dropdown">
                                        <select id="educationLevel" onchange="handleEducationLevelChange()">
                                            <option value="">Select education level</option>
                                            <option value="High School">High School</option>
                                            <option value="Associate's Degree">Associate's Degree</option>
                                            <option value="Bachelor's Degree">Bachelor's Degree</option>
                                            <option value="Master's Degree">Master's Degree</option>
                                            <option value="Doctorate">Doctorate</option>
                                            <option value="other">Other (specify)</option>
                                        </select>
                                    </div>
                                    <div class="other-input-container" id="educationLevelOther">
                                        <input type="text" id="educationLevelInput" placeholder="Enter education level">
                                    </div>
                                </div>
                                
                                <div class="form-group">
                                    <label for="industry">Industry:</label>
                                    <div class="custom-dropdown">
                                        <select id="industryDropdown" onchange="handleIndustryChange()">
                                            <option value="">Select industry</option>
                                            <option value="Technology">Technology</option>
                                            <option value="Finance">Finance</option>
                                            <option value="Healthcare">Healthcare</option>
                                            <option value="Education">Education</option>
                                            <option value="Manufacturing">Manufacturing</option>
                                            <option value="Retail">Retail</option>
                                            <option value="other">Other (specify)</option>
                                        </select>
                                    </div>
                                    <div class="other-input-container" id="industryOther">
                                        <input type="text" id="industry" placeholder="Enter industry">
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="accordion-item">
                            <div class="accordion-header">Scoring Configuration</div>
                            <div class="accordion-content">
                                <div class="section-description">
                                    Customize how resumes are ranked by adjusting the weight of each factor. The total must equal 100%.
                                </div>
                                
                                <div class="scoring-config">
                                    <div class="weight-item">
                                        <div class="weight-header">
                                            <label for="skillMatchWeight">Skill Match Weight</label>
                                            <div class="info-tooltip">
                                                <span class="info-icon">ⓘ</span>
                                                <span class="tooltip-text">How closely the resume matches required skills and qualifications.</span>
                                            </div>
                                            <span class="weight-percentage" id="skillMatchPercentage">40%</span>
                                        </div>
                                        <input type="range" id="skillMatchWeight" min="10" max="80" value="40" class="weight-slider" oninput="updateWeights('skillMatchWeight')">
                                    </div>
                                    
                                    <div class="weight-item">
                                        <div class="weight-header">
                                            <label for="experienceMatchWeight">Experience Match Weight</label>
                                            <div class="info-tooltip">
                                                <span class="info-icon">ⓘ</span>
                                                <span class="tooltip-text">Whether the candidate has sufficient relevant experience for the role.</span>
                                            </div>
                                            <span class="weight-percentage" id="experienceMatchPercentage">30%</span>
                                        </div>
                                        <input type="range" id="experienceMatchWeight" min="10" max="80" value="30" class="weight-slider" oninput="updateWeights('experienceMatchWeight')">
                                    </div>
                                    
                                    <div class="weight-item">
                                        <div class="weight-header">
                                            <label for="techRelevanceWeight">Technology Relevance Weight</label>
                                            <div class="info-tooltip">
                                                <span class="info-icon">ⓘ</span>
                                                <span class="tooltip-text">Whether the resume content reflects current technology trends or relevant tools and frameworks.</span>
                                            </div>
                                            <span class="weight-percentage" id="techRelevancePercentage">30%</span>
                                        </div>
                                        <input type="range" id="techRelevanceWeight" min="10" max="80" value="30" class="weight-slider" oninput="updateWeights('techRelevanceWeight')">
                                    </div>
                                    
                                    <div class="total-weight">
                                        <span>Total:</span>
                                        <span id="totalWeightPercentage">100%</span>
                                    </div>
                                    
                                    <button id="applyWeightsBtn" class="primary-button" onclick="applyWeights()">Apply Weights</button>
                                </div>
                            </div>
                        </div>
                        
                        <div class="accordion-item">
                            <div class="accordion-header">Required Skills</div>
                            <div class="accordion-content">
                                <div class="form-group">
                                    <div class="input-group">
                                        <div class="custom-dropdown">
                                            <select id="requiredSkillsDropdown" onchange="handleRequiredSkillsChange()">
                                                <option value="">Select a skill</option>
                                                <option value="Python">Python</option>
                                                <option value="JavaScript">JavaScript</option>
                                                <option value="Java">Java</option>
                                                <option value="C++">C++</option>
                                                <option value="SQL">SQL</option>
                                                <option value="React">React</option>
                                                <option value="Angular">Angular</option>
                                                <option value="Node.js">Node.js</option>
                                                <option value="Django">Django</option>
                                                <option value="Flask">Flask</option>
                                                <option value="AWS">AWS</option>
                                                <option value="Docker">Docker</option>
                                                <option value="Kubernetes">Kubernetes</option>
                                                <option value="Git">Git</option>
                                                <option value="CI/CD">CI/CD</option>
                                                <option value="other">Other (specify)</option>
                                            </select>
                                        </div>
                                        <button onclick="addRequiredSkill()" class="input-button">Add Skill</button>
                                    </div>
                                    <div class="other-input-container" id="requiredSkillsOther">
                                        <div class="input-group">
                                            <input type="text" id="requiredSkillsInput" placeholder="Enter skill">
                                            <button onclick="addCustomRequiredSkill()" class="input-button">Add</button>
                                        </div>
                                    </div>
                                    <div class="skill-tags-container" id="requiredSkillsTags"></div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="accordion-item">
                            <div class="accordion-header">Preferred Skills (Optional)</div>
                            <div class="accordion-content">
                                <div class="form-group">
                                    <div class="input-group">
                                        <div class="custom-dropdown">
                                            <select id="preferredSkillsDropdown" onchange="handlePreferredSkillsChange()">
                                                <option value="">Select a skill</option>
                                                <option value="Python">Python</option>
                                                <option value="JavaScript">JavaScript</option>
                                                <option value="Java">Java</option>
                                                <option value="C++">C++</option>
                                                <option value="SQL">SQL</option>
                                                <option value="React">React</option>
                                                <option value="Angular">Angular</option>
                                                <option value="Node.js">Node.js</option>
                                                <option value="Django">Django</option>
                                                <option value="Flask">Flask</option>
                                                <option value="AWS">AWS</option>
                                                <option value="Docker">Docker</option>
                                                <option value="Kubernetes">Kubernetes</option>
                                                <option value="Git">Git</option>
                                                <option value="CI/CD">CI/CD</option>
                                                <option value="other">Other (specify)</option>
                                            </select>
                                        </div>
                                        <button onclick="addPreferredSkill()" class="input-button">Add Skill</button>
                                    </div>
                                    <div class="other-input-container" id="preferredSkillsOther">
                                        <div class="input-group">
                                            <input type="text" id="preferredSkillsInput" placeholder="Enter skill">
                                            <button onclick="addCustomPreferredSkill()" class="input-button">Add</button>
                                        </div>
                                    </div>
                                    <div class="skill-tags-container" id="preferredSkillsTags"></div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="accordion-item">
                            <div class="accordion-header">Keywords</div>
                            <div class="accordion-content">
                                <div class="form-group">
                                    <div class="input-group">
                                        <div class="custom-dropdown">
                                            <select id="keywordsDropdown" onchange="handleKeywordsChange()">
                                                <option value="">Select a keyword</option>
                                                <option value="backend">Backend</option>
                                                <option value="frontend">Frontend</option>
                                                <option value="fullstack">Fullstack</option>
                                                <option value="web development">Web Development</option>
                                                <option value="mobile development">Mobile Development</option>
                                                <option value="api">API</option>
                                                <option value="database">Database</option>
                                                <option value="cloud">Cloud</option>
                                                <option value="security">Security</option>
                                                <option value="testing">Testing</option>
                                                <option value="other">Other (specify)</option>
                                            </select>
                                        </div>
                                        <button onclick="addKeyword()" class="input-button">Add Keyword</button>
                                    </div>
                                    <div class="other-input-container" id="keywordsOther">
                                        <div class="input-group">
                                            <input type="text" id="keywordsInput" placeholder="Enter keyword">
                                            <button onclick="addCustomKeyword()" class="input-button">Add</button>
                                        </div>
                                    </div>
                                    <div class="skill-tags-container" id="keywordsTags"></div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="accordion-item">
                            <div class="accordion-header">Certifications</div>
                            <div class="accordion-content">
                                <div class="form-group">
                                    <div class="input-group">
                                        <input type="text" id="certificationsInput" placeholder="Add certification (e.g., AWS, PMP)">
                                        <button type="button" onclick="addSkillTag(document.getElementById('certificationsInput').value, 'certificationsTags', certifications)" class="input-button">Add</button>
                                    </div>
                                    <div id="certificationsTags" class="tags-container"></div>
                                    <button type="button" onclick="suggestCertifications(document.getElementById('jobTitle').value)" class="suggest-btn">Suggest Relevant Certifications</button>
                                    <div class="section-description">
                                        Add industry-recognized certifications that are relevant to the job. The system will prioritize 
                                        certifications like AWS, PMP, Google Analytics, etc.
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="accordion-item">
                            <div class="accordion-header">Company Values / Culture</div>
                            <div class="accordion-content">
                                <div class="form-group">
                                    <div class="input-group">
                                        <input type="text" id="companyValuesInput" placeholder="Add company value (e.g., innovation, teamwork)">
                                        <button type="button" onclick="addSkillTag(document.getElementById('companyValuesInput').value, 'companyValuesTags', companyValues)" class="input-button">Add</button>
                                    </div>
                                    <div id="companyValuesTags" class="tags-container"></div>
                                    <button type="button" onclick="suggestCompanyValues(document.getElementById('industryDropdown').value)" class="suggest-btn">Suggest Company Values</button>
                                    <div class="section-description">
                                        Add company values or cultural aspects that candidates should align with. The system will analyze how well 
                                        the resume's tone and content matches these values.
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <button onclick="setDefaultOptions()" class="default-options-btn">Add Default Options</button>
                    <button onclick="analyzeResumes()" class="primary-button">Rank Resumes</button>
                    <div class="loading" id="analysisLoading">
                        <div class="loading-spinner"></div>
                        <p>Analyzing and ranking resumes...</p>
                    </div>
                    
                    <div class="section-nav-buttons">
                        <button onclick="showSection('upload-section')" class="nav-button prev-button">← Back</button>
                        <button onclick="showSection('results-section')" class="nav-button next-button">Next →</button>
                    </div>
                </div>
            </section>
            
            <!-- Ranking Results Section -->
            <section id="results-section" class="layout-section">
                <div class="card full-width-card">
                    <h2>Ranking Results</h2>
                    <div class="section-description">
                        View the ranked results of your candidate resumes. They are scored based on the job requirements you provided.
                    </div>
                    <div id="analysisResult" class="ranking-results"></div>
                    
                    <div class="section-nav-buttons">
                        <button onclick="showSection('requirements-section')" class="nav-button prev-button">← Back</button>
                    </div>
                </div>
            </section>
        </div>

        <script>
            // Theme switcher functionality
            document.addEventListener('DOMContentLoaded', function() {
                const themeToggle = document.getElementById('theme-toggle');
                const currentTheme = localStorage.getItem('theme') || 'light';
                
                // Set initial theme based on user preference
                if (currentTheme === 'dark') {
                    document.documentElement.setAttribute('data-theme', 'dark');
                    themeToggle.checked = true;
                }
                
                // Handle theme toggle
                themeToggle.addEventListener('change', function() {
                    if (this.checked) {
                        document.documentElement.setAttribute('data-theme', 'dark');
                        localStorage.setItem('theme', 'dark');
                    } else {
                        document.documentElement.removeAttribute('data-theme');
                        localStorage.setItem('theme', 'light');
                    }
                });
            });
            
            let parsedResumes = [];
            let selectedFiles = [];
            let requiredSkills = [];
            let preferredSkills = [];
            let keywords = [];
            let certifications = [];
            let companyValues = [];
            let missingCertificationsData = []; // Store missing certifications for all candidates
            
            // Certification details functions
            function toggleCertDetails(detailsId) {
                const detailsElement = document.getElementById(detailsId);
                const buttonElement = event.currentTarget;
                const iconElement = buttonElement.querySelector('.toggle-icon');
                
                if (detailsElement.style.display === 'none') {
                    detailsElement.style.display = 'block';
                    iconElement.style.transform = 'rotate(180deg)';
                    buttonElement.innerHTML = 'Hide Details <span class="toggle-icon" style="transform: rotate(180deg);">▼</span>';
                } else {
                    detailsElement.style.display = 'none';
                    iconElement.style.transform = 'rotate(0deg)';
                    buttonElement.innerHTML = 'Show Details <span class="toggle-icon">▼</span>';
                }
            }
            
            // Get certification description based on the certification name and job title
            function getCertDescription(certName, jobTitle) {
                // Database of certification descriptions
                const certDescriptions = {
                    // AWS Certifications
                    "AWS Certified Solutions Architect": "Validates expertise in designing distributed systems on AWS",
                    "AWS Certified Developer": "Validates expertise in developing applications for AWS",
                    "AWS Certified DevOps Engineer": "Validates expertise in implementing DevOps practices on AWS",
                    
                    // Google Certifications
                    "Google Data Analytics": "Validates skills in data analysis using Google tools",
                    "Google Cloud Professional": "Validates expertise in Google Cloud Platform",
                    
                    // Microsoft Certifications
                    "Microsoft Azure Fundamentals": "Validates foundational knowledge of Azure services",
                    "Microsoft Azure Administrator": "Validates skills in implementing Azure infrastructure",
                    
                    // Project Management
                    "PMP": "Project Management Professional certification by PMI",
                    "PRINCE2": "PRojects IN Controlled Environments methodology certification",
                    "Scrum Master": "Validates expertise in the Scrum framework for Agile development",
                    
                    // Default for unknown certifications
                    "default": "Industry-recognized certification relevant to job requirements"
                };
                
                // Return the description if it exists, otherwise return the default
                return certDescriptions[certName] || certDescriptions["default"];
            }
            
            // Get certification relevance based on the certification name and job title
            function getCertRelevance(certName, jobTitle) {
                // Map job titles to relevant certifications with explanations
                const jobCertRelevance = {
                    "Software Engineer": {
                        "AWS Certified Developer": "Essential for cloud development which is a core requirement for modern software engineering",
                        "Scrum Master": "Important for Agile development practices used in most software teams",
                        "default": "Provides specialized knowledge relevant to software engineering practices"
                    },
                    "Data Scientist": {
                        "Google Data Analytics": "Directly applicable to data analysis workflows",
                        "IBM Data Science Professional": "Comprehensive training for data science methodologies",
                        "default": "Enhances data analysis capabilities required for the role"
                    },
                    "DevOps Engineer": {
                        "AWS Certified DevOps Engineer": "Directly applicable to AWS-based DevOps workflows",
                        "Docker Certified Associate": "Essential for containerization expertise",
                        "Kubernetes Administrator": "Critical for container orchestration in production environments",
                        "default": "Improves infrastructure management capabilities required for DevOps"
                    },
                    "default": {
                        "default": "Provides specialized knowledge valuable in this field"
                    }
                };
                
                // Get job-specific relevance map or default
                const relevanceMap = jobCertRelevance[jobTitle] || jobCertRelevance["default"];
                
                // Return the relevance explanation if it exists, otherwise return the default
                return relevanceMap[certName] || relevanceMap["default"];
            }
            
            // Get certification learning link based on certification name
            function getCertLink(certName) {
                // Database of certification links
                const certLinks = {
                    // AWS Certifications
                    "AWS Certified Solutions Architect": "https://aws.amazon.com/certification/certified-solutions-architect-associate/",
                    "AWS Certified Developer": "https://aws.amazon.com/certification/certified-developer-associate/",
                    "AWS Certified DevOps Engineer": "https://aws.amazon.com/certification/certified-devops-engineer-professional/",
                    
                    // Google Certifications
                    "Google Data Analytics": "https://grow.google/certificates/data-analytics/",
                    "Google Cloud Professional": "https://cloud.google.com/certification",
                    
                    // Microsoft Certifications
                    "Microsoft Azure Fundamentals": "https://learn.microsoft.com/en-us/certifications/azure-fundamentals/",
                    "Microsoft Azure Administrator": "https://learn.microsoft.com/en-us/certifications/azure-administrator/",
                    
                    // Project Management
                    "PMP": "https://www.pmi.org/certifications/project-management-pmp",
                    "PRINCE2": "https://www.axelos.com/certifications/propath/prince2",
                    "Scrum Master": "https://www.scrum.org/professional-scrum-certifications",
                    
                    // Default link for unknown certifications
                    "default": "https://www.coursera.org/search?query=" + encodeURIComponent(certName)
                };
                
                // Return the link if it exists, otherwise return a search link
                return certLinks[certName] || certLinks["default"];
            }
            
            // Dropdown handlers
            function handleJobTitleChange() {
                const dropdown = document.getElementById('jobTitleDropdown');
                const otherContainer = document.getElementById('jobTitleOther');
                const input = document.getElementById('jobTitle');
                
                if (dropdown.value === 'other') {
                    otherContainer.classList.add('active');
                    input.focus();
                } else {
                    otherContainer.classList.remove('active');
                    input.value = dropdown.value;
                    
                    // Suggest relevant certifications based on the new job title
                    suggestCertifications(dropdown.value);
                }
            }
            
            function suggestCompanyValues(industry) {
                // Define industry-specific company values
                const valuesByIndustry = {
                    'Technology': [
                        'innovation', 
                        'teamwork', 
                        'excellence', 
                        'customer focus', 
                        'integrity',
                        'diversity',
                        'continuous learning'
                    ],
                    'Finance': [
                        'integrity', 
                        'client focus', 
                        'excellence', 
                        'ethics', 
                        'teamwork',
                        'accountability',
                        'risk management'
                    ],
                    'Healthcare': [
                        'patient care', 
                        'innovation', 
                        'ethics', 
                        'quality', 
                        'teamwork',
                        'compassion',
                        'continuous improvement'
                    ],
                    'Manufacturing': [
                        'quality',
                        'safety',
                        'efficiency',
                        'teamwork',
                        'innovation',
                        'sustainability',
                        'continuous improvement'
                    ],
                    'Retail': [
                        'customer satisfaction',
                        'teamwork',
                        'integrity',
                        'diversity',
                        'innovation',
                        'adaptability',
                        'community'
                    ],
                    'Education': [
                        'student success',
                        'integrity',
                        'innovation',
                        'teamwork',
                        'diversity',
                        'excellence',
                        'life-long learning'
                    ],
                    'Default': [
                        'innovation', 
                        'teamwork', 
                        'integrity', 
                        'customer focus', 
                        'excellence'
                    ]
                };
                
                // Clear previous values
                document.getElementById('companyValuesTags').innerHTML = '';
                companyValues = [];
                
                // Get values for this industry, or default if not found
                let suggestedValues = valuesByIndustry[industry] || valuesByIndustry['Default'];
                
                // Add the suggested values to the UI and array
                suggestedValues.forEach(value => {
                    addSkillTag(value, 'companyValuesTags', companyValues);
                });
                
                // Show success message
                const successMsg = document.createElement('div');
                successMsg.style.color = 'green';
                successMsg.style.marginTop = '10px';
                successMsg.textContent = 'Added company values for ' + (industry || 'this industry');
                document.getElementById('companyValuesTags').after(successMsg);
                
                // Remove success message after 3 seconds
                setTimeout(() => {
                    successMsg.remove();
                }, 3000);
            }
            
            function suggestCertifications(jobTitle) {
                // Define job-specific certification sets (same as in setDefaultOptions)
                const certificationsByJob = {
                    'Software Engineer': [
                        'AWS Certified Developer', 
                        'Scrum Master',
                        'Docker Certified Associate',
                        'Oracle Certified Java Programmer',
                        'Microsoft Certified: Azure Developer Associate'
                    ],
                    'Full Stack Developer': [
                        'AWS Certified Developer',
                        'MongoDB Certified Developer Associate',
                        'React Developer Certification',
                        'Node.js Certification',
                        'Microsoft Certified: Azure Developer Associate'
                    ],
                    'Data Scientist': [
                        'Google Data Analytics',
                        'IBM Data Science Professional',
                        'Microsoft Certified: Data Analyst Associate',
                        'Cloudera Certified Professional Data Scientist',
                        'TensorFlow Developer Certificate'
                    ],
                    'DevOps Engineer': [
                        'AWS Certified DevOps Engineer',
                        'Docker Certified Associate',
                        'Kubernetes Administrator',
                        'Terraform Associate',
                        'Red Hat Certified Engineer (RHCE)'
                    ],
                    'Product Manager': [
                        'PMP',
                        'Scrum Master',
                        'Agile Certified Practitioner',
                        'PRINCE2',
                        'Product Owner Certification'
                    ],
                    'UI/UX Designer': [
                        'Adobe Certified Expert',
                        'Certified User Experience Professional',
                        'Google UX Design Certificate',
                        'Interaction Design Foundation Certification',
                        'Sketch Certified'
                    ]
                };
                
                // Get certifications for this job title, or default if not found
                let suggestedCerts = certificationsByJob[jobTitle] || [
                    'AWS Certified Developer', 
                    'Scrum Master',
                    'Google Data Analytics',
                    'CompTIA Security+',
                    'PMP'
                ];
                
                // Don't automatically add certs, but show a suggestion dialog
                const certSuggestionDiv = document.createElement('div');
                certSuggestionDiv.className = 'cert-suggestion';
                certSuggestionDiv.style.marginTop = '10px';
                certSuggestionDiv.style.padding = '10px';
                certSuggestionDiv.style.backgroundColor = '#f1f8ff';
                certSuggestionDiv.style.borderRadius = '5px';
                certSuggestionDiv.style.borderLeft = '4px solid #3498db';
                
                certSuggestionDiv.innerHTML = `
                    <p><strong>Suggested certifications for ${jobTitle}:</strong></p>
                    <div class="suggested-certs-container">
                        ${suggestedCerts.map(cert => 
                            `<div class="suggested-cert">
                                <span>${cert}</span>
                                <button class="add-cert-btn" onclick="addSuggestedCert('${cert}')">Add</button>
                            </div>`
                        ).join('')}
                    </div>
                `;
                
                // Find the certifications section to append suggestions
                const certSection = document.getElementById('certificationsTags').parentNode;
                
                // Remove any existing suggestion
                const existingSuggestion = certSection.querySelector('.cert-suggestion');
                if (existingSuggestion) {
                    existingSuggestion.remove();
                }
                
                // Add the new suggestion
                certSection.appendChild(certSuggestionDiv);
                
                // Add some styles for the suggestion display
                const style = document.createElement('style');
                style.textContent = `
                    .suggested-certs-container {
                        display: flex;
                        flex-wrap: wrap;
                        gap: 8px;
                        margin-top: 8px;
                    }
                    .suggested-cert {
                        display: flex;
                        align-items: center;
                        background-color: white;
                        padding: 5px 10px;
                        border-radius: 4px;
                        border: 1px solid #e0e0e0;
                    }
                    .add-cert-btn {
                        background-color: #3498db;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        padding: 2px 6px;
                        margin-left: 8px;
                        cursor: pointer;
                        font-size: 12px;
                    }
                    .add-cert-btn:hover {
                        background-color: #2980b9;
                    }
                `;
                document.head.appendChild(style);
            }
            
            function addSuggestedCert(cert) {
                // Add the certification to the list
                addSkillTag(cert, 'certificationsTags', certifications);
                
                // Find and remove the suggestions after adding one cert
                const certSuggestion = document.querySelector('.cert-suggestion');
                if (certSuggestion) {
                    certSuggestion.remove();
                }
            }
            
            function handleRequiredSkillsChange() {
                const dropdown = document.getElementById('requiredSkillsDropdown');
                const otherContainer = document.getElementById('requiredSkillsOther');
                
                if (dropdown.value === 'other') {
                    otherContainer.classList.add('active');
                    document.getElementById('requiredSkillsInput').focus();
                } else {
                    otherContainer.classList.remove('active');
                }
            }
            
            function handlePreferredSkillsChange() {
                const dropdown = document.getElementById('preferredSkillsDropdown');
                const otherContainer = document.getElementById('preferredSkillsOther');
                
                if (dropdown.value === 'other') {
                    otherContainer.classList.add('active');
                    document.getElementById('preferredSkillsInput').focus();
                } else {
                    otherContainer.classList.remove('active');
                }
            }
            
            function handleExperienceYearsChange() {
                const dropdown = document.getElementById('experienceYearsDropdown');
                const otherContainer = document.getElementById('experienceYearsOther');
                const input = document.getElementById('experienceYears');
                
                if (dropdown.value === 'other') {
                    otherContainer.classList.add('active');
                    input.focus();
                } else {
                    otherContainer.classList.remove('active');
                    input.value = dropdown.value;
                }
            }
            
            function handleEducationLevelChange() {
                const dropdown = document.getElementById('educationLevel');
                const otherContainer = document.getElementById('educationLevelOther');
                const input = document.getElementById('educationLevelInput');
                
                if (dropdown.value === 'other') {
                    otherContainer.classList.add('active');
                    input.focus();
                } else {
                    otherContainer.classList.remove('active');
                    input.value = dropdown.value;
                }
            }
            
            function handleIndustryChange() {
                const dropdown = document.getElementById('industryDropdown');
                const otherContainer = document.getElementById('industryOther');
                const input = document.getElementById('industry');
                
                if (dropdown.value === 'other') {
                    otherContainer.classList.add('active');
                    input.focus();
                } else {
                    otherContainer.classList.remove('active');
                    input.value = dropdown.value;
                }
            }
            
            function handleKeywordsChange() {
                const dropdown = document.getElementById('keywordsDropdown');
                const otherContainer = document.getElementById('keywordsOther');
                
                if (dropdown.value === 'other') {
                    otherContainer.classList.add('active');
                    document.getElementById('keywordsInput').focus();
                } else {
                    otherContainer.classList.remove('active');
                }
            }
            
            // Skill tag functions
            function addRequiredSkill() {
                const dropdown = document.getElementById('requiredSkillsDropdown');
                if (dropdown.value && dropdown.value !== 'other') {
                    addSkillTag(dropdown.value, 'requiredSkillsTags', requiredSkills);
                    dropdown.value = '';
                }
            }
            
            function addCustomRequiredSkill() {
                const input = document.getElementById('requiredSkillsInput');
                const value = input.value.trim();
                
                if (value) {
                    addSkillTag(value, 'requiredSkillsTags', requiredSkills);
                    input.value = '';
                    document.getElementById('requiredSkillsOther').classList.remove('active');
                    document.getElementById('requiredSkillsDropdown').value = '';
                }
            }
            
            function addPreferredSkill() {
                const dropdown = document.getElementById('preferredSkillsDropdown');
                if (dropdown.value && dropdown.value !== 'other') {
                    addSkillTag(dropdown.value, 'preferredSkillsTags', preferredSkills);
                    dropdown.value = '';
                }
            }
            
            function addCustomPreferredSkill() {
                const input = document.getElementById('preferredSkillsInput');
                const value = input.value.trim();
                
                if (value) {
                    addSkillTag(value, 'preferredSkillsTags', preferredSkills);
                    input.value = '';
                    document.getElementById('preferredSkillsOther').classList.remove('active');
                    document.getElementById('preferredSkillsDropdown').value = '';
                }
            }
            
            function addKeyword() {
                const dropdown = document.getElementById('keywordsDropdown');
                if (dropdown.value && dropdown.value !== 'other') {
                    addSkillTag(dropdown.value, 'keywordsTags', keywords);
                    dropdown.value = '';
                }
            }
            
            function addCustomKeyword() {
                const input = document.getElementById('keywordsInput');
                const value = input.value.trim();
                
                if (value) {
                    addSkillTag(value, 'keywordsTags', keywords);
                    input.value = '';
                    document.getElementById('keywordsOther').classList.remove('active');
                    document.getElementById('keywordsDropdown').value = '';
                }
            }
            
            function addSkillTag(skill, containerId, array) {
                if (!array.includes(skill)) {
                    array.push(skill);
                    updateSkillTags(containerId, array);
                }
            }
            
            function removeSkillTag(index, containerId) {
                // Make sure we're using the correct array based on the containerId
                if (containerId === 'requiredSkillsTags') {
                    requiredSkills.splice(index, 1);
                    updateSkillTags(containerId, requiredSkills);
                } else if (containerId === 'preferredSkillsTags') {
                    preferredSkills.splice(index, 1);
                    updateSkillTags(containerId, preferredSkills);
                } else if (containerId === 'certificationsTags') {
                    certifications.splice(index, 1);
                    updateSkillTags(containerId, certifications);
                } else if (containerId === 'keywordsTags') {
                    keywords.splice(index, 1);
                    updateSkillTags(containerId, keywords);
                } else if (containerId === 'companyValuesTags') {
                    companyValues.splice(index, 1);
                    updateSkillTags(containerId, companyValues);
                }
            }
            
            function updateSkillTags(containerId, array) {
                const container = document.getElementById(containerId);
                container.innerHTML = '';
                
                array.forEach((skill, index) => {
                    const tag = document.createElement('div');
                    tag.className = 'skill-tag';
                    tag.innerHTML = `
                        ${skill}
                        <span class="remove-skill" onclick="removeSkillTag(${index}, '${containerId}')">×</span>
                    `;
                    container.appendChild(tag);
                });
            }
            
            // Drag and drop functionality
            const dropZone = document.getElementById('dropZone');
            const fileInput = document.getElementById('fileInput');
            const filePreview = document.getElementById('filePreview');
            
            // Prevent default drag behaviors
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, preventDefaults, false);
                document.body.addEventListener(eventName, preventDefaults, false);
            });
            
            // Highlight drop zone when item is dragged over it
            ['dragenter', 'dragover'].forEach(eventName => {
                dropZone.addEventListener(eventName, highlight, false);
            });
            
            ['dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, unhighlight, false);
            });
            
            // Handle dropped files
            dropZone.addEventListener('drop', handleDrop, false);
            
            // Handle click to browse
            dropZone.addEventListener('click', () => {
                fileInput.click();
            });
            
            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            function highlight() {
                dropZone.classList.add('dragover');
            }
            
            function unhighlight() {
                dropZone.classList.remove('dragover');
            }
            
            function handleDrop(e) {
                const dt = e.dataTransfer;
                const files = dt.files;
                
                handleFiles(files);
            }
            
            // Handle file selection
            document.getElementById('fileInput').addEventListener('change', function(e) {
                handleFiles(e.target.files);
            });
            
            function handleFiles(files) {
                const fileArray = Array.from(files);
                
                // Check if we're adding to existing files or replacing them
                if (selectedFiles.length > 0 && !confirm('Do you want to add these files to the existing selection?')) {
                    selectedFiles = [];
                }
                
                // Add new files to the selection
                selectedFiles = [...selectedFiles, ...fileArray];
                
                // Limit to 20 files
                if (selectedFiles.length > 20) {
                    alert('Maximum 20 files allowed. Only the first 20 will be kept.');
                    selectedFiles = selectedFiles.slice(0, 20);
                }
                
                updateFileList();
                updateFilePreview();
            }
            
            function updateFilePreview() {
                filePreview.innerHTML = '';
                
                selectedFiles.forEach((file, index) => {
                    const fileItem = document.createElement('div');
                    fileItem.className = 'file-item';
                    
                    // Determine file icon based on extension
                    let fileIcon = '📄';
                    if (file.name.endsWith('.pdf')) {
                        fileIcon = '📕';
                    } else if (file.name.endsWith('.docx')) {
                        fileIcon = '📘';
                    }
                    
                    fileItem.innerHTML = `
                        <div class="file-name">${file.name}</div>
                        <span class="remove-file" onclick="removeFile(${index})">×</span>
                    `;
                    
                    filePreview.appendChild(fileItem);
                });
            }
            
            function updateFileList() {
                const fileList = document.getElementById('fileList');
                fileList.innerHTML = '';
                
                if (selectedFiles.length === 0) {
                    fileList.innerHTML = '<div class="file-item">No files selected</div>';
                    document.getElementById('fileCount').textContent = '0 files selected';
                    return;
                }
                
                document.getElementById('fileCount').textContent = `${selectedFiles.length} file(s) selected`;
                
                selectedFiles.forEach((file, index) => {
                    const fileItem = document.createElement('div');
                    fileItem.className = 'file-item';
                    fileItem.innerHTML = `
                        <div class="file-name">${file.name}</div>
                        <span class="remove-file" onclick="removeFile(${index})">×</span>
                    `;
                    fileList.appendChild(fileItem);
                });
                
                // Update the file input to reflect the current selection
                const dataTransfer = new DataTransfer();
                selectedFiles.forEach(file => dataTransfer.items.add(file));
                document.getElementById('fileInput').files = dataTransfer.files;
            }
            
            function removeFile(index) {
                selectedFiles.splice(index, 1);
                updateFileList();
                updateFilePreview();
            }
            
            // Section navigation
            function showSection(sectionId) {
                console.log('Showing section:', sectionId);
                
                // Hide all sections
                document.querySelectorAll('.layout-section').forEach(section => {
                    section.classList.remove('active-section');
                });
                
                // Show selected section
                const targetSection = document.getElementById(sectionId);
                if (targetSection) {
                    targetSection.classList.add('active-section');
                    console.log('Section activated:', sectionId);
                } else {
                    console.error('Section not found:', sectionId);
                }
                
                // Update navigation
                updateNavigation(sectionId);
                
                // Scroll to top of page
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            }

            // Initialize all sections and navigation on page load
            document.addEventListener('DOMContentLoaded', function() {
                // Initialize tooltips
                if (window.initializeTooltips) {
                    window.initializeTooltips();
                }
                
                // Set up accordion functionality
                const accordionItems = document.querySelectorAll('.accordion-item');
                
                // Make the first accordion item active by default
                if (accordionItems.length > 0) {
                    accordionItems[0].classList.add('active');
                }
                
                accordionItems.forEach(item => {
                    const header = item.querySelector('.accordion-header');
                    header.addEventListener('click', () => {
                        // Toggle the current item
                        item.classList.toggle('active');
                    });
                });
                
                // Set up section navigation
                const navItems = document.querySelectorAll('.nav-item');
                navItems.forEach(item => {
                    item.addEventListener('click', () => {
                        const sectionId = item.dataset.section;
                        showSection(sectionId);
                    });
                });
                
                // Initialize sections - make sure only the upload section is active initially
                document.querySelectorAll('.layout-section').forEach(section => {
                    section.classList.remove('active-section');
                });
                document.getElementById('upload-section').classList.add('active-section');
                
                // Update the navigation indicators
                updateNavigation('upload-section');
                
                // Initialize weights
                initializeWeights();
            });
            
            // Scoring Configuration Functions
            let scoreWeights = {
                skillMatch: 40,
                experienceMatch: 30,
                techRelevance: 30
            };
            
            let weightsChanged = false;
            
            function initializeWeights() {
                // Set initial slider values
                document.getElementById('skillMatchWeight').value = scoreWeights.skillMatch;
                document.getElementById('experienceMatchWeight').value = scoreWeights.experienceMatch;
                document.getElementById('techRelevanceWeight').value = scoreWeights.techRelevance;
                
                // Set initial percentage displays
                document.getElementById('skillMatchPercentage').textContent = `${scoreWeights.skillMatch}%`;
                document.getElementById('experienceMatchPercentage').textContent = `${scoreWeights.experienceMatch}%`;
                document.getElementById('techRelevancePercentage').textContent = `${scoreWeights.techRelevance}%`;
                
                // Initialize total display
                document.getElementById('totalWeightPercentage').textContent = '100%';
            }
            
            function updateWeights(changedSliderId) {
                const skillSlider = document.getElementById('skillMatchWeight');
                const expSlider = document.getElementById('experienceMatchWeight');
                const techSlider = document.getElementById('techRelevanceWeight');
                
                // Get the changed value
                const changedValue = parseInt(document.getElementById(changedSliderId).value);
                
                if (changedSliderId === 'skillMatchWeight') {
                    scoreWeights.skillMatch = changedValue;
                    
                    // Adjust other weights proportionally to maintain total of 100%
                    const remainingWeight = 100 - changedValue;
                    const expTechRatio = scoreWeights.experienceMatch / (scoreWeights.experienceMatch + scoreWeights.techRelevance);
                    
                    scoreWeights.experienceMatch = Math.round(remainingWeight * expTechRatio);
                    scoreWeights.techRelevance = remainingWeight - scoreWeights.experienceMatch;
                    
                    // Update other sliders
                    expSlider.value = scoreWeights.experienceMatch;
                    techSlider.value = scoreWeights.techRelevance;
                    
                } else if (changedSliderId === 'experienceMatchWeight') {
                    scoreWeights.experienceMatch = changedValue;
                    
                    // Adjust other weights proportionally to maintain total of 100%
                    const remainingWeight = 100 - changedValue;
                    const skillTechRatio = scoreWeights.skillMatch / (scoreWeights.skillMatch + scoreWeights.techRelevance);
                    
                    scoreWeights.skillMatch = Math.round(remainingWeight * skillTechRatio);
                    scoreWeights.techRelevance = remainingWeight - scoreWeights.skillMatch;
                    
                    // Update other sliders
                    skillSlider.value = scoreWeights.skillMatch;
                    techSlider.value = scoreWeights.techRelevance;
                    
                } else if (changedSliderId === 'techRelevanceWeight') {
                    scoreWeights.techRelevance = changedValue;
                    
                    // Adjust other weights proportionally to maintain total of 100%
                    const remainingWeight = 100 - changedValue;
                    const skillExpRatio = scoreWeights.skillMatch / (scoreWeights.skillMatch + scoreWeights.experienceMatch);
                    
                    scoreWeights.skillMatch = Math.round(remainingWeight * skillExpRatio);
                    scoreWeights.experienceMatch = remainingWeight - scoreWeights.skillMatch;
                    
                    // Update other sliders
                    skillSlider.value = scoreWeights.skillMatch;
                    expSlider.value = scoreWeights.experienceMatch;
                }
                
                // Update percentage displays
                document.getElementById('skillMatchPercentage').textContent = `${scoreWeights.skillMatch}%`;
                document.getElementById('experienceMatchPercentage').textContent = `${scoreWeights.experienceMatch}%`;
                document.getElementById('techRelevancePercentage').textContent = `${scoreWeights.techRelevance}%`;
                
                // Check if total is 100%
                const total = scoreWeights.skillMatch + scoreWeights.experienceMatch + scoreWeights.techRelevance;
                const totalElement = document.getElementById('totalWeightPercentage');
                totalElement.textContent = `${total}%`;
                
                if (total !== 100) {
                    totalElement.classList.add('error');
                } else {
                    totalElement.classList.remove('error');
                }
                
                // Mark that weights have been changed but not yet applied
                weightsChanged = true;
                updateApplyButton();
            }
            
            function updateApplyButton() {
                const applyBtn = document.getElementById('applyWeightsBtn');
                if (weightsChanged) {
                    applyBtn.textContent = 'Apply Weights';
                    applyBtn.style.backgroundColor = '';
                    applyBtn.disabled = false;
                } else {
                    applyBtn.textContent = 'Weights Applied';
                    applyBtn.style.backgroundColor = '#10b981';
                    applyBtn.disabled = true;
                    
                    // Reset after 3 seconds
                    setTimeout(() => {
                        applyBtn.textContent = 'Apply Weights';
                        applyBtn.style.backgroundColor = '';
                        applyBtn.disabled = false;
                    }, 3000);
                }
            }
            
            function applyWeights() {
                // Check if total is 100%
                const total = scoreWeights.skillMatch + scoreWeights.experienceMatch + scoreWeights.techRelevance;
                
                if (total !== 100) {
                    alert('Total weight must equal 100%. Please adjust the weights.');
                    return;
                }
                
                // If we have results already, recalculate them with new weights
                if (parsedResumes.length > 0 && document.getElementById('analysisResult').innerHTML !== '') {
                    analyzeResumes();
                }
                
                weightsChanged = false;
                updateApplyButton();
            }

            // Function to update navigation indicators
            function updateNavigation(activeSectionId) {
                document.querySelectorAll('.nav-item').forEach(item => {
                    item.classList.remove('active');
                    if (item.dataset.section === activeSectionId) {
                        item.classList.add('active');
                    }
                });
            }

            // Modified uploadResumes function to update file status indicators
            async function uploadResumes() {
                if (selectedFiles.length === 0) {
                    alert('Please select at least one file');
                    return;
                }
                
                if (selectedFiles.length > 20) {
                    alert('Maximum 20 files allowed');
                    return;
                }
                
                document.getElementById('uploadLoading').style.display = 'block';
                document.getElementById('uploadResult').innerHTML = '';
                parsedResumes = [];
                
                let successCount = 0;
                let errorCount = 0;
                let errorDetails = [];
                
                try {
                    // First, update the UI to show "Uploading..." status for all files
                    const fileList = document.getElementById('fileList');
                    fileList.innerHTML = '';
                    
                    selectedFiles.forEach((file, index) => {
                        const fileItem = document.createElement('div');
                        fileItem.className = 'file-item';
                        fileItem.id = `file-item-${index}`;
                        fileItem.innerHTML = `
                            <div class="file-name">${file.name}</div>
                            <div class="file-status" id="file-status-${index}">Uploading...</div>
                            <span class="remove-file" onclick="removeFile(${index})">×</span>
                        `;
                        fileList.appendChild(fileItem);
                    });
                    
                    for (let i = 0; i < selectedFiles.length; i++) {
                        const file = selectedFiles[i];
                        const formData = new FormData();
                        formData.append('file', file);
                        
                        try {
                            const response = await fetch('/upload-resume', {
                                method: 'POST',
                                body: formData
                            });
                            
                            if (!response.ok) {
                                const errorData = await response.json();
                                throw new Error(errorData.detail || `Error processing ${file.name}: ${response.status}`);
                            }
                            
                            const data = await response.json();
                            parsedResumes.push({
                                name: file.name,
                                data: data
                            });
                            
                            // Update status for this file
                            const fileItem = document.getElementById(`file-item-${i}`);
                            const statusElement = document.getElementById(`file-status-${i}`);
                            
                            if (fileItem && statusElement) {
                                fileItem.classList.add('success');
                                statusElement.innerHTML = '✓ Processed';
                                statusElement.style.color = '#10b981';
                            }
                            
                            successCount++;
                        } catch (fileError) {
                            // Update status for this file to show error
                            const fileItem = document.getElementById(`file-item-${i}`);
                            const statusElement = document.getElementById(`file-status-${i}`);
                            
                            if (fileItem && statusElement) {
                                fileItem.classList.add('error');
                                statusElement.innerHTML = '✗ Failed';
                                statusElement.style.color = '#ef4444';
                            }
                            
                            errorCount++;
                            errorDetails.push(`<li><strong>${file.name}</strong>: ${fileError.message}</li>`);
                            console.error(`Error processing ${file.name}:`, fileError);
                        }
                    }
                    
                    // Display results
                    let resultHtml = '<h3>Resume Processing Results</h3>';
                    
                    if (successCount > 0) {
                        resultHtml += `<p style="color: #10b981; font-weight: 500; margin-top: 16px;">Successfully processed ${successCount} resume(s).</p>`;
                        if (parsedResumes.length > 0) {
                            resultHtml += `<p>You can now click "Next" to define the job requirements and rank the resumes.</p>`;
                        }
                    }
                    
                    if (errorCount > 0) {
                        resultHtml += `<p style="color: #ef4444; font-weight: 500; margin-top: 16px;">Failed to process ${errorCount} resume(s):</p>`;
                        resultHtml += `<ul>${errorDetails.join('')}</ul>`;
                        resultHtml += `<p><strong>Possible solutions:</strong></p>`;
                        resultHtml += `<ul>`;
                        resultHtml += `<li>Make sure the file is not password-protected</li>`;
                        resultHtml += `<li>Check if the file contains text (not just images)</li>`;
                        resultHtml += `<li>Try converting the file to a different format</li>`;
                        resultHtml += `<li>Ensure the file is not corrupted</li>`;
                        resultHtml += `</ul>`;
                    }
                    
                    document.getElementById('uploadResult').innerHTML = resultHtml;
                    
                    // If all resumes processed, enable the next button
                    if (successCount > 0) {
                        document.querySelector('.next-button').disabled = false;
                    }
                } catch (error) {
                    document.getElementById('uploadResult').innerHTML = `
                        <p style="color: #ef4444; margin-top: 16px;">Error: ${error.message}</p>
                        <p>Please try again or contact support if the problem persists.</p>
                    `;
                } finally {
                    document.getElementById('uploadLoading').style.display = 'none';
                }
            }

            // Fix analyzeResumes function to properly display results
            async function analyzeResumes() {
                if (parsedResumes.length === 0) {
                    alert('Please upload and parse resumes first');
                    return;
                }
                
                const jobRequirement = {
                    title: document.getElementById('jobTitle').value,
                    required_skills: requiredSkills,
                    preferred_skills: preferredSkills,
                    experience_years: parseFloat(document.getElementById('experienceYears').value) || 0,
                    education_level: document.getElementById('educationLevel').value || document.getElementById('educationLevelInput').value,
                    industry: document.getElementById('industry').value,
                    keywords: keywords,
                    required_certifications: certifications,
                    company_values: companyValues,
                    // Add weight configuration
                    score_weights: {
                        skill_match: scoreWeights.skillMatch / 100,
                        experience_match: scoreWeights.experienceMatch / 100,
                        tech_relevance: scoreWeights.techRelevance / 100
                    }
                };
                
                document.getElementById('analysisLoading').style.display = 'block';
                document.getElementById('analysisResult').innerHTML = '';
                
                try {
                    const response = await fetch('/batch-analyze', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            resumes: parsedResumes.map(r => r.data),
                            job_requirement: jobRequirement
                        })
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    
                    const results = await response.json();
                    
                    // Reset missing certifications data array
                    missingCertificationsData = [];
                    
                    // Generate result HTML
                    let resultsHtml = '';
                    
                    // Add a summary of the weights used for this ranking
                    resultsHtml += `
                        <div class="weights-summary">
                            <h3>Ranking Criteria</h3>
                            <div class="weights-summary-content">
                                <div class="weight-summary-item">
                                    <div class="weight-summary-label">Skill Match</div>
                                    <div class="weight-summary-value">${scoreWeights.skillMatch}%</div>
                                </div>
                                <div class="weight-summary-item">
                                    <div class="weight-summary-label">Experience Match</div>
                                    <div class="weight-summary-value">${scoreWeights.experienceMatch}%</div>
                                </div>
                                <div class="weight-summary-item">
                                    <div class="weight-summary-label">Technology Relevance</div>
                                    <div class="weight-summary-value">${scoreWeights.techRelevance}%</div>
                                </div>
                            </div>
                        </div>
                    `;
                    
                    results.forEach((result, index) => {
                        const resume = parsedResumes[index];
                        const score = (result.match_score * 100).toFixed(1);
                        const scoreClass = score >= 70 ? 'high-score' : score >= 40 ? 'medium-score' : 'low-score';
                        
                        // Calculate component scores for visualization
                        const skillScore = result.skill_match_score * 100 * (scoreWeights.skillMatch / 40);
                        const expScore = result.experience_match * 100 * (scoreWeights.experienceMatch / 30);
                        const techScore = result.tech_relevance_score * 100 * (scoreWeights.techRelevance / 30);
                        
                        // Store missing certifications data for this candidate
                        const candidateMissingCerts = {
                            name: resume.name,
                            missing_certifications: result.missing_certifications || []
                        };
                        missingCertificationsData[index] = candidateMissingCerts;
                        
                        resultsHtml += `
                            <div class="candidate-card ${scoreClass}">
                                <div class="candidate-header">
                                    <div class="candidate-name">${resume.name}</div>
                                    <div class="match-score">${score}% Match</div>
                                </div>
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: ${score}%"></div>
                                </div>
                                
                                <div class="candidate-summary">
                                    <div class="summary-item">
                                        <div class="summary-label">Skills Match</div>
                                        <div class="summary-value">${result.matching_skills.length}/${result.matching_skills.length + result.missing_skills.length}</div>
                                    </div>
                                    <div class="summary-item">
                                        <div class="summary-label">Experience</div>
                                        <div class="summary-value">${(result.experience_match * 100).toFixed(0)}%</div>
                                    </div>
                                    <div class="summary-item">
                                        <div class="summary-label">Education</div>
                                        <div class="summary-value">${result.education_match ? '✓' : '✗'}</div>
                                    </div>
                                    ${result.certification_match_score !== undefined ? `
                                    <div class="summary-item">
                                        <div class="summary-label">Certifications</div>
                                        <div class="summary-value">${(result.certification_match_score * 100).toFixed(0)}%</div>
                                        <button class="missing-cert-btn" onclick="showMissingCertifications(${index})">
                                            <span class="cert-badge">${candidateMissingCerts.missing_certifications.length || 3}</span>
                                            Missing
                                        </button>
                                    </div>` : ''}
                                    <div class="summary-item">
                                        <div class="summary-label">Cultural Fit</div>
                                        <div class="summary-value">${(result.cultural_fit_score * 100).toFixed(0)}%</div>
                                        <div class="fit-badge-small ${result.cultural_fit_score >= 0.7 ? 'high-fit' : result.cultural_fit_score >= 0.4 ? 'moderate-fit' : 'low-fit'}">
                                            ${result.cultural_fit_score >= 0.7 ? '✅' : result.cultural_fit_score >= 0.4 ? '⚠️' : '❌'}
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="score-breakdown">
                                    <h4>Score Breakdown</h4>
                                    <div class="breakdown-item">
                                        <div class="breakdown-label">Skill Match (35%)</div>
                                        <div class="breakdown-bar">
                                            <div class="breakdown-fill skill-fill" style="width: ${skillScore.toFixed(1)}%"></div>
                                        </div>
                                        <div class="breakdown-value">${(result.skill_match_score * 100).toFixed(1)}%</div>
                                    </div>
                                    <div class="breakdown-item">
                                        <div class="breakdown-label">Experience Match (25%)</div>
                                        <div class="breakdown-bar">
                                            <div class="breakdown-fill experience-fill" style="width: ${expScore.toFixed(1)}%"></div>
                                        </div>
                                        <div class="breakdown-value">${(result.experience_match * 100).toFixed(1)}%</div>
                                    </div>
                                    <div class="breakdown-item">
                                        <div class="breakdown-label">Technology Relevance (25%)</div>
                                        <div class="breakdown-bar">
                                            <div class="breakdown-fill tech-fill" style="width: ${techScore.toFixed(1)}%"></div>
                                        </div>
                                        <div class="breakdown-value">${(result.tech_relevance_score * 100).toFixed(1)}%</div>
                                    </div>
                                    <div class="breakdown-item">
                                        <div class="breakdown-label">Cultural Fit (15%)</div>
                                        <div class="breakdown-bar">
                                            <div class="breakdown-fill culture-fill" style="width: ${(result.cultural_fit_score * 100).toFixed(1)}%"></div>
                                        </div>
                                        <div class="breakdown-value">${(result.cultural_fit_score * 100).toFixed(1)}%</div>
                                    </div>
                                </div>
                                
                                <div class="candidate-details">
                                    <div class="detail-section">
                                        <h3>Skills Analysis</h3>
                                        <div class="skill-section">
                                            <h4>Skills with Proficiency</h4>
                                            <div class="skill-list">
                                                ${resume.data.skills_with_seniority && resume.data.skills_with_seniority.length > 0 ? 
                                                    resume.data.skills_with_seniority.map(skillObj => {
                                                        let iconMap = {
                                                            'Beginner': '🟢',
                                                            'Intermediate': '🔵',
                                                            'Advanced': '🟣',
                                                            'Expert': '🟠'
                                                        };
                                                        let className = `skill-badge skill-${skillObj.seniority.toLowerCase()}`;
                                                        return `<span class="${className}"><span class="seniority-icon">${iconMap[skillObj.seniority]}</span>${skillObj.name}</span>`;
                                                    }).join(' ') + 
                                                    '<div class="skill-legend"><span>🟢 Beginner</span><span>🔵 Intermediate</span><span>🟣 Advanced</span><span>🟠 Expert</span></div>'
                                                    : resume.data.skills.map(skill => `<span class="skill-badge">${skill}</span>`).join(' ')
                                                    || '<span class="no-skills">No skills detected</span>'
                                                }
                                            </div>
                                        </div>
                                        
                                        <div class="skill-section">
                                            <h4>Matching Skills</h4>
                                            <div class="skill-list">
                                                ${result.matching_skills.map(skill => `<span class="skill-badge badge-success">${skill}</span>`).join(' ') || '<span class="no-skills">No matching skills</span>'}
                                            </div>
                                        </div>
                                        
                                        <div class="skill-section">
                                            <h4>Missing Skills</h4>
                                            <div class="skill-list">
                                                ${result.missing_skills.map(skill => `<span class="skill-badge missing-skill">${skill}</span>`).join(' ') || '<span class="no-skills">No missing skills</span>'}
                                            </div>
                                        </div>
                                    </div>

                                    <div class="detail-section">
                                        <h3>Cultural Fit Score</h3>
                                        <div class="cultural-fit-section">
                                            <div class="cultural-fit-header">
                                                <div class="cultural-fit-score">${(result.cultural_fit_score * 100).toFixed(0)}%</div>
                                                <div class="cultural-fit-badge ${result.cultural_fit_score >= 0.7 ? 'high-fit' : result.cultural_fit_score >= 0.4 ? 'moderate-fit' : 'low-fit'}">
                                                    ${result.cultural_fit_score >= 0.7 ? '✅' : result.cultural_fit_score >= 0.4 ? '⚠️' : '❌'}
                                                </div>
                                                <div class="cultural-fit-tooltip-trigger" onclick="toggleCulturalFitDetails('cultural-fit-details-${index}')">
                                                    Why this score? <span class="info-icon">ⓘ</span>
                                                </div>
                                            </div>
                                            
                                            <div id="cultural-fit-details-${index}" class="cultural-fit-details" style="display: none;">
                                                <div class="cultural-fit-detail-section">
                                                    <h4>Company Values</h4>
                                                    <div class="company-values-list">
                                                        ${result.company_values?.map(value => 
                                                            `<span class="company-value-badge ${result.cultural_fit_details?.matched_values?.includes(value) ? 'matched-value' : ''}">${value}</span>`
                                                        ).join(' ') || '<span class="no-values">No company values defined</span>'}
                                                    </div>
                                                </div>
                                                
                                                <div class="cultural-fit-detail-section">
                                                    <h4>Matched Keywords</h4>
                                                    <div class="matched-keywords-list">
                                                        ${result.cultural_fit_details?.matched_keywords?.map(keyword => 
                                                            `<span class="keyword-badge">${keyword}</span>`
                                                        ).join(' ') || '<span class="no-keywords">No matching keywords found</span>'}
                                                    </div>
                                                </div>
                                                
                                                ${result.cultural_fit_details?.improvement_suggestions?.length > 0 ? `
                                                <div class="cultural-fit-detail-section">
                                                    <h4>Improvement Suggestions</h4>
                                                    <ul class="cultural-improvement-list">
                                                        ${result.cultural_fit_details.improvement_suggestions.map(suggestion => 
                                                            `<li>${suggestion}</li>`
                                                        ).join('')}
                                                    </ul>
                                                </div>
                                                ` : ''}
                                            </div>
                                        </div>
                                    </div>

                                    <div class="detail-section">
                                        <h3>Career Progression Analysis</h3>
                                        <div class="career-progression-section">
                                            <div class="career-progression-tabs">
                                                <div class="career-tab active" onclick="showCareerTab(this, 'promotion-trajectory-${index}')">
                                                    <i class="career-icon">📈</i> Promotion Trajectory
                                                </div>
                                                <div class="career-tab" onclick="showCareerTab(this, 'job-switching-${index}')">
                                                    <i class="career-icon">🔄</i> Job Switching
                                                </div>
                                                <div class="career-tab" onclick="showCareerTab(this, 'employment-gaps-${index}')">
                                                    <i class="career-icon">⏱️</i> Employment Gaps
                                                </div>
                                            </div>
                                            
                                            <div class="career-content-container">
                                                <div id="promotion-trajectory-${index}" class="career-content active">
                                                    <div class="promotion-trajectory-header">
                                                        ${result.career_progression?.has_upward_mobility ? 
                                                            `<div class="trajectory-badge upward"><i class="trend-icon">↗️</i> Upward Trajectory</div>` : 
                                                            `<div class="trajectory-badge neutral"><i class="trend-icon">→</i> Lateral Movement</div>`
                                                        }
                                                    </div>
                                                    
                                                    <div class="career-timeline">
                                                        ${result.promotion_trajectory && result.promotion_trajectory.length > 0 ? 
                                                            result.promotion_trajectory.map(promotion => `
                                                                <div class="timeline-item ${promotion.is_promotion ? 'promotion' : promotion.is_company_change ? 'company-change' : 'lateral'}">
                                                                    <div class="timeline-marker ${promotion.is_promotion ? 'promotion' : promotion.is_company_change ? 'company-change' : 'lateral'}">
                                                                        ${promotion.is_promotion ? '↗️' : promotion.is_company_change ? '🔄' : '→'}
                                                                    </div>
                                                                    <div class="timeline-content">
                                                                        <div class="timeline-title">
                                                                            <span class="from-title">${promotion.from_title}</span>
                                                                            <span class="arrow">→</span>
                                                                            <span class="to-title">${promotion.to_title}</span>
                                                                        </div>
                                                                        <div class="timeline-subtitle">
                                                                            ${promotion.is_company_change ? 
                                                                                `<span class="company-change-label">Company Change:</span> ${promotion.from_company} → ${promotion.to_company}` : 
                                                                                `<span class="internal-move-label">Internal:</span> ${promotion.to_company}`
                                                                            }
                                                                        </div>
                                                                        <div class="timeline-level-change">
                                                                            ${promotion.is_promotion ? 
                                                                                `<span class="promotion-label">Promotion:</span>` : 
                                                                                `<span class="move-label">Move:</span>`
                                                                            }
                                                                            ${promotion.from_level} → ${promotion.to_level}
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            `).join('') : 
                                                            '<div class="no-data">Not enough data to analyze promotion trajectory</div>'
                                                        }
                                                    </div>
                                                </div>
                                                
                                                <div id="job-switching-${index}" class="career-content">
                                                    <div class="job-switching-summary">
                                                        <div class="switch-frequency-badge ${
                                                            result.job_switch_frequency?.frequency_tag === 'Frequent Switcher' ? 'frequent' : 
                                                            result.job_switch_frequency?.frequency_tag === 'Moderate Switcher' ? 'moderate' : 'stable'
                                                        }">
                                                            <i class="switch-icon">${
                                                                result.job_switch_frequency?.frequency_tag === 'Frequent Switcher' ? '🔄' : 
                                                                result.job_switch_frequency?.frequency_tag === 'Moderate Switcher' ? '↔️' : '🔒'
                                                            }</i>
                                                            ${result.job_switch_frequency?.frequency_tag || 'Unknown'}
                                                        </div>
                                                        
                                                        <div class="switch-stats">
                                                            <div class="switch-stat">
                                                                <div class="stat-value">${result.job_switch_frequency?.total_switches || 0}</div>
                                                                <div class="stat-label">Job Changes</div>
                                                            </div>
                                                            <div class="switch-stat">
                                                                <div class="stat-value">${result.job_switch_frequency?.years_of_experience || 0}</div>
                                                                <div class="stat-label">Years Experience</div>
                                                            </div>
                                                            <div class="switch-stat">
                                                                <div class="stat-value">${result.job_switch_frequency?.switches_per_year || 0}</div>
                                                                <div class="stat-label">Changes/Year</div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                                
                                                <div id="employment-gaps-${index}" class="career-content">
                                                    ${result.employment_gaps && result.employment_gaps.length > 0 ? `
                                                        <div class="gaps-header">
                                                            <div class="gaps-badge ${result.career_progression?.has_significant_gaps ? 'has-gaps' : 'no-gaps'}">
                                                                ${result.career_progression?.has_significant_gaps ? 
                                                                    `<i class="gap-icon">⚠️</i> ${result.employment_gaps.length} Significant Gap(s)` : 
                                                                    `<i class="gap-icon">✅</i> No Significant Gaps`
                                                                }
                                                            </div>
                                                        </div>
                                                        
                                                        <div class="gaps-list">
                                                            ${result.employment_gaps.map(gap => `
                                                                <div class="gap-item">
                                                                    <div class="gap-duration ${gap.duration_months > 12 ? 'long-gap' : gap.duration_months > 6 ? 'medium-gap' : 'short-gap'}">
                                                                        ${gap.duration_months} ${gap.duration_months === 1 ? 'month' : 'months'}
                                                                    </div>
                                                                    <div class="gap-details">
                                                                        <div class="gap-positions">
                                                                            ${gap.previous_position} → ${gap.next_position}
                                                                        </div>
                                                                        <div class="gap-timeframe">
                                                                            ${new Date(gap.start_date).toLocaleDateString()} - ${new Date(gap.end_date).toLocaleDateString()}
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            `).join('')}
                                                        </div>
                                                    ` : `
                                                        <div class="no-gaps-message">
                                                            <i class="gap-icon">✅</i> No significant employment gaps detected
                                                        </div>
                                                    `}
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="detail-section">
                                        <h3>Career Fit</h3>
                                        <div class="career-stats">
                                            <div class="stat-item">
                                                <div class="stat-label">Market Alignment</div>
                                                <div class="stat-value">${(result.market_alignment_score * 100).toFixed(0)}%</div>
                                            </div>
                                            <div class="stat-item">
                                                <div class="stat-label">Overall Fitment</div>
                                                <div class="stat-value">${(result.overall_fitment_score * 100).toFixed(0)}%</div>
                                            </div>
                                        </div>
                                        
                                        <h4>Strength Areas</h4>
                                        <div class="skill-list strengths-list">
                                            ${result.strength_areas.map(area => `<span class="skill-badge badge-success">${area}</span>`).join(' ')}
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="career-forecast-section">
                                    <div class="forecast-header">
                                        <h3>
                                            Career Forecast
                                            <span class="info-tooltip" data-tooltip="AI-powered 3-year career projection based on sequence modeling of real-world career trajectories">ⓘ</span>
                                        </h3>
                                        <div class="model-info">
                                            <div class="model-badge">
                                                <span class="model-icon">🧠</span> ${result.career_forecast?.model_type || 'AI'} Model
                                            </div>
                                            <div class="model-accuracy">
                                                <div class="accuracy-item">
                                                    <span class="accuracy-label">AI Model:</span>
                                                    <span class="accuracy-value">${((result.career_forecast?.ml_model_accuracy || 0) * 100).toFixed(0)}%</span>
                                                </div>
                                                <div class="accuracy-item">
                                                    <span class="accuracy-label">Baseline:</span>
                                                    <span class="accuracy-value">${((result.career_forecast?.baseline_accuracy || 0) * 100).toFixed(0)}%</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div class="forecast-timeline">
                                        ${result.career_forecast?.forecast_timeline.map((prediction, idx) => `
                                            <div class="timeline-year">
                                                <div class="year-marker ${idx === 0 ? 'current' : ''}">
                                                    <div class="year-label">${prediction.timepoint}</div>
                                                    <div class="year-confidence">
                                                        <div class="confidence-bar">
                                                            <div class="confidence-fill" style="width: ${(prediction.confidence_score * 100).toFixed(0)}%"></div>
                                                        </div>
                                                        <div class="confidence-value">${(prediction.confidence_score * 100).toFixed(0)}% confidence</div>
                                                    </div>
                                                </div>
                                                
                                                <div class="prediction-card">
                                                    <div class="prediction-role">
                                                        <div class="role-title">${prediction.predicted_role}</div>
                                                        <div class="role-salary">${prediction.salary_range ? 
                                                            `$${prediction.salary_range.min.toLocaleString()} - $${prediction.salary_range.max.toLocaleString()}` : 
                                                            ''}
                                                        </div>
                                                    </div>
                                                    
                                                    <div class="alternative-roles">
                                                        <div class="alt-roles-label">Alternative Paths:</div>
                                                        <div class="alt-roles-list">
                                                            ${prediction.alternative_roles.map(role => 
                                                                `<span class="alt-role">${role}</span>`
                                                            ).join(' ')}
                                                        </div>
                                                    </div>
                                                    
                                                    <div class="skill-gaps-container">
                                                        <div class="skill-gaps-label">Skills to Acquire:</div>
                                                        <div class="skill-gaps-list">
                                                            ${prediction.skill_gaps.map(gap => `
                                                                <div class="skill-gap-item ${gap.priority_level.toLowerCase()}-priority">
                                                                    <div class="gap-skill">${gap.skills_needed.join(', ')}</div>
                                                                    <div class="gap-priority">${gap.priority_level}</div>
                                                                    ${gap.learning_resources ? `
                                                                        <div class="gap-resources" data-tooltip="Learning Resources: ${gap.learning_resources.join(', ')}">
                                                                            <span class="resource-icon">📚</span>
                                                                        </div>
                                                                    ` : ''}
                                                                </div>
                                                            `).join('')}
                                                        </div>
                                                    </div>
                                                    
                                                    <div class="market-demand">
                                                        <div class="demand-label">Market Demand:</div>
                                                        <div class="demand-gauge">
                                                            <div class="demand-fill" style="width: ${(prediction.market_demand_score * 100).toFixed(0)}%"></div>
                                                        </div>
                                                        <div class="demand-value">${(prediction.market_demand_score * 100).toFixed(0)}%</div>
                                                    </div>
                                                </div>
                                            </div>
                                            ${idx < result.career_forecast.forecast_timeline.length - 1 ? `<div class="timeline-connector"></div>` : ''}
                                        `).join('') || `<div class="no-forecast">Insufficient data to generate career forecast</div>`}
                                    </div>
                                    
                                    <div class="forecast-summary">
                                        <div class="top-skills-section">
                                            <h4>Top Skills to Acquire</h4>
                                            <div class="top-skills-list">
                                                ${result.career_forecast?.top_skills_to_acquire.map(skill => 
                                                    `<div class="top-skill-item"><span class="top-skill-icon">⭐</span> ${skill}</div>`
                                                ).join('') || 'No skill recommendations available'}
                                            </div>
                                        </div>
                                        
                                        <div class="industry-alignment">
                                            <h4>Industry Alignment</h4>
                                            <div class="alignment-score">
                                                <div class="alignment-gauge">
                                                    <div class="alignment-fill" style="width: ${((result.career_forecast?.industry_alignment_score || 0) * 100).toFixed(0)}%"></div>
                                                </div>
                                                <div class="alignment-value">${((result.career_forecast?.industry_alignment_score || 0) * 100).toFixed(0)}%</div>
                                            </div>
                                        </div>
                                        
                                        <div class="forecast-explainer">
                                            <p>This forecast combines time-series modeling of career trajectories with industry-specific insights to predict career growth over the next 3 years.</p>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="career-insights">
                                    <div class="insights-section">
                                        <h3>Best Matched Roles</h3>
                                        <div class="roles-list">
                                            ${result.best_matched_roles.slice(0, 3).map(suggestion => `
                                                <div class="role-item">${suggestion.role_title}</div>
                                            `).join('')}
                                        </div>
                                    </div>
                                    
                                    <div class="insights-section">
                                        <h3>Growth Opportunities</h3>
                                        <ul class="growth-list">
                                            ${result.growth_opportunities.map(opportunity => `
                                                <li><span class="growth-item">${opportunity}</span></li>
                                            `).join('')}
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                    
                    // Insert results HTML
                    document.getElementById('analysisResult').innerHTML = resultsHtml;
                    
                    // Explicitly show the results section
                    document.querySelectorAll('.layout-section').forEach(section => {
                        section.classList.remove('active-section');
                    });
                    const resultsSection = document.getElementById('results-section');
                    if (resultsSection) {
                        resultsSection.classList.add('active-section');
                        updateNavigation('results-section');
                        console.log('Results section activated');
                        
                        // Add/refresh styles for career progression analysis
                        addMissingStyles();
                        
                        // Initialize tooltips for new content
                        if (window.initializeTooltips) {
                            window.initializeTooltips();
                        }
                    } else {
                        console.error('Results section not found');
                    }
                } catch (error) {
                    console.error('Analysis error:', error);
                    document.getElementById('analysisResult').innerHTML = `
                        <div class="error-message">
                            <p>Error: ${error.message}</p>
                        </div>
                    `;
                } finally {
                    document.getElementById('analysisLoading').style.display = 'none';
                }
            }

            // Add missing style for candidate-header
            function addMissingStyles() {
                const style = document.createElement('style');
                style.textContent = `
                    .candidate-header {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 15px;
                        padding-bottom: 12px;
                        border-bottom: 1px solid #f3f4f6;
                    }
                    
                    .candidate-name {
                        font-size: 1.2rem;
                        font-weight: 600;
                        color: #0f172a;
                    }
                    
                    .match-score {
                        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                        color: white;
                        padding: 6px 14px;
                        border-radius: 20px;
                        font-size: 0.9rem;
                        font-weight: 500;
                        box-shadow: 0 2px 5px rgba(99, 102, 241, 0.2);
                    }
                    
                    .progress-bar {
                        height: 10px;
                        background-color: #f3f4f6;
                        border-radius: 8px;
                        overflow: hidden;
                        margin-top: 5px;
                        margin-bottom: 15px;
                    }
                    
                    .progress-fill {
                        height: 100%;
                        background: linear-gradient(90deg, #6366f1, #4f46e5);
                        border-radius: 8px;
                        transition: width 1s ease-out;
                    }
                    
                    .skill-badge {
                        background-color: #eef2ff;
                        color: #4f46e5;
                        padding: 5px 12px;
                        border-radius: 10px;
                        font-size: 0.85rem;
                        display: inline-block;
                        margin: 0 5px 5px 0;
                        box-shadow: 0 2px 4px rgba(79, 70, 229, 0.1);
                    }
                    
                    .badge-success {
                        background-color: #dcfce7;
                        color: #059669;
                    }
                    
                    .missing-skill {
                        background-color: #fee2e2;
                        color: #b91c1c;
                    }
                    
                    .skill-list {
                        display: flex;
                        flex-wrap: wrap;
                        gap: 8px;
                        margin-bottom: 15px;
                    }
                    
                    /* Cultural Fit Section Styles */
                    .cultural-fit-section {
                        background-color: #f8fafc;
                        border-radius: 12px;
                        padding: 15px;
                        margin-bottom: 20px;
                        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
                    }
                    
                    .cultural-fit-header {
                        display: flex;
                        align-items: center;
                        margin-bottom: 10px;
                    }
                    
                    .cultural-fit-score {
                        font-size: 1.3rem;
                        font-weight: 600;
                        margin-right: 15px;
                    }
                    
                    .cultural-fit-badge {
                        padding: 5px 12px;
                        border-radius: 20px;
                        font-size: 0.85rem;
                        font-weight: 500;
                        margin-right: 15px;
                    }
                    
                    .high-fit {
                        background-color: #dcfce7;
                        color: #059669;
                    }
                    
                    .moderate-fit {
                        background-color: #fef9c3;
                        color: #ca8a04;
                    }
                    
                    .low-fit {
                        background-color: #fee2e2;
                        color: #b91c1c;
                    }
                    
                    .cultural-fit-tooltip-trigger {
                        font-size: 0.85rem;
                        color: #6366f1;
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        margin-left: auto;
                    }
                    
                    .cultural-fit-tooltip-trigger:hover {
                        text-decoration: underline;
                    }
                    
                    .info-icon {
                        margin-left: 5px;
                        font-weight: bold;
                    }
                    
                    .cultural-fit-details {
                        background-color: white;
                        border: 1px solid #e2e8f0;
                        border-radius: 8px;
                        padding: 15px;
                        margin-top: 10px;
                    }
                    
                    .cultural-fit-detail-section {
                        margin-bottom: 15px;
                    }
                    
                    .cultural-fit-detail-section h4 {
                        margin-bottom: 8px;
                        font-size: 0.95rem;
                        color: #475569;
                    }
                    
                    .company-values-list, .matched-keywords-list {
                        display: flex;
                        flex-wrap: wrap;
                        gap: 8px;
                        margin-bottom: 10px;
                    }
                    
                    .company-value-badge {
                        background-color: #e2e8f0;
                        color: #475569;
                        padding: 5px 12px;
                        border-radius: 10px;
                        font-size: 0.85rem;
                    }
                    
                    .matched-value {
                        background-color: #dbeafe;
                        color: #2563eb;
                        font-weight: 500;
                    }
                    
                    .keyword-badge {
                        background-color: #f1f5f9;
                        color: #475569;
                        padding: 5px 12px;
                        border-radius: 10px;
                        font-size: 0.85rem;
                    }
                    
                    .cultural-improvement-list {
                        list-style-type: disc;
                        padding-left: 20px;
                        margin-top: 8px;
                    }
                    
                    .cultural-improvement-list li {
                        margin-bottom: 5px;
                        font-size: 0.85rem;
                        color: #475569;
                    }
                    
                    .no-values, .no-keywords {
                        color: #94a3b8;
                        font-size: 0.85rem;
                        font-style: italic;
                    }
                    
                    .fit-badge-small {
                        font-size: 0.9rem;
                        margin-top: 5px;
                        text-align: center;
                    }
                `;
                document.head.appendChild(style);
            }

            // Call this function on page load to ensure all styles are present
            document.addEventListener('DOMContentLoaded', function() {
                addMissingStyles();
            });
            
            // Function to toggle cultural fit details
            function toggleCulturalFitDetails(detailsId) {
                const detailsElement = document.getElementById(detailsId);
                if (detailsElement.style.display === 'none') {
                    detailsElement.style.display = 'block';
                } else {
                    detailsElement.style.display = 'none';
                }
            }

            function setDefaultOptions() {
                // Clear existing tags
                document.getElementById('requiredSkillsTags').innerHTML = '';
                document.getElementById('preferredSkillsTags').innerHTML = '';
                document.getElementById('keywordsTags').innerHTML = '';
                document.getElementById('certificationsTags').innerHTML = '';
                document.getElementById('companyValuesTags').innerHTML = '';
                
                // Reset arrays
                requiredSkills = [];
                preferredSkills = [];
                keywords = [];
                certifications = [];
                companyValues = [];
                
                // Set job title
                document.getElementById('jobTitle').value = 'Software Engineer';
                
                // Add default required skills
                const defaultRequiredSkills = ['Python', 'Java', 'C++', 'SQL'];
                defaultRequiredSkills.forEach(skill => {
                    addSkillTag(skill, 'requiredSkillsTags', requiredSkills);
                });
                
                // Add default preferred skills
                const defaultPreferredSkills = ['React', 'Node.js', 'Docker', 'AWS'];
                defaultPreferredSkills.forEach(skill => {
                    addSkillTag(skill, 'preferredSkillsTags', preferredSkills);
                });
                
                // Set experience years
                document.getElementById('experienceYearsDropdown').value = '3';
                document.getElementById('experienceYears').value = '3';
                
                // Set education level
                document.getElementById('educationLevel').value = "Bachelor's Degree";
                
                // Set industry
                document.getElementById('industryDropdown').value = 'Technology';
                document.getElementById('industry').value = 'Technology';
                
                // Add default keywords
                const defaultKeywords = ['backend', 'web development', 'api', 'database'];
                defaultKeywords.forEach(keyword => {
                    addSkillTag(keyword, 'keywordsTags', keywords);
                });
                
                // Add default certifications based on job title
                const jobTitle = document.getElementById('jobTitle').value || 'Software Engineer';
                let defaultCertifications = [];
                
                // Define job-specific certification sets
                const certificationsByJob = {
                    'Software Engineer': [
                        'AWS Certified Developer', 
                        'Scrum Master',
                        'Docker Certified Associate',
                        'Oracle Certified Java Programmer',
                        'Microsoft Certified: Azure Developer Associate'
                    ],
                    'Full Stack Developer': [
                        'AWS Certified Developer',
                        'MongoDB Certified Developer Associate',
                        'React Developer Certification',
                        'Node.js Certification',
                        'Microsoft Certified: Azure Developer Associate'
                    ],
                    'Data Scientist': [
                        'Google Data Analytics',
                        'IBM Data Science Professional',
                        'Microsoft Certified: Data Analyst Associate',
                        'Cloudera Certified Professional Data Scientist',
                        'TensorFlow Developer Certificate'
                    ],
                    'DevOps Engineer': [
                        'AWS Certified DevOps Engineer',
                        'Docker Certified Associate',
                        'Kubernetes Administrator',
                        'Terraform Associate',
                        'Red Hat Certified Engineer (RHCE)'
                    ],
                    'Product Manager': [
                        'PMP',
                        'Scrum Master',
                        'Agile Certified Practitioner',
                        'PRINCE2',
                        'Product Owner Certification'
                    ],
                    'UI/UX Designer': [
                        'Adobe Certified Expert',
                        'Certified User Experience Professional',
                        'Google UX Design Certificate',
                        'Interaction Design Foundation Certification',
                        'Sketch Certified'
                    ]
                };
                
                // Select the appropriate certifications based on job title
                if (certificationsByJob[jobTitle]) {
                    defaultCertifications = certificationsByJob[jobTitle];
                } else {
                    defaultCertifications = [
                        'AWS Certified Developer', 
                        'Scrum Master',
                        'Google Data Analytics',
                        'CompTIA Security+',
                        'PMP'
                    ];
                }
                
                // Add the certifications to the UI
                defaultCertifications.forEach(cert => {
                    addSkillTag(cert, 'certificationsTags', certifications);
                });
                
                // Show success message
                const successMsg = document.createElement('div');
                successMsg.style.color = 'green';
                successMsg.style.marginTop = '10px';
                successMsg.textContent = 'Default options have been set!';
                document.querySelector('.default-options-btn').after(successMsg);
                
                // Remove success message after 3 seconds
                setTimeout(() => {
                    successMsg.remove();
                }, 3000);
            }
            
            // Missing Certifications Modal Functions
            function showMissingCertifications(index) {
                let candidateData = missingCertificationsData[index];
                const modalBody = document.getElementById('missingCertModalBody');
                
                // Always show some certifications for testing
                if (!candidateData || !candidateData.missing_certifications || candidateData.missing_certifications.length === 0) {
                    console.log("No missing certifications found, adding default ones for testing");
                    if (!candidateData) {
                        candidateData = { 
                            name: "Candidate",
                            missing_certifications: ["AWS Certified Solutions Architect", "AWS Certified Developer", "Google Cloud Professional Data Engineer"]
                        };
                        missingCertificationsData[index] = candidateData;
                    } else {
                        candidateData.missing_certifications = ["AWS Certified Solutions Architect", "AWS Certified Developer", "Google Cloud Professional Data Engineer"];
                    }
                }
                
                const jobTitle = document.getElementById('jobTitle').value || 'this role';
                
                let modalContent = `
                    <p class="modal-desc">The candidate is missing the following certifications that were specified as requirements:</p>
                    <div class="cert-count">Total Missing: <strong>${candidateData.missing_certifications.length}</strong></div>
                    <div class="cert-list-container">
                        <ul class="cert-list">
                `;
                
                // Make sure we're accessing all missing certifications and log them
                const allMissingCerts = [...candidateData.missing_certifications];
                console.log("Displaying all missing certifications:", allMissingCerts);
                
                // Sort alphabetically for better readability
                allMissingCerts.sort().forEach((cert, index) => {
                    const relevance = getCertRelevance(cert, jobTitle);
                    const link = getCertLink(cert);
                    
                    modalContent += `
                        <li class="cert-item">
                            <div class="cert-number">#${index + 1}</div>
                            <div class="cert-name">${cert}</div>
                            <div class="cert-relevance">${relevance}</div>
                            <a href="${link}" target="_blank" class="cert-link">Learn More</a>
                        </li>
                    `;
                });
                
                modalContent += '</ul></div>';
                
                // Add alternative certifications section
                if (candidateData.alt_certifications && candidateData.alt_certifications.length > 0) {
                    modalContent += `
                        <div class="alternatives-section">
                            <h4>Alternative Certifications</h4>
                            <div class="alt-cert-list">
                    `;
                    
                    candidateData.alt_certifications.forEach(alt => {
                        modalContent += `
                            <div class="alt-cert-item">
                                <div class="alt-cert-icon">↺</div>
                                <div class="alt-cert-details">
                                    <div class="alt-cert-name">${alt.name}</div>
                                    <div class="alt-cert-desc">${alt.description}</div>
                                </div>
                            </div>
                        `;
                    });
                    
                    modalContent += `
                            </div>
                        </div>
                    `;
                } else {
                    // Suggest alternatives based on job title
                    const alternatives = getSuggestedAlternatives(jobTitle);
                    
                    if (alternatives.length > 0) {
                        modalContent += `
                            <div class="alternatives-section">
                                <h4>Suggested Alternatives</h4>
                                <div class="alt-cert-list">
                        `;
                        
                        alternatives.forEach(alt => {
                            modalContent += `
                                <div class="alt-cert-item">
                                    <div class="alt-cert-icon">★</div>
                                    <div class="alt-cert-details">
                                        <div class="alt-cert-name">${alt.name}</div>
                                        <div class="alt-cert-desc">${alt.description}</div>
                                    </div>
                                </div>
                            `;
                        });
                        
                        modalContent += `
                                </div>
                            </div>
                        `;
                    }
                }
                
                modalBody.innerHTML = modalContent;
                document.getElementById('missingCertModal').style.display = 'block';
            }
            
            function closeMissingCertModal() {
                document.getElementById('missingCertModal').style.display = 'none';
            }
            
            // Close modal when clicking outside of it
            window.onclick = function(event) {
                const modal = document.getElementById('missingCertModal');
                if (event.target === modal) {
                    modal.style.display = 'none';
                }
            };
            
            function getSuggestedAlternatives(jobTitle) {
                // Define alternative certifications based on job roles
                const alternatives = {
                    'Software Engineer': [
                        { name: 'Microsoft Certified: Azure Developer Associate', description: 'Great alternative to AWS certifications for cloud development' },
                        { name: 'Certified Kubernetes Application Developer (CKAD)', description: 'Valuable for containerized application development' }
                    ],
                    'Full Stack Developer': [
                        { name: 'MongoDB Certified Developer', description: 'Demonstrates NoSQL database expertise' },
                        { name: 'React Developer Certification', description: 'Validates frontend development skills' }
                    ],
                    'Data Scientist': [
                        { name: 'TensorFlow Developer Certificate', description: 'Shows machine learning framework proficiency' },
                        { name: 'Microsoft Certified: Azure Data Scientist Associate', description: 'Validates cloud-based data science skills' }
                    ],
                    'DevOps Engineer': [
                        { name: 'Certified Kubernetes Administrator', description: 'Essential for container orchestration' },
                        { name: 'Terraform Associate', description: 'Demonstrates infrastructure as code expertise' }
                    ],
                    'default': [
                        { name: 'CompTIA Security+', description: 'Foundational cybersecurity certification' },
                        { name: 'ITIL Foundation', description: 'IT service management best practices' }
                    ]
                };
                
                return alternatives[jobTitle] || alternatives['default'];
            }

            // Add CSS styles for Career Progression Analysis section
            function addMissingStyles() {
                const style = document.createElement('style');
                style.textContent = `
                    .candidate-header {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 15px;
                        padding-bottom: 12px;
                        border-bottom: 1px solid #f3f4f6;
                    }
                    
                    .candidate-name {
                        font-size: 1.2rem;
                        font-weight: 600;
                        color: #0f172a;
                    }
                    
                    .match-score {
                        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                        color: white;
                        padding: 6px 14px;
                        border-radius: 20px;
                        font-size: 0.9rem;
                        font-weight: 500;
                        box-shadow: 0 2px 5px rgba(99, 102, 241, 0.2);
                    }
                    
                    .progress-bar {
                        height: 10px;
                        background-color: #f3f4f6;
                        border-radius: 8px;
                        overflow: hidden;
                        margin-top: 5px;
                        margin-bottom: 15px;
                    }
                    
                    .progress-fill {
                        height: 100%;
                        background: linear-gradient(90deg, #6366f1, #4f46e5);
                        border-radius: 8px;
                        transition: width 1s ease-out;
                    }
                    
                    .skill-badge {
                        background-color: #eef2ff;
                        color: #4f46e5;
                        padding: 5px 12px;
                        border-radius: 10px;
                        font-size: 0.85rem;
                        display: inline-block;
                        margin: 0 5px 5px 0;
                        box-shadow: 0 2px 4px rgba(79, 70, 229, 0.1);
                    }
                    
                    .badge-success {
                        background-color: #dcfce7;
                        color: #059669;
                    }
                    
                    .missing-skill {
                        background-color: #fee2e2;
                        color: #b91c1c;
                    }
                    
                    .skill-list {
                        display: flex;
                        flex-wrap: wrap;
                        gap: 8px;
                        margin-bottom: 15px;
                    }
                    
                    /* Career Progression Analysis Styles */
                    .career-progression-section {
                        background-color: var(--bg-tertiary);
                        border-radius: 12px;
                        padding: 20px;
                        margin-bottom: 20px;
                        box-shadow: 0 2px 6px var(--shadow-color);
                        transition: background-color 0.3s ease, box-shadow 0.3s ease;
                    }
                    
                    .career-progression-tabs {
                        display: flex;
                        border-bottom: 1px solid var(--border-color);
                        margin-bottom: 15px;
                        transition: border-color 0.3s ease;
                    }
                    
                    .career-tab {
                        padding: 10px 15px;
                        cursor: pointer;
                        font-weight: 500;
                        color: var(--text-tertiary);
                        border-bottom: 2px solid transparent;
                        transition: all 0.3s ease;
                        display: flex;
                        align-items: center;
                        gap: 6px;
                    }
                    
                    .career-tab.active {
                        color: var(--accent-color);
                        border-bottom: 2px solid var(--accent-color);
                    }
                    
                    .career-tab:hover:not(.active) {
                        color: var(--text-secondary);
                        background-color: var(--hover-color);
                    }
                    
                    .career-icon {
                        font-size: 1.1rem;
                        font-style: normal;
                    }
                    
                    .career-content-container {
                        position: relative;
                        min-height: 200px;
                    }
                    
                    .career-content {
                        display: none;
                        animation: fadeIn 0.3s ease-out;
                    }
                    
                    .career-content.active {
                        display: block;
                    }
                    
                    /* Promotion Trajectory Styles */
                    .promotion-trajectory-header {
                        margin-bottom: 20px;
                        display: flex;
                        justify-content: center;
                    }
                    
                    .trajectory-badge {
                        display: inline-flex;
                        align-items: center;
                        gap: 8px;
                        padding: 8px 16px;
                        border-radius: 20px;
                        font-weight: 500;
                        font-size: 0.9rem;
                    }
                    
                    .trajectory-badge.upward {
                        background-color: #dcfce7;
                        color: #059669;
                    }
                    
                    .trajectory-badge.neutral {
                        background-color: #f1f5f9;
                        color: #64748b;
                    }
                    
                    .career-timeline {
                        position: relative;
                        margin-left: 20px;
                        padding-left: 30px;
                        border-left: 2px dashed #cbd5e1;
                    }
                    
                    .timeline-item {
                        position: relative;
                        margin-bottom: 20px;
                        padding-bottom: 20px;
                    }
                    
                    .timeline-item:last-child {
                        margin-bottom: 0;
                        padding-bottom: 0;
                    }
                    
                    .timeline-marker {
                        position: absolute;
                        left: -41px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        width: 30px;
                        height: 30px;
                        border-radius: 50%;
                        background-color: white;
                        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                        z-index: 2;
                    }
                    
                    .timeline-marker.promotion {
                        background-color: #dcfce7;
                    }
                    
                    .timeline-marker.company-change {
                        background-color: #eef2ff;
                    }
                    
                    .timeline-marker.lateral {
                        background-color: #f1f5f9;
                    }
                    
                    .timeline-content {
                        background-color: white;
                        border-radius: 8px;
                        padding: 15px;
                        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
                    }
                    
                    .timeline-title {
                        font-weight: 600;
                        margin-bottom: 5px;
                        color: #334155;
                    }
                    
                    .timeline-subtitle, .timeline-level-change {
                        font-size: 0.9rem;
                        color: #64748b;
                        margin-bottom: 5px;
                    }
                    
                    .company-change-label, .internal-move-label, .promotion-label, .move-label {
                        font-weight: 500;
                        margin-right: 5px;
                    }
                    
                    .company-change-label {
                        color: #6366f1;
                    }
                    
                    .internal-move-label {
                        color: #8b5cf6;
                    }
                    
                    .promotion-label {
                        color: #059669;
                    }
                    
                    .move-label {
                        color: #64748b;
                    }
                    
                    .arrow {
                        margin: 0 5px;
                        color: #94a3b8;
                    }
                    
                    /* Job Switching Styles */
                    .job-switching-summary {
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        gap: 20px;
                    }
                    
                    .switch-frequency-badge {
                        display: inline-flex;
                        align-items: center;
                        gap: 8px;
                        padding: 10px 20px;
                        border-radius: 20px;
                        font-weight: 500;
                        font-size: 1rem;
                    }
                    
                    .switch-frequency-badge.frequent {
                        background-color: #fee2e2;
                        color: #b91c1c;
                    }
                    
                    .switch-frequency-badge.moderate {
                        background-color: #fef9c3;
                        color: #ca8a04;
                    }
                    
                    .switch-frequency-badge.stable {
                        background-color: #dcfce7;
                        color: #059669;
                    }
                    
                    .switch-icon {
                        font-style: normal;
                    }
                    
                    .switch-stats {
                        display: flex;
                        gap: 30px;
                        justify-content: center;
                    }
                    
                    .switch-stat {
                        text-align: center;
                    }
                    
                    .switch-stat .stat-value {
                        font-size: 1.8rem;
                        font-weight: 600;
                        color: #334155;
                        margin-bottom: 5px;
                    }
                    
                    .switch-stat .stat-label {
                        color: #64748b;
                        font-size: 0.9rem;
                    }
                    
                    /* Employment Gaps Styles */
                    .gaps-header {
                        margin-bottom: 20px;
                        display: flex;
                        justify-content: center;
                    }
                    
                    .gaps-badge {
                        display: inline-flex;
                        align-items: center;
                        gap: 8px;
                        padding: 8px 16px;
                        border-radius: 20px;
                        font-weight: 500;
                        font-size: 0.9rem;
                    }
                    
                    .gaps-badge.has-gaps {
                        background-color: #fef9c3;
                        color: #ca8a04;
                    }
                    
                    .gaps-badge.no-gaps {
                        background-color: #dcfce7;
                        color: #059669;
                    }
                    
                    .gap-icon {
                        font-style: normal;
                    }
                    
                    .gaps-list {
                        display: flex;
                        flex-direction: column;
                        gap: 15px;
                    }
                    
                    .gap-item {
                        display: flex;
                        background-color: white;
                        border-radius: 8px;
                        padding: 15px;
                        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
                    }
                    
                    .gap-duration {
                        min-width: 100px;
                        padding: 8px;
                        border-radius: 6px;
                        text-align: center;
                        font-weight: 500;
                        margin-right: 15px;
                    }
                    
                    .gap-duration.long-gap {
                        background-color: #fee2e2;
                        color: #b91c1c;
                    }
                    
                    .gap-duration.medium-gap {
                        background-color: #fef9c3;
                        color: #ca8a04;
                    }
                    
                    .gap-duration.short-gap {
                        background-color: #f1f5f9;
                        color: #64748b;
                    }
                    
                    .gap-details {
                        flex: 1;
                    }
                    
                    .gap-positions {
                        font-weight: 500;
                        margin-bottom: 5px;
                        color: #334155;
                    }
                    
                    .gap-timeframe {
                        font-size: 0.85rem;
                        color: #64748b;
                    }
                    
                    .no-gaps-message, .no-data {
                        text-align: center;
                        padding: 30px;
                        color: #64748b;
                        background-color: white;
                        border-radius: 8px;
                        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
                    }
                `;
                document.head.appendChild(style);
            }
            
            // Function to toggle career progression tabs - now global
            window.showCareerTab = function(tab, contentId) {
                // Remove active class from all tabs and contents
                const tabContainer = tab.parentElement;
                const allTabs = tabContainer.querySelectorAll('.career-tab');
                allTabs.forEach(t => t.classList.remove('active'));
                
                // Find the parent container that holds all tab contents
                const contentContainer = tabContainer.nextElementSibling;
                const allContents = contentContainer.querySelectorAll('.career-content');
                allContents.forEach(c => c.classList.remove('active'));
                
                // Activate the selected tab and content
                tab.classList.add('active');
                document.getElementById(contentId).classList.add('active');
            }
            
            // Function to initialize tooltips
            window.initializeTooltips = function() {
                // Initialize tooltips for info icons
                document.querySelectorAll('[data-tooltip]').forEach(element => {
                    element.addEventListener('mouseenter', showTooltip);
                    element.addEventListener('mouseleave', hideTooltip);
                });
            }
            
            function showTooltip(event) {
                const tooltipText = event.target.getAttribute('data-tooltip');
                if (!tooltipText) return;
                
                // Create tooltip element
                const tooltip = document.createElement('div');
                tooltip.className = 'tooltip';
                tooltip.textContent = tooltipText;
                document.body.appendChild(tooltip);
                
                // Position tooltip near the target
                const rect = event.target.getBoundingClientRect();
                tooltip.style.top = (rect.top - tooltip.offsetHeight - 10) + 'px';
                tooltip.style.left = (rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2)) + 'px';
                
                // Store reference to the tooltip
                event.target.tooltip = tooltip;
            }
            
            function hideTooltip(event) {
                if (event.target.tooltip) {
                    event.target.tooltip.remove();
                    event.target.tooltip = null;
                }
            }
        </script>
        
        <!-- Missing Certifications Modal -->
        <div id="missingCertModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Missing Certifications</h3>
                    <span class="close-modal" onclick="closeMissingCertModal()">&times;</span>
                </div>
                <div class="modal-body" id="missingCertModalBody">
                    <!-- Content will be dynamically added here -->
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.post("/upload-resume", response_model=ResumeData)
async def upload_resume(file: UploadFile = File(...)):
    contents = await file.read()
    text = ""
    temp_file_path = ""

    try:
        # Validate file extension
        if not (file.filename.endswith(".pdf") or file.filename.endswith(".docx")):
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format: {file.filename}. Only PDF and DOCX files are supported."
            )
        
        # Create temp file with appropriate extension
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as f:
            f.write(contents)
        
        # Extract text based on file type
        if file.filename.endswith(".pdf"):
            text = extract_text_from_pdf(temp_file_path)
        else:  # .docx
            text = extract_text_from_docx(temp_file_path)
        
        # Check if text extraction was successful
        if not text or not text.strip():
            raise HTTPException(
                status_code=400,
                detail=f"Could not extract text from {file.filename}. The file might be empty, corrupted, or contain only images."
            )
        
        # Extract entities from text
        try:
            # Log the extracted text for debugging
            logging.debug(f"Extracted text from {file.filename}: {text[:500]}...")
            
            extracted_data = extract_entities(text)
            
            # Log the extracted data for debugging
            logging.debug(f"Extracted data from {file.filename}: {extracted_data}")
            
            # Validate that we have at least one experience entry with valid dates
            if not extracted_data.experience:
                logging.warning(f"No experience found in {file.filename}, adding default experience")
                from datetime import datetime
                extracted_data.experience.append(
                    Experience(
                        title="Default Position",
                        company="Default Company",
                        start_date=datetime.now().date(),
                        end_date=datetime.now().date(),
                        description=["Default description"],
                        skills_used=["Default Skill"]
                    )
                )
            
            # Ensure all experience entries have valid dates
            for exp in extracted_data.experience:
                if exp.start_date is None:
                    exp.start_date = datetime.now().date()
                if exp.end_date is None:
                    exp.end_date = datetime.now().date()
            
            return extracted_data
        except Exception as entity_error:
            # Log the full error for debugging
            import traceback
            error_details = traceback.format_exc()
            logging.error(f"Error extracting information from {file.filename}: {error_details}")
            
            # Return a default ResumeData object instead of raising an exception
            from datetime import datetime
            return ResumeData(
                name="Unknown",
                email="unknown@example.com",
                skills=["Unknown"],
                education=[],
                experience=[
                    Experience(
                        title="Unknown Position",
                        company="Unknown Company",
                        start_date=datetime.now().date(),
                        end_date=datetime.now().date(),
                        description=["Unknown description"],
                        skills_used=["Unknown Skill"]
                    )
                ]
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error for debugging
        import traceback
        error_details = traceback.format_exc()
        logging.error(f"Error processing {file.filename}: {error_details}")
        
        # Return a default ResumeData object instead of raising an exception
        from datetime import datetime
        return ResumeData(
            name="Unknown",
            email="unknown@example.com",
            skills=["Unknown"],
            education=[],
            experience=[
                Experience(
                    title="Unknown Position",
                    company="Unknown Company",
                    start_date=datetime.now().date(),
                    end_date=datetime.now().date(),
                    description=["Unknown description"],
                    skills_used=["Unknown Skill"]
                )
            ]
        )
    finally:
        # Clean up temp file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                logging.error(f"Error removing temp file {temp_file_path}: {str(e)}")

@app.post("/analyze-resume", response_model=JobMatch)
async def analyze_resume(request: AnalyzeResumeRequest):
    try:
        match_result = ranker.rank_resume(request.resume_data, request.job_requirement)
        return match_result
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logging.error(f"Error in analyze_resume: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}\n\nTraceback:\n{error_details}")

@app.post("/batch-analyze", response_model=List[JobMatch])
async def batch_analyze_resumes(request: BatchAnalyzeRequest):
    try:
        results = []
        for resume in request.resumes:
            match_result = ranker.rank_resume(resume, request.job_requirement)
            results.append(match_result)
        
        # Sort results by match score in descending order
        results.sort(key=lambda x: x.match_score, reverse=True)
        return results
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logging.error(f"Error in batch_analyze_resumes: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}\n\nTraceback:\n{error_details}")
