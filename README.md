# AI Resume & Cover Letter Generator

Automated resume and cover letter generation system using Google Drive, Google Docs API, and Gemini AI.

## Features

- 📝 **AI-Powered Generation**: Tailored resumes and cover letters using Gemini AI
- 📁 **Google Drive Integration**: Monitor Excel files and auto-generate documents
- 🔄 **Continuous Monitoring**: Automatic processing of new job applications
- 📄 **Combined Documents**: Resume + cover letter in single Google Doc
- 🏢 **Smart Company Detection**: Auto-extracts company names
- ⚡ **Batch Processing**: Process multiple jobs simultaneously

## Quick Start

### 1. Installation

```bash
git clone <repository>
cd cover_resume_ai
pip install -r requirements.txt
```

### 2. Configuration

Create `.env` file:
```env
SECRET_KEY=your-django-secret-key
DEBUG=True
GEMINI_API_KEY=your-gemini-api-key
```

Add `credentials.json` (Google Service Account) to project root.

### 3. Setup Database

```bash
python manage.py migrate
```

### 4. Run Server

```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000/

## Project Structure (MVC Architecture)

```
cover_resume_ai/
├── resume_generator/
│   ├── controllers/          # Controllers (Views)
│   │   └── views.py
│   ├── models.py            # Data models
│   ├── repositories/        # Data access layer
│   │   └── job_repositories.py
│   ├── services/            # Business logic
│   │   ├── ai/             # AI services
│   │   │   └── gemini_service.py
│   │   ├── external/       # External APIs
│   │   │   └── google_drive_service.py
│   │   ├── resume_service.py
│   │   └── google_drive_monitor_service.py
│   ├── management/         # Django commands
│   ├── migrations/         # Database migrations
│   └── templates/          # HTML templates
├── static/                 # Static files
├── media/                  # Uploaded files
└── cover_resume_ai/        # Django settings
```

## Usage

### 1. Upload Resume
- Go to `/upload-resume/`
- Upload your resume (PDF/DOCX/TXT)

### 2. Configure Settings
- Go to `/settings/`
- Add Google Sheets File ID (your job application spreadsheet)
- Add Output Folder ID (where to save generated documents)
- Configure generation settings:
  - **Generate Tailored Resume**: Create customized resume for each job
  - **Generate AI Recommendations**: Get improvement suggestions
  - **Always Generate Cover Letter**: Always create cover letters

### 3. Setup Google Sheet

Create a Google Sheet with these columns:
- `job_url` - Job posting URL (optional if job_description is provided)
- `job_description` - Full job description text (optional if job_url is provided)
- `additional_instructions` - Special instructions for AI (optional)
- `company_name` - Company name (auto-filled)
- `resume_generated` - Status (auto-filled: yes/no)
- `cover_letter_generated` - Status (auto-filled: yes/no)
- `google_doc_url` - Link to generated doc (auto-filled)
- `recommendations` - AI suggestions (auto-filled)

**Note:** You must provide either `job_url` OR `job_description`. If `job_url` is empty, the system will use the `job_description` column.

### 4. Start Continuous Monitoring

**Option A: Using Management Command (Recommended)**
```bash
python manage.py monitor_drive --interval 60
```
This will continuously check your Google Sheet every 60 seconds for changes.

**Option B: Using Web Interface**
- Go to `/monitoring-status/`
- Click "Start Monitoring" or "Process Now"

### 5. How It Works

1. **Add job information** to your Google Sheet (job URL or job description)
2. **System automatically detects** new/changed rows
3. **Generates** resume + cover letter using AI
4. **Saves** combined document to Google Drive
5. **Updates** Google Sheet with status and document link
6. **You can**:
   - Add new rows anytime
   - Use job URLs for automatic scraping
   - Paste job descriptions directly if URL is unavailable
   - Remove old rows
   - Update URLs
   - Change instructions
   - System processes changes automatically!

## Commands

```bash
# Start continuous monitoring (checks every 60 seconds)
python manage.py monitor_drive --interval 60

# Custom interval (checks every 30 seconds)
python manage.py monitor_drive --interval 30

# Run development server
python manage.py runserver

# Apply database migrations
python manage.py migrate
```
- Go to `/setup-google-drive/`
- Enter Excel file ID and output folder ID
- Enable header setup (auto-configures Excel columns)

### 3. Process Jobs
- Add job URLs to your Google Sheet
- Click "Process Now" or enable auto-monitoring
- System generates documents in Google Drive

## Tech Stack

- **Backend**: Django 4.2
- **AI**: Google Gemini 2.5 Flash
- **Cloud**: Google Drive API, Google Docs API
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Architecture**: MVC with Repository Pattern

## License

MIT License
