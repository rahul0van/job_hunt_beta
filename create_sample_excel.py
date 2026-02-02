"""
Script to create sample Excel template
"""
import pandas as pd
import os

# Sample data
data = {
    'job_url': [
        'https://www.linkedin.com/jobs/view/12345',
        '',
        'https://example.com/careers/software-engineer',
    ],
    'job_description': [
        '',
        'We are looking for a Senior Python Developer with 5+ years of experience in Django, REST APIs, and cloud technologies. Must have strong leadership skills and experience managing teams.',
        '',
    ],
    'additional_instructions': [
        'Focus on Python and Django experience',
        'Emphasize leadership and team management skills',
        'Highlight machine learning and AI projects',
    ],
    'generate_resume': ['yes', 'yes', 'yes'],
    'generate_cover': ['yes', 'yes', 'no'],
    'generate_new_resume': ['yes', 'no', 'yes'],
    'resume_generated': ['no', 'no', 'no'],
    'cover_letter_generated': ['no', 'no', 'no'],
    'recommendations': ['', '', '']
}

# Create DataFrame
df = pd.DataFrame(data)

# Create static directory if it doesn't exist
os.makedirs('static', exist_ok=True)

# Save to Excel
df.to_excel('static/sample_jobs.xlsx', index=False)

print("✓ Sample Excel template created: static/sample_jobs.xlsx")
print(f"\nColumns: {', '.join(df.columns)}")
print(f"Sample rows: {len(df)}")
print("\nFeatures:")
print("  - job_url: URL of job posting (optional if job_description is provided)")
print("  - job_description: Paste full job description here (optional if job_url is provided)")
print("  - At least one of job_url or job_description must be provided")
print("  - generate_new_resume: If 'no', only cover letter + recommendations are generated")
print("  - resume_generated: System updates to 'yes' when complete")
print("  - cover_letter_generated: System updates to 'yes' when complete")
print("  - recommendations: AI fills with resume improvement suggestions")
