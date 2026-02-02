"""
Views for resume generator application
"""
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, FileResponse
from django.conf import settings
from ..models import UserResume, JobApplication, GeneratedResume, GeneratedCoverLetter, GoogleDriveConfig
from ..repositories import (
    UserResumeRepository, JobApplicationRepository,
    GeneratedResumeRepository, GeneratedCoverLetterRepository
)
from ..services import ResumeProcessorService, AIResumeGeneratorService, GoogleDriveMonitorService
from ..services.external import GoogleDriveService


def home(request):
    """Home page view"""
    active_resume = UserResumeRepository.get_active_resume()
    job_applications = JobApplicationRepository.get_all()[:10]  # Latest 10
    
    context = {
        'active_resume': active_resume,
        'job_applications': job_applications,
    }
    return render(request, 'resume_generator/home.html', context)


def upload_resume(request):
    """Handle resume upload"""
    if request.method == 'POST':
        if 'resume_file' not in request.FILES:
            messages.error(request, 'No file uploaded')
            return redirect('resume_generator:home')
        
        resume_file = request.FILES['resume_file']
        user_name = request.POST.get('user_name', 'User')
        
        # Validate file extension
        allowed_extensions = ['.pdf', '.docx', '.txt']
        file_extension = os.path.splitext(resume_file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            messages.error(request, f'Invalid file type. Allowed: {", ".join(allowed_extensions)}')
            return redirect('resume_generator:home')
        
        try:
            # Create resume record
            user_resume = UserResumeRepository.create(
                user_name=user_name,
                file=resume_file
            )
            
            # Extract text from resume
            resume_processor = ResumeProcessorService()
            file_path = user_resume.file.path
            content = resume_processor.extract_text_from_file(file_path)
            
            # Update resume content
            UserResumeRepository.update_content(user_resume.id, content)
            
            messages.success(request, 'Resume uploaded successfully!')
            return redirect('resume_generator:home')
        
        except Exception as e:
            messages.error(request, f'Error uploading resume: {str(e)}')
            return redirect('resume_generator:home')
    
    return render(request, 'resume_generator/upload_resume.html')


def settings(request):
    """Application settings and configuration"""
    # Get existing config if any
    config = GoogleDriveConfig.objects.first()
    
    if request.method == 'POST':
        excel_file_id = request.POST.get('excel_file_id', '').strip()
        output_folder_id = request.POST.get('output_folder_id', '').strip()
        setup_headers = request.POST.get('setup_headers') == 'on'
        
        # Settings
        generate_new_resume = request.POST.get('generate_new_resume') == 'on'
        generate_recommendations = request.POST.get('generate_recommendations') == 'on'
        always_generate_cover_letter = request.POST.get('always_generate_cover_letter') == 'on'
        
        if not excel_file_id or not output_folder_id:
            messages.error(request, 'Please provide both Excel file ID and output folder ID')
            return redirect('resume_generator:settings')
        
        try:
            # Setup headers if requested
            if setup_headers:
                drive_service = GoogleDriveService()
                drive_service.setup_excel_headers(excel_file_id)
                messages.success(request, 'Excel headers configured successfully!')
            
            # Create or update config
            if config:
                config.excel_file_id = excel_file_id
                config.output_folder_id = output_folder_id
                config.generate_new_resume = generate_new_resume
                config.generate_recommendations = generate_recommendations
                config.always_generate_cover_letter = always_generate_cover_letter
                config.save()
            else:
                monitor_service = GoogleDriveMonitorService()
                result = monitor_service.start_monitoring(excel_file_id, output_folder_id)
                
                if result['success']:
                    config = GoogleDriveConfig.objects.first()
                    config.generate_new_resume = generate_new_resume
                    config.generate_recommendations = generate_recommendations
                    config.always_generate_cover_letter = always_generate_cover_letter
                    config.save()
                    messages.success(request, 'Settings saved successfully!')
                    return redirect('resume_generator:monitoring_status')
                else:
                    messages.error(request, f'Error: {result.get("error")}')
                    return redirect('resume_generator:settings')
            
            messages.success(request, 'Settings updated successfully!')
            return redirect('resume_generator:settings')
        
        except Exception as e:
            messages.error(request, f'Error saving settings: {str(e)}')
            return redirect('resume_generator:settings')
    
    context = {
        'config': config
    }
    return render(request, 'resume_generator/settings.html', context)


def process_jobs(request):
    """Process pending job applications"""
    pending_jobs = JobApplicationRepository.get_pending_jobs()
    
    if not pending_jobs:
        messages.info(request, 'No pending jobs to process')
        return redirect('resume_generator:home')
    
    ai_service = AIResumeGeneratorService()
    processed_count = 0
    
    for job in pending_jobs:
        try:
            # Update status to processing
            JobApplicationRepository.update_status(job.id, 'processing')
            
            # Get user resume content
            if job.user_resume:
                resume_content = job.user_resume.content
            else:
                active_resume = UserResumeRepository.get_active_resume()
                resume_content = active_resume.content if active_resume else ''
            
            # Generate resume if requested
            if job.generate_resume and resume_content:
                result = ai_service.generate_resume(
                    job,
                    resume_content,
                    job.additional_instructions
                )
                
                if result['success']:
                    GeneratedResumeRepository.create(
                        job_application=job,
                        content=result['content'],
                        recommendations=result.get('recommendations', '')
                    )
            
            # Generate cover letter if requested
            if job.generate_cover_letter and resume_content:
                result = ai_service.generate_cover_letter(
                    job,
                    resume_content,
                    job.additional_instructions
                )
                
                if result['success']:
                    GeneratedCoverLetterRepository.create(
                        job_application=job,
                        content=result['content']
                    )
            
            # Update status to completed
            JobApplicationRepository.update_status(job.id, 'completed')
            processed_count += 1
        
        except Exception as e:
            JobApplicationRepository.update_status(job.id, 'failed')
            messages.error(request, f'Error processing job {job.id}: {str(e)}')
    
    messages.success(request, f'Successfully processed {processed_count} job applications!')
    return redirect('resume_generator:home')


def job_details(request, job_id):
    """View details of a job application"""
    job = get_object_or_404(JobApplication, id=job_id)
    generated_resumes = GeneratedResumeRepository.get_by_job(job)
    generated_covers = GeneratedCoverLetterRepository.get_by_job(job)
    
    context = {
        'job': job,
        'generated_resumes': generated_resumes,
        'generated_covers': generated_covers,
    }
    return render(request, 'resume_generator/job_details.html', context)


def generate_resume(request, job_id):
    """Generate resume for a specific job"""
    job = get_object_or_404(JobApplication, id=job_id)
    
    try:
        # Get user resume content
        if job.user_resume:
            resume_content = job.user_resume.content
        else:
            active_resume = UserResumeRepository.get_active_resume()
            if not active_resume:
                messages.error(request, 'Please upload a resume first')
                return redirect('resume_generator:job_details', job_id=job_id)
            resume_content = active_resume.content
        
        # Generate resume
        ai_service = AIResumeGeneratorService()
        result = ai_service.generate_resume(
            job,
            resume_content,
            job.additional_instructions
        )
        
        if result['success']:
            generated_resume = GeneratedResumeRepository.create(
                job_application=job,
                content=result['content'],
                recommendations=result.get('recommendations', '')
            )
            messages.success(request, 'Resume generated successfully!')
        else:
            messages.error(request, f'Error generating resume: {result.get("error")}')
        
        return redirect('resume_generator:job_details', job_id=job_id)
    
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('resume_generator:job_details', job_id=job_id)


def generate_cover_letter(request, job_id):
    """Generate cover letter for a specific job"""
    job = get_object_or_404(JobApplication, id=job_id)
    
    try:
        # Get user resume content
        if job.user_resume:
            resume_content = job.user_resume.content
        else:
            active_resume = UserResumeRepository.get_active_resume()
            if not active_resume:
                messages.error(request, 'Please upload a resume first')
                return redirect('resume_generator:job_details', job_id=job_id)
            resume_content = active_resume.content
        
        # Generate cover letter
        ai_service = AIResumeGeneratorService()
        result = ai_service.generate_cover_letter(
            job,
            resume_content,
            job.additional_instructions
        )
        
        if result['success']:
            GeneratedCoverLetterRepository.create(
                job_application=job,
                content=result['content']
            )
            messages.success(request, 'Cover letter generated successfully!')
        else:
            messages.error(request, f'Error generating cover letter: {result.get("error")}')
        
        return redirect('resume_generator:job_details', job_id=job_id)
    
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('resume_generator:job_details', job_id=job_id)


def download_resume(request, resume_id):
    """Download generated resume as text file"""
    resume = get_object_or_404(GeneratedResume, id=resume_id)
    
    response = HttpResponse(resume.content, content_type='text/plain')
    filename = f'resume_{resume.job_application.id}_{resume.id}.txt'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


def download_cover_letter(request, cover_id):
    """Download generated cover letter as text file"""
    cover = get_object_or_404(GeneratedCoverLetter, id=cover_id)
    
    response = HttpResponse(cover.content, content_type='text/plain')
    filename = f'cover_letter_{cover.job_application.id}_{cover.id}.txt'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


def monitoring_status(request):
    """View monitoring status of Google Drive files"""
    monitor_service = GoogleDriveMonitorService()
    status = monitor_service.get_monitoring_status()
    
    context = {
        'status': status,
        'configs': status.get('configs', []) if status['success'] else []
    }
    return render(request, 'resume_generator/monitoring_status.html', context)


def start_monitoring(request, config_id):
    """Start monitoring a specific Google Drive file"""
    try:
        config = get_object_or_404(GoogleDriveConfig, id=config_id)
        monitor_service = GoogleDriveMonitorService()
        result = monitor_service.start_monitoring(config.excel_file_id, config.output_folder_id)
        
        if result['success']:
            messages.success(request, f'Started monitoring {config.excel_file_name}')
        else:
            messages.error(request, f'Error: {result.get("error")}')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('resume_generator:monitoring_status')


def stop_monitoring(request, config_id):
    """Stop monitoring a specific Google Drive file"""
    try:
        monitor_service = GoogleDriveMonitorService()
        result = monitor_service.stop_monitoring(config_id=config_id)
        
        if result['success']:
            messages.success(request, 'Stopped monitoring')
        else:
            messages.error(request, f'Error: {result.get("error")}')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('resume_generator:monitoring_status')


def process_drive_now(request, config_id):
    """Manually process a Google Drive Excel file now"""
    try:
        monitor_service = GoogleDriveMonitorService()
        result = monitor_service.process_drive_excel(config_id)
        
        if result['success']:
            messages.success(request, 
                f'Processed {result["processed"]} jobs, '
                f'skipped {result["skipped"]}, '
                f'errors {result["errors"]}')
        else:
            messages.error(request, f'Error: {result.get("error")}')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('resume_generator:monitoring_status')
