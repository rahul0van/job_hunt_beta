from django.urls import path
from .controllers import views

app_name = 'resume_generator'

urlpatterns = [
    path('', views.home, name='home'),
    path('upload-resume/', views.upload_resume, name='upload_resume'),
    path('settings/', views.settings, name='settings'),
    path('process-jobs/', views.process_jobs, name='process_jobs'),
    path('job-details/<int:job_id>/', views.job_details, name='job_details'),
    path('generate-resume/<int:job_id>/', views.generate_resume, name='generate_resume'),
    path('generate-cover-letter/<int:job_id>/', views.generate_cover_letter, name='generate_cover_letter'),
    path('download-resume/<int:resume_id>/', views.download_resume, name='download_resume'),
    path('download-cover/<int:cover_id>/', views.download_cover_letter, name='download_cover'),
    
    # Google Drive monitoring endpoints
    path('monitoring-status/', views.monitoring_status, name='monitoring_status'),
    path('start-monitoring/<int:config_id>/', views.start_monitoring, name='start_monitoring'),
    path('stop-monitoring/<int:config_id>/', views.stop_monitoring, name='stop_monitoring'),
    path('process-drive-now/<int:config_id>/', views.process_drive_now, name='process_drive_now'),
]
