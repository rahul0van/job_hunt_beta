from django.db import models
from django.core.validators import FileExtensionValidator


class GoogleDriveConfig(models.Model):
    """Model to store Google Drive configuration"""
    excel_file_id = models.CharField(max_length=500, help_text='Google Drive File ID for Excel file')
    excel_file_name = models.CharField(max_length=500, blank=True, help_text='Excel file name')
    output_folder_id = models.CharField(max_length=500, help_text='Google Drive Folder ID for output docs')
    is_monitoring = models.BooleanField(default=False, help_text='Is currently being monitored')
    last_checked = models.DateTimeField(null=True, blank=True, help_text='Last time file was checked')
    last_modified = models.DateTimeField(null=True, blank=True, help_text='Last modification time of file')
    
    # Application Settings
    generate_new_resume = models.BooleanField(
        default=True,
        help_text="Generate new tailored resume for each job (requires uploaded resume)"
    )
    generate_recommendations = models.BooleanField(
        default=True,
        help_text="Generate AI recommendations for resume improvement"
    )
    always_generate_cover_letter = models.BooleanField(
        default=True,
        help_text="Always generate cover letter regardless of resume setting"
    )
    auto_cleanup_old_jobs = models.BooleanField(
        default=False,
        help_text="Automatically archive jobs not found in Excel during sync"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Google Drive Config'
        verbose_name_plural = 'Google Drive Configs'
    
    def __str__(self):
        return f"Google Drive: {self.excel_file_name} ({'Monitoring' if self.is_monitoring else 'Stopped'})"


class UserResume(models.Model):
    """Model to store user's uploaded resumes"""
    user_name = models.CharField(max_length=255, blank=True, default='User')
    file = models.FileField(
        upload_to='resumes/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'docx', 'txt'])],
        help_text='Upload resume in PDF, DOCX, or TXT format'
    )
    content = models.TextField(blank=True, help_text='Extracted text from resume')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, help_text='Current active resume')
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'User Resume'
        verbose_name_plural = 'User Resumes'
    
    def __str__(self):
        return f"Resume - {self.user_name} ({self.uploaded_at.strftime('%Y-%m-%d')})"


class JobApplication(models.Model):
    """Model to store job applications from Excel/Google Sheets"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    unique_id = models.CharField(max_length=100, unique=True, blank=True, help_text='Unique identifier for Excel row sync')
    job_url = models.URLField(max_length=1000, blank=True, help_text='URL of the job description (optional if job_description is provided)')
    job_description = models.TextField(blank=True, help_text='Job description text (required if job_url is empty)')
    company_name = models.CharField(max_length=500, blank=True, help_text='Extracted company name')
    additional_instructions = models.TextField(
        blank=True,
        help_text='Additional instructions for AI to customize resume/cover letter'
    )
    generate_resume = models.BooleanField(default=True, help_text='Generate/Update resume')
    generate_cover_letter = models.BooleanField(default=True, help_text='Generate cover letter')
    generate_new_resume = models.BooleanField(
        default=True,
        help_text='If False, only generate cover letter and recommendations without updating resume'
    )
    resume_generated = models.BooleanField(default=False, help_text='Resume has been generated')
    cover_letter_generated = models.BooleanField(default=False, help_text='Cover letter has been generated')
    excel_row_index = models.IntegerField(null=True, blank=True, help_text='Row index in Excel file')
    user_resume = models.ForeignKey(
        UserResume,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_applications'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Job Application'
        verbose_name_plural = 'Job Applications'
    
    def __str__(self):
        if self.job_url:
            return f"Job Application - {self.job_url[:50]}... ({self.status})"
        elif self.job_description:
            return f"Job Application - {self.job_description[:50]}... ({self.status})"
        else:
            return f"Job Application #{self.id} ({self.status})"


class GeneratedResume(models.Model):
    """Model to store AI-generated or updated resumes"""
    job_application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name='generated_resumes'
    )
    content = models.TextField(help_text='Generated resume content')
    recommendations = models.TextField(
        blank=True,
        help_text='AI recommendations for improving the resume'
    )
    file_path = models.CharField(max_length=500, blank=True, help_text='Path to generated file')
    google_doc_id = models.CharField(max_length=500, blank=True, help_text='Google Docs ID (combined doc with cover letter)')
    google_doc_url = models.URLField(max_length=1000, blank=True, help_text='Google Docs URL')
    company_name = models.CharField(max_length=500, blank=True, help_text='Extracted company name')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Generated Resume'
        verbose_name_plural = 'Generated Resumes'
    
    def __str__(self):
        job_info = self.job_application.job_url[:30] if self.job_application.job_url else f"Job #{self.job_application.id}"
        return f"Resume for {job_info}... ({self.created_at.strftime('%Y-%m-%d')})"


class GeneratedCoverLetter(models.Model):
    """Model to store AI-generated cover letters"""
    job_application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name='generated_cover_letters'
    )
    content = models.TextField(help_text='Generated cover letter content')
    file_path = models.CharField(max_length=500, blank=True, help_text='Path to generated file')
    google_doc_id = models.CharField(max_length=500, blank=True, help_text='Google Docs ID')
    google_doc_url = models.URLField(max_length=1000, blank=True, help_text='Google Docs URL')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Generated Cover Letter'
        verbose_name_plural = 'Generated Cover Letters'
    
    def __str__(self):
        job_info = self.job_application.job_url[:30] if self.job_application.job_url else f"Job #{self.job_application.id}"
        return f"Cover Letter for {job_info}... ({self.created_at.strftime('%Y-%m-%d')})"
