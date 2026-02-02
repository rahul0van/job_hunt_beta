"""
Gemini API integration service
"""
import google.generativeai as genai
from django.conf import settings
from typing import Optional


class GeminiService:
    """Service to interact with Google's Gemini API"""
    
    def __init__(self):
        """Initialize Gemini service with API key"""
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in settings. Please set it in environment variables.")
        
        genai.configure(api_key=api_key)
        
        # Using Gemini 2.5 Flash
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def generate_content(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """
        Generate content using Gemini API
        
        Args:
            prompt: The input prompt for content generation
            max_tokens: Maximum number of tokens to generate (optional)
        
        Returns:
            Generated text content
        """
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=0.7,
                top_p=0.95,
                top_k=40,
            )
            
            if max_tokens:
                generation_config.max_output_tokens = max_tokens
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
        
        except Exception as e:
            raise Exception(f"Error generating content with Gemini: {str(e)}")
    
    def generate_with_context(self, system_instruction: str, user_prompt: str) -> str:
        """
        Generate content with system instructions
        
        Args:
            system_instruction: System-level instructions for the model
            user_prompt: User's actual prompt
        
        Returns:
            Generated text content
        """
        try:
            model = genai.GenerativeModel(
                'gemini-2.5-flash',
                system_instruction=system_instruction
            )
            
            response = model.generate_content(user_prompt)
            return response.text
        
        except Exception as e:
            raise Exception(f"Error generating content with Gemini: {str(e)}")
    
    def analyze_job_description(self, job_description: str) -> dict:
        """
        Analyze job description to extract key requirements
        
        Args:
            job_description: The job description text
        
        Returns:
            Dictionary with analyzed components
        """
        try:
            prompt = f"""
Analyze the following job description and extract:
1. Key required skills
2. Required experience level
3. Educational requirements
4. Key responsibilities
5. Company culture indicators

Job Description:
{job_description}

Provide the analysis in a structured format.
"""
            
            response = self.generate_content(prompt)
            
            return {
                'success': True,
                'analysis': response
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
