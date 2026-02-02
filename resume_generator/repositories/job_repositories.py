"""
Repository pattern implementation for data access layer
"""
from typing import List, Optional
from django.db.models import QuerySet
from ..models import UserResume, JobApplication, GeneratedResume, GeneratedCoverLetter


class UserResumeRepository:
    """Repository for UserResume model"""
    
    @staticmethod
    def create(user_name: str, file, content: str = '') -> UserResume:
        """Create a new user resume"""
        # Deactivate all previous resumes
        UserResume.objects.filter(is_active=True).update(is_active=False)
        return UserResume.objects.create(
            user_name=user_name,
            file=file,
            content=content,
            is_active=True
        )
    
    @staticmethod
    def get_active_resume() -> Optional[UserResume]:
        """Get the current active resume"""
        return UserResume.objects.filter(is_active=True).first()
    
    @staticmethod
    def get_by_id(resume_id: int) -> Optional[UserResume]:
        """Get resume by ID"""
        try:
            return UserResume.objects.get(id=resume_id)
        except UserResume.DoesNotExist:
            return None
    
    @staticmethod
    def get_all() -> QuerySet:
        """Get all resumes"""
        return UserResume.objects.all()
    
    @staticmethod
    def update_content(resume_id: int, content: str) -> bool:
        """Update resume content"""
        try:
            resume = UserResume.objects.get(id=resume_id)
            resume.content = content
            resume.save()
            return True
        except UserResume.DoesNotExist:
            return False


class JobApplicationRepository:
    """Repository for JobApplication model"""
    
    @staticmethod
    def create(unique_id: str = '', job_url: str = '', job_description: str = '', additional_instructions: str = '',
               generate_resume: bool = True, generate_cover_letter: bool = True,
               generate_new_resume: bool = True, resume_generated: bool = False,
               cover_letter_generated: bool = False, excel_row_index: int = None,
               company_name: str = '', user_resume: Optional[UserResume] = None) -> JobApplication:
        """Create a new job application"""
        return JobApplication.objects.create(
            unique_id=unique_id,
            job_url=job_url,
            job_description=job_description,
            additional_instructions=additional_instructions,
            generate_resume=generate_resume,
            generate_cover_letter=generate_cover_letter,
            generate_new_resume=generate_new_resume,
            resume_generated=resume_generated,
            cover_letter_generated=cover_letter_generated,
            excel_row_index=excel_row_index,
            company_name=company_name,
            user_resume=user_resume
        )
    
    @staticmethod
    def bulk_create(job_applications: List[dict]) -> List[JobApplication]:
        """Create multiple job applications at once"""
        objs = [JobApplication(**data) for data in job_applications]
        return JobApplication.objects.bulk_create(objs)
    
    @staticmethod
    def get_by_id(job_id: int) -> Optional[JobApplication]:
        """Get job application by ID"""
        try:
            return JobApplication.objects.get(id=job_id)
        except JobApplication.DoesNotExist:
            return None
    
    @staticmethod
    def get_pending_jobs() -> QuerySet:
        """Get all pending job applications"""
        return JobApplication.objects.filter(status='pending')
    
    @staticmethod
    def get_all() -> QuerySet:
        """Get all job applications"""
        return JobApplication.objects.all()
    
    @staticmethod
    def update_status(job_id: int, status: str) -> bool:
        """Update job application status"""
        try:
            job = JobApplication.objects.get(id=job_id)
            job.status = status
            job.save()
            return True
        except JobApplication.DoesNotExist:
            return False
    
    @staticmethod
    def update_job_description(job_id: int, job_description: str) -> bool:
        """Update job description"""
        try:
            job = JobApplication.objects.get(id=job_id)
            job.job_description = job_description
            job.save()
            return True
        except JobApplication.DoesNotExist:
            return False


class GeneratedResumeRepository:
    """Repository for GeneratedResume model"""
    
    @staticmethod
    def create(job_application: JobApplication, content: str,
               recommendations: str = '', file_path: str = '',
               google_doc_id: str = '', google_doc_url: str = '',
               company_name: str = '') -> GeneratedResume:
        """Create a new generated resume"""
        return GeneratedResume.objects.create(
            job_application=job_application,
            content=content,
            recommendations=recommendations,
            file_path=file_path,
            google_doc_id=google_doc_id,
            google_doc_url=google_doc_url,
            company_name=company_name
        )
    
    @staticmethod
    def get_by_id(resume_id: int) -> Optional[GeneratedResume]:
        """Get generated resume by ID"""
        try:
            return GeneratedResume.objects.get(id=resume_id)
        except GeneratedResume.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_job(job_application: JobApplication) -> QuerySet:
        """Get all generated resumes for a job application"""
        return GeneratedResume.objects.filter(job_application=job_application)
    
    @staticmethod
    def get_by_job_application(job_app_id: int) -> Optional[GeneratedResume]:
        """Get the latest generated resume for a job application by ID"""
        return GeneratedResume.objects.filter(job_application_id=job_app_id).order_by('-created_at').first()



class GeneratedCoverLetterRepository:
    """Repository for GeneratedCoverLetter model"""
    
    @staticmethod
    def create(job_application: JobApplication, content: str,
               file_path: str = '', google_doc_id: str = '',
               google_doc_url: str = '') -> GeneratedCoverLetter:
        """Create a new generated cover letter"""
        return GeneratedCoverLetter.objects.create(
            job_application=job_application,
            content=content,
            file_path=file_path,
            google_doc_id=google_doc_id,
            google_doc_url=google_doc_url
        )
    
    @staticmethod
    def get_by_id(cover_id: int) -> Optional[GeneratedCoverLetter]:
        """Get generated cover letter by ID"""
        try:
            return GeneratedCoverLetter.objects.get(id=cover_id)
        except GeneratedCoverLetter.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_job(job_application: JobApplication) -> QuerySet:
        """Get all generated cover letters for a job application"""
        return GeneratedCoverLetter.objects.filter(job_application=job_application)
    
    @staticmethod
    def get_by_job_application(job_app_id: int) -> Optional[GeneratedCoverLetter]:
        """Get the latest generated cover letter for a job application by ID"""
        return GeneratedCoverLetter.objects.filter(job_application_id=job_app_id).order_by('-created_at').first()

