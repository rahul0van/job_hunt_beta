"""
Service for continuous monitoring and processing of Google Drive Excel files
"""
import time
from datetime import datetime
from typing import Optional, Dict
from django.utils import timezone
from ..models import GoogleDriveConfig, JobApplication, UserResume
from .external.google_drive_service import GoogleDriveService
from .resume_service import AIResumeGeneratorService, JobScraperService
from ..repositories import (
    JobApplicationRepository, 
    GeneratedResumeRepository,
    GeneratedCoverLetterRepository,
    UserResumeRepository
)


class GoogleDriveMonitorService:
    """Service to monitor Google Drive Excel files and automatically generate resumes/cover letters"""
    
    def __init__(self):
        self.ai_service = AIResumeGeneratorService()
        self.job_scraper = JobScraperService()
        self.drive_service = GoogleDriveService()
    
    def start_monitoring(self, excel_file_id: str, output_folder_id: str) -> Dict:
        """
        Start monitoring a Google Drive Excel file
        
        Args:
            excel_file_id: Google Drive file ID of Excel file
            output_folder_id: Google Drive folder ID for output documents
        
        Returns:
            Status dictionary
        """
        try:
            # Get file metadata
            file_meta = self.drive_service.get_file_metadata(excel_file_id)
            
            # Create or update config
            config, created = GoogleDriveConfig.objects.get_or_create(
                excel_file_id=excel_file_id,
                defaults={
                    'excel_file_name': file_meta['name'],
                    'output_folder_id': output_folder_id,
                    'is_monitoring': True,
                    'last_modified': timezone.now()
                }
            )
            
            if not created:
                config.output_folder_id = output_folder_id
                config.excel_file_name = file_meta['name']
                config.is_monitoring = True
                config.save()
            
            return {
                'success': True,
                'message': f'Started monitoring {file_meta["name"]}',
                'config_id': config.id
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def stop_monitoring(self, config_id: int = None, excel_file_id: str = None) -> Dict:
        """
        Stop monitoring a Google Drive Excel file
        
        Args:
            config_id: ID of config
            excel_file_id: Google Drive file ID
        
        Returns:
            Status dictionary
        """
        try:
            if config_id:
                config = GoogleDriveConfig.objects.get(id=config_id)
            elif excel_file_id:
                config = GoogleDriveConfig.objects.get(excel_file_id=excel_file_id)
            else:
                return {'success': False, 'error': 'Provide config_id or excel_file_id'}
            
            config.is_monitoring = False
            config.save()
            
            return {'success': True, 'message': 'Stopped monitoring'}
        
        except GoogleDriveConfig.DoesNotExist:
            return {'success': False, 'error': 'Config not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def process_drive_excel(self, config_id: int, force_reprocess: bool = False) -> Dict:
        """
        Process all pending jobs from Google Drive Excel file
        
        Args:
            config_id: GoogleDriveConfig ID
            force_reprocess: If True, reprocess even if already generated
        
        Returns:
            Status dictionary with counts
        """
        try:
            config = GoogleDriveConfig.objects.get(id=config_id)
            
            # Read Excel from Drive
            job_apps_data = self.drive_service.read_excel_from_drive(config.excel_file_id)
            
            # Get active resume
            active_resume = UserResumeRepository.get_active_resume()
            if not active_resume:
                return {
                    'success': False,
                    'error': 'No active resume found. Please upload a resume first.'
                }
            
            processed_count = 0
            skipped_count = 0
            error_count = 0
            
            for job_data in job_apps_data:
                try:
                    # Skip if both are already generated in the sheet
                    resume_done_in_sheet = str(job_data.get('resume_generated', '')).lower() == 'yes'
                    cover_done_in_sheet = str(job_data.get('cover_letter_generated', '')).lower() == 'yes'
                    
                    if not force_reprocess and resume_done_in_sheet and cover_done_in_sheet:
                        skipped_count += 1
                        continue
                    
                    # Check generation flags from sheet
                    should_gen_resume = str(job_data.get('generate_resume', 'yes')).lower() in ['yes', 'true', '1']
                    should_gen_cover = str(job_data.get('generate_cover_letter', 'yes')).lower() in ['yes', 'true', '1']
                    
                    if not force_reprocess and not should_gen_resume and not should_gen_cover:
                        skipped_count += 1
                        continue
                    
                    # Find or create job application
                    job_app = JobApplication.objects.filter(
                        job_url=job_data['job_url'],
                        user_resume=active_resume
                    ).first()
                    
                    if not job_app:
                        job_app = JobApplicationRepository.create(
                            job_url=job_data['job_url'],
                            additional_instructions=job_data.get('additional_instructions', ''),
                            generate_resume=should_gen_resume,
                            generate_cover_letter=should_gen_cover,
                            generate_new_resume=job_data.get('generate_new_resume', True),
                            resume_generated=resume_done_in_sheet,
                            cover_letter_generated=cover_done_in_sheet,
                            excel_row_index=job_data.get('excel_row_index'),
                            company_name=job_data.get('company_name', ''),
                            user_resume=active_resume
                        )
                    else:
                        # Update from sheet data
                        job_app.generate_resume = should_gen_resume
                        job_app.generate_cover_letter = should_gen_cover
                        job_app.additional_instructions = job_data.get('additional_instructions', '')
                        job_app.excel_row_index = job_data.get('excel_row_index')
                        job_app.save()
                    
                    # Process the job
                    result = self._process_single_job(
                        job_app=job_app,
                        resume_content=active_resume.content,
                        config=config,
                        force_reprocess=force_reprocess
                    )
                    
                    if result['success']:
                        processed_count += 1
                    else:
                        error_count += 1
                
                except Exception as e:
                    print(f"Error processing job {job_data.get('job_url')}: {str(e)}")
                    error_count += 1
            
            # Update config
            config.last_checked = timezone.now()
            config.last_modified = timezone.now()
            config.save()
            
            return {
                'success': True,
                'processed': processed_count,
                'skipped': skipped_count,
                'errors': error_count,
                'total': len(job_apps_data)
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _process_single_job(self, job_app: JobApplication, resume_content: str,
                           config: GoogleDriveConfig, force_reprocess: bool = False) -> Dict:
        """
        Process a single job application and create Google Doc
        
        Args:
            job_app: JobApplication instance
            resume_content: User's resume content
            config: GoogleDriveConfig instance
            force_reprocess: Force reprocessing
        
        Returns:
            Status dictionary
        """
        try:
            # Extract job description if needed
            if not job_app.job_description:
                job_description = self.job_scraper.extract_job_description(job_app.job_url)
                
                # If scraping failed and we have additional_instructions, use that as job description
                if ("Unable to extract" in job_description or "blocked the request" in job_description or 
                    "Error" in job_description or len(job_description) < 100):
                    if job_app.additional_instructions and len(job_app.additional_instructions) > 100:
                        # User provided job description in additional_instructions
                        job_description = f"Job Description (from user input):\n\n{job_app.additional_instructions}"
                        job_app.additional_instructions = ""  # Clear it since we used it
                
                JobApplicationRepository.update_job_description(job_app.id, job_description)
                job_app.refresh_from_db()
            
            # If job description is still too short or contains error message, fail gracefully
            if len(job_app.job_description) < 50 or "Error" in job_app.job_description[:100]:
                return {
                    'success': False, 
                    'error': 'Could not obtain job description. Please paste the job description in the additional_instructions column of your Google Sheet.'
                }
            
            # Extract company name if not already set
            if not job_app.company_name:
                company_name = self.drive_service.extract_company_name(
                    job_app.job_description,
                    job_app.job_url
                )
                job_app.company_name = company_name if company_name else "Company"
                job_app.save()
            
            resume_generated = False
            cover_generated = False
            recommendations = ""
            resume_content_text = ""
            cover_letter_content = ""
            
            # Respect config settings for generation behavior
            should_generate_resume = config.generate_new_resume and job_app.generate_resume
            should_generate_recommendations = config.generate_recommendations
            should_generate_cover_letter = config.always_generate_cover_letter or job_app.generate_cover_letter
            
            # Generate cover letter if requested
            if should_generate_cover_letter and (force_reprocess or not job_app.cover_letter_generated):
                result = self.ai_service.generate_cover_letter(
                    job_app,
                    resume_content,
                    job_app.additional_instructions
                )
                
                if result['success']:
                    cover_letter_content = result['content']
                    cover_generated = True
            
            # Generate resume if requested
            if should_generate_resume and (force_reprocess or not job_app.resume_generated):
                if job_app.generate_new_resume:
                    # Generate new resume
                    result = self.ai_service.generate_resume(
                        job_app,
                        resume_content,
                        job_app.additional_instructions
                    )
                    
                    if result['success']:
                        resume_content_text = result['content']
                        recommendations = result.get('recommendations', '')
                        resume_generated = True
                else:
                    # Only generate recommendations if enabled
                    if should_generate_recommendations:
                        recommendations_prompt = f"""
Based on the job description and the candidate's current resume, provide 3-5 specific, actionable recommendations for improving the resume to better match this job opportunity.

**Job Description:**
{job_app.job_description[:2000]}...

**Current Resume:**
{resume_content[:2000]}...

Provide clear, actionable recommendations in a concise format.
"""
                        recommendations = self.ai_service.gemini_service.generate_content(
                            recommendations_prompt
                        )
                    resume_generated = True
            
            # Check if Google Doc already exists for this job
            google_doc_url = ""
            google_doc_id = ""
            
            # Check existing generated resume/cover letter for this job
            existing_resume = GeneratedResumeRepository.get_by_job_application(job_app.id)
            existing_cover = GeneratedCoverLetterRepository.get_by_job_application(job_app.id)
            
            # Use existing document if available
            if existing_resume and existing_resume.google_doc_id:
                google_doc_id = existing_resume.google_doc_id
                google_doc_url = existing_resume.google_doc_url
            elif existing_cover and existing_cover.google_doc_id:
                google_doc_id = existing_cover.google_doc_id
                google_doc_url = existing_cover.google_doc_url
            
            # Create or update Google Doc if we have content to save
            if (resume_content_text or cover_letter_content):
                doc_title = f"{job_app.company_name} - Resume & Cover Letter"
                
                # Use original resume if no new resume generated
                if not resume_content_text:
                    resume_content_text = resume_content
                
                if google_doc_id:
                    # Update existing document
                    doc_info = self.drive_service.update_google_doc(
                        doc_id=google_doc_id,
                        resume_content=resume_content_text,
                        cover_letter_content=cover_letter_content if cover_letter_content else ""
                    )
                else:
                    # Create new document
                    doc_info = self.drive_service.create_google_doc(
                        folder_id=config.output_folder_id,
                        doc_title=doc_title,
                        resume_content=resume_content_text,
                        cover_letter_content=cover_letter_content if cover_letter_content else ""
                    )
                
                google_doc_id = doc_info['doc_id']
                google_doc_url = doc_info['doc_url']
            
            # Save to database
            if resume_generated or resume_content_text or cover_generated:
                # Only create resume entry if we have resume content
                if resume_content_text or resume_generated:
                    GeneratedResumeRepository.create(
                        job_application=job_app,
                        content=resume_content_text if resume_content_text else resume_content,
                        recommendations=recommendations,
                        google_doc_id=google_doc_id,
                        google_doc_url=google_doc_url,
                        company_name=job_app.company_name
                    )
            
            if cover_generated:
                GeneratedCoverLetterRepository.create(
                    job_application=job_app,
                    content=cover_letter_content,
                    google_doc_id=google_doc_id,
                    google_doc_url=google_doc_url
                )
            
            # Update job application status
            job_app.resume_generated = job_app.resume_generated or resume_generated
            job_app.cover_letter_generated = job_app.cover_letter_generated or cover_generated
            
            if job_app.resume_generated and job_app.cover_letter_generated:
                job_app.status = 'completed'
            elif job_app.resume_generated or job_app.cover_letter_generated:
                job_app.status = 'processing'
            
            job_app.save()
            
            # Update Excel in Drive
            if job_app.excel_row_index:
                self.drive_service.update_excel_in_drive(
                    file_id=config.excel_file_id,
                    row_index=job_app.excel_row_index,
                    resume_generated=job_app.resume_generated,
                    cover_letter_generated=job_app.cover_letter_generated,
                    recommendations=recommendations if recommendations else None,
                    company_name=job_app.company_name,
                    google_doc_url=google_doc_url if google_doc_url else None
                )
            
            return {'success': True}
        
        except Exception as e:
            job_app.status = 'failed'
            job_app.save()
            return {'success': False, 'error': str(e)}
    
    def monitor_loop(self, check_interval: int = 60):
        """
        Continuous monitoring loop for Google Drive
        
        Args:
            check_interval: Seconds between checks (default: 60)
        """
        print(f"Starting Google Drive monitoring loop (checking every {check_interval} seconds)...")
        
        while True:
            try:
                # Get all configs being monitored
                configs = GoogleDriveConfig.objects.filter(is_monitoring=True)
                
                for config in configs:
                    print(f"Processing {config.excel_file_name}...")
                    result = self.process_drive_excel(config.id)
                    
                    if result['success']:
                        print(f"Processed: {result['processed']}, "
                             f"Skipped: {result['skipped']}, "
                             f"Errors: {result['errors']}")
                    else:
                        print(f"Error: {result.get('error')}")
                
                time.sleep(check_interval)
            
            except KeyboardInterrupt:
                print("\nStopping monitor loop...")
                break
            except Exception as e:
                print(f"Error in monitor loop: {str(e)}")
                time.sleep(check_interval)
    
    def get_monitoring_status(self) -> Dict:
        """
        Get status of all monitored Google Drive files
        
        Returns:
            Dictionary with monitoring information
        """
        try:
            configs = GoogleDriveConfig.objects.all()
            
            status_list = []
            for config in configs:
                status_list.append({
                    'id': config.id,
                    'excel_file_id': config.excel_file_id,
                    'excel_file_name': config.excel_file_name,
                    'output_folder_id': config.output_folder_id,
                    'is_monitoring': config.is_monitoring,
                    'last_checked': config.last_checked,
                    'last_modified': config.last_modified,
                })
            
            return {
                'success': True,
                'configs': status_list,
                'active_count': len([c for c in status_list if c['is_monitoring']])
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
