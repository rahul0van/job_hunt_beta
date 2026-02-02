from django.contrib import admin
from .models import UserResume, JobApplication, GeneratedResume, GeneratedCoverLetter, GoogleDriveConfig

@admin.register(GoogleDriveConfig)
class GoogleDriveConfigAdmin(admin.ModelAdmin):
    list_display = ['id', 'excel_file_name', 'is_monitoring', 'last_checked', 'created_at']
    list_filter = ['is_monitoring', 'created_at']
    search_fields = ['excel_file_name', 'excel_file_id']

@admin.register(UserResume)
class UserResumeAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_name', 'uploaded_at', 'is_active']
    list_filter = ['is_active', 'uploaded_at']
    search_fields = ['user_name']

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ['id', 'job_url', 'company_name', 'generate_resume', 'generate_cover_letter', 'generate_new_resume', 
                   'resume_generated', 'cover_letter_generated', 'status', 'created_at']
    list_filter = ['status', 'generate_resume', 'generate_cover_letter', 'generate_new_resume',
                   'resume_generated', 'cover_letter_generated', 'created_at']
    search_fields = ['job_url', 'company_name', 'additional_instructions']

@admin.register(GeneratedResume)
class GeneratedResumeAdmin(admin.ModelAdmin):
    list_display = ['id', 'job_application', 'company_name', 'google_doc_url', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'company_name']

@admin.register(GeneratedCoverLetter)
class GeneratedCoverLetterAdmin(admin.ModelAdmin):
    list_display = ['id', 'job_application', 'google_doc_url', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content']
