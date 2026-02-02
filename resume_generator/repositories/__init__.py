"""
Repositories - Data access layer
"""
from .job_repositories import (
    UserResumeRepository,
    JobApplicationRepository,
    GeneratedResumeRepository,
    GeneratedCoverLetterRepository
)

__all__ = [
    'UserResumeRepository',
    'JobApplicationRepository',
    'GeneratedResumeRepository',
    'GeneratedCoverLetterRepository'
]
