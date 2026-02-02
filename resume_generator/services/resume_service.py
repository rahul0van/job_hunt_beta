"""
Service layer for handling business logic
"""
import os
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional
from django.conf import settings
from ..repositories import (
    UserResumeRepository, JobApplicationRepository,
    GeneratedResumeRepository, GeneratedCoverLetterRepository
)
from .ai.gemini_service import GeminiService


class JobScraperService:
    """Service to scrape job descriptions from URLs"""
    
    @staticmethod
    def extract_job_description(url: str) -> str:
        """
        Extract job description from a URL
        Returns the text content of the job posting
        """
        try:
            # More comprehensive headers to avoid being blocked
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
            }
            
            # Try with session for better cookie handling
            session = requests.Session()
            response = session.get(url, headers=headers, timeout=15, allow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(['script', 'style', 'header', 'footer', 'nav']):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # If text is too short, it might mean the scraping failed
            if len(text) < 100:
                return f"Unable to extract sufficient job description content from URL. Please paste the job description manually in the 'additional_instructions' column of your Google Sheet."
            
            return text
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                return "Website blocked the request (403 Forbidden). Please copy and paste the job description into the 'additional_instructions' column of your Google Sheet, and the system will use that instead."
            else:
                return f"HTTP Error {e.response.status_code}: Unable to access job posting. Please paste the job description in 'additional_instructions' column."
        except requests.exceptions.Timeout:
            return "Request timed out. Please paste the job description in 'additional_instructions' column of your Google Sheet."
        except Exception as e:
            return f"Unable to extract job description automatically. Please paste the job description in 'additional_instructions' column. Error: {str(e)}"


class ResumeProcessorService:
    """Service to process resumes and extract text"""
    
    @staticmethod
    def extract_text_from_file(file_path: str) -> str:
        """
        Extract text from uploaded resume file
        Supports PDF, DOCX, and TXT formats
        """
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif file_extension == '.pdf':
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        text = ''
                        for page in pdf_reader.pages:
                            text += page.extract_text()
                        return text
                except ImportError:
                    return "PyPDF2 not installed. Please install it to process PDF files."
            
            elif file_extension == '.docx':
                try:
                    import docx
                    doc = docx.Document(file_path)
                    text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                    return text
                except ImportError:
                    return "python-docx not installed. Please install it to process DOCX files."
            
            else:
                return "Unsupported file format"
        
        except Exception as e:
            return f"Error extracting text: {str(e)}"


class AIResumeGeneratorService:
    """Service to generate and update resumes using AI"""
    
    def __init__(self):
        self.gemini_service = GeminiService()
        self.job_scraper = JobScraperService()
    
    def generate_resume(self, job_application, user_resume_content: str, 
                       additional_instructions: str = '') -> Dict:
        """
        Generate a tailored resume for a specific job
        """
        try:
            # Extract job description if not already available
            if not job_application.job_description:
                job_description = self.job_scraper.extract_job_description(
                    job_application.job_url
                )
                JobApplicationRepository.update_job_description(
                    job_application.id, job_description
                )
            else:
                job_description = job_application.job_description
            
            # Create prompt for Gemini
            prompt = f"""
You are an expert resume writer. Based on the following information, create a tailored, professional resume that highlights the most relevant skills and experiences for this specific job.

**Job Description:**
{job_description}

**Current Resume:**
{user_resume_content}

**Additional Instructions:**
{additional_instructions if additional_instructions else 'None'}

Please generate a professional, ATS-friendly resume that:
1. Highlights relevant skills and experiences matching the job requirements
2. Uses action verbs and quantifiable achievements
3. Is properly formatted with clear sections (Summary, Experience, Education, Skills)
4. Emphasizes keywords from the job description
5. Maintains honesty while presenting information in the best light

Format the resume in a clean, professional manner.
"""
            
            # Generate resume using Gemini
            generated_content = self.gemini_service.generate_content(prompt)
            
            # Also generate recommendations
            recommendations_prompt = f"""
Based on the job description and the candidate's current resume, provide 3-5 specific recommendations for improving the resume to better match this job opportunity.

**Job Description:**
{job_description[:1000]}...

**Current Resume:**
{user_resume_content[:1000]}...

Provide actionable, specific recommendations.
"""
            
            recommendations = self.gemini_service.generate_content(recommendations_prompt)
            
            return {
                'success': True,
                'content': generated_content,
                'recommendations': recommendations
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_cover_letter(self, job_application, user_resume_content: str,
                             additional_instructions: str = '') -> Dict:
        """
        Generate a tailored cover letter for a specific job
        """
        try:
            # Extract job description if not already available
            if not job_application.job_description:
                job_description = self.job_scraper.extract_job_description(
                    job_application.job_url
                )
                JobApplicationRepository.update_job_description(
                    job_application.id, job_description
                )
            else:
                job_description = job_application.job_description
            
            # Create prompt for Gemini
            prompt = f"""
You are an expert cover letter writer. Based on the following information, create a compelling, professional cover letter that demonstrates enthusiasm for the position and highlights why the candidate is a perfect fit.

**Job Description:**
{job_description}

**Candidate's Resume/Background:**
{user_resume_content}

**Additional Instructions:**
{additional_instructions if additional_instructions else 'None'}

Please generate a professional cover letter that:
1. Opens with a strong, engaging introduction
2. Clearly explains why the candidate is interested in this specific role and company
3. Highlights 2-3 key achievements or skills that match the job requirements
4. Shows genuine enthusiasm and cultural fit
5. Closes with a confident call to action
6. Is concise (3-4 paragraphs, fitting on one page)

Format the cover letter professionally with proper business letter structure.
"""
            
            # Generate cover letter using Gemini
            generated_content = self.gemini_service.generate_content(prompt)
            
            return {
                'success': True,
                'content': generated_content
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
