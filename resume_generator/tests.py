"""
Tests for resume_generator app
"""
from django.test import TestCase, Client
from django.urls import reverse
from .models import UserResume, JobApplication, GeneratedResume, GeneratedCoverLetter
from .repositories import UserResumeRepository, JobApplicationRepository


class UserResumeModelTest(TestCase):
    """Test UserResume model"""
    
    def test_create_user_resume(self):
        """Test creating a user resume"""
        resume = UserResume.objects.create(
            user_name="Test User",
            content="Test resume content"
        )
        self.assertEqual(resume.user_name, "Test User")
        self.assertTrue(resume.is_active)
    
    def test_only_one_active_resume(self):
        """Test that only one resume is active at a time"""
        resume1 = UserResumeRepository.create(
            user_name="User 1",
            file=None,
            content="Resume 1"
        )
        resume2 = UserResumeRepository.create(
            user_name="User 2",
            file=None,
            content="Resume 2"
        )
        
        # Refresh from database
        resume1.refresh_from_db()
        
        self.assertFalse(resume1.is_active)
        self.assertTrue(resume2.is_active)


class JobApplicationModelTest(TestCase):
    """Test JobApplication model"""
    
    def test_create_job_application(self):
        """Test creating a job application"""
        job = JobApplication.objects.create(
            job_url="https://example.com/job",
            additional_instructions="Test instructions",
            generate_resume=True,
            generate_cover_letter=True
        )
        self.assertEqual(job.status, 'pending')
        self.assertTrue(job.generate_resume)


class JobApplicationRepositoryTest(TestCase):
    """Test JobApplicationRepository"""
    
    def test_get_pending_jobs(self):
        """Test getting pending jobs"""
        # Create test jobs
        JobApplication.objects.create(
            job_url="https://example.com/job1",
            status='pending'
        )
        JobApplication.objects.create(
            job_url="https://example.com/job2",
            status='completed'
        )
        
        pending_jobs = JobApplicationRepository.get_pending_jobs()
        self.assertEqual(pending_jobs.count(), 1)
    
    def test_update_status(self):
        """Test updating job status"""
        job = JobApplication.objects.create(
            job_url="https://example.com/job",
            status='pending'
        )
        
        JobApplicationRepository.update_status(job.id, 'completed')
        job.refresh_from_db()
        
        self.assertEqual(job.status, 'completed')


class ViewsTest(TestCase):
    """Test views"""
    
    def setUp(self):
        self.client = Client()
    
    def test_home_view(self):
        """Test home page loads"""
        response = self.client.get(reverse('resume_generator:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AI Resume & Cover Letter Generator')
    
    def test_upload_resume_view(self):
        """Test upload resume page loads"""
        response = self.client.get(reverse('resume_generator:upload_resume'))
        self.assertEqual(response.status_code, 200)
    
    def test_upload_excel_view(self):
        """Test upload excel page loads"""
        response = self.client.get(reverse('resume_generator:upload_excel'))
        self.assertEqual(response.status_code, 200)


# To run tests:
# python manage.py test resume_generator
