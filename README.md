# AI Resume & Cover Letter Generator

Automated resume and cover letter generation system using Google Drive, Google Docs API, and Gemini AI.

## Features

- 📝 **AI-Powered Generation**: Tailored resumes and cover letters using Gemini AI
- 📁 **Google Drive Integration**: Monitor Excel files and auto-generate documents
- 🔄 **Continuous Monitoring**: Automatic processing of new job applications
- 📄 **Combined Documents**: Resume + cover letter in single Google Doc
- 🏢 **Smart Company Detection**: Auto-extracts company names
- ⚡ **Batch Processing**: Process multiple jobs simultaneously

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [API Configuration](#api-configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Commands](#commands)
- [Tech Stack](#tech-stack)

## Prerequisites

### Required Software

- **Python 3.8+**: Download from [python.org](https://www.python.org/downloads/)
- **pip**: Python package installer (included with Python)
- **Git**: Version control system
- **Google Account**: For Drive and Gemini API access

### Verify Installation

```bash
python --version  # Should show Python 3.8 or higher
pip --version     # Should show pip version
git --version     # Should show git version
```

## Installation & Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/rahul0van/job_hunt_beta.git
cd job_hunt_beta
```

### Step 2: Create Virtual Environment (Recommended)

**On macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Setup Database

```bash
python manage.py migrate
```

## API Configuration

### 1. Get Gemini API Key

1. **Visit Google AI Studio**
   - Go to [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
   - Sign in with your Google account

2. **Create API Key**
   - Click "Create API Key"
   - Select "Create API key in new project" or choose existing project
   - Copy the generated API key

3. **Add to Environment**
   - Create `.env` file in project root:
   ```env
   SECRET_KEY=your-django-secret-key-here
   DEBUG=True
   GEMINI_API_KEY=your-gemini-api-key-here
   ```

### 2. Setup Google Drive & Docs API

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Click "Create Project"
   - Enter project name (e.g., "Resume Generator")
   - Click "Create"

2. **Enable Required APIs**
   - In your project, go to "APIs & Services" > "Library"
   - Search and enable these APIs:
     - **Google Drive API**
     - **Google Docs API**
     - **Google Sheets API**

3. **Create Service Account**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Enter service account name: `resume-generator-sa`
   - Click "Create and Continue"
   - Grant role: **Editor** (or Project > Editor)
   - Click "Done"

4. **Download Credentials**
   - Click on the created service account
   - Go to "Keys" tab
   - Click "Add Key" > "Create new key"
   - Select "JSON" format
   - Click "Create"
   - File downloads automatically

5. **Add Credentials to Project**
   - Rename downloaded file to `credentials.json`
   - Move it to project root directory:
   ```
   cover_resume_ai/
   ├── credentials.json  ← Place here
   ├── manage.py
   ├── requirements.txt
   └── ...
   ```

6. **Share Google Drive Folders/Files**
   - Open the `credentials.json` file
   - Copy the `client_email` value (looks like: `xxx@xxx.iam.gserviceaccount.com`)
   - In Google Drive, share your:
     - **Job tracking Excel/Sheet** with this email (Editor access)
     - **Output folder** with this email (Editor access)

### 3. Generate Django Secret Key

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and add to `.env` file as `SECRET_KEY`.

### 4. Final `.env` File

Your `.env` file should look like:

```env
SECRET_KEY=django-insecure-your-generated-secret-key-here
DEBUG=True
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### Step 5: Run the Server

```bash
python manage.py runserver
```

Visit: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## Getting Started - First Time Usage

### 1. Upload Your Resume

1. Navigate to [http://127.0.0.1:8000/upload-resume/](http://127.0.0.1:8000/upload-resume/)
2. Upload your master resume (PDF, DOCX, or TXT format)
3. System will extract and store the content

### 2. Create Job Tracking Spreadsheet

**Option A: Use Sample Template**
```bash
python create_sample_excel.py
```
This creates `static/sample_jobs.xlsx` with proper columns.

**Option B: Create Manually in Google Sheets**

Create a Google Sheet with these columns (exact names, case-insensitive):

| Column Name | Required | Description |
|------------|----------|-------------|
| `job_url` | Optional* | URL to job posting |
| `job_description` | Optional* | Full job description text |
| `additional_instructions` | No | Custom instructions for AI |
| `generate_resume` | No | yes/no (default: yes) |
| `generate_cover` | No | yes/no (default: yes) |
| `generate_new_resume` | No | yes/no - If no, only generates cover letter |
| `company_name` | No | Auto-filled by system |
| `resume_generated` | No | Auto-filled: yes/no |
| `cover_letter_generated` | No | Auto-filled: yes/no |
| `google_doc_url` | No | Auto-filled with document link |
| `recommendations` | No | Auto-filled with AI suggestions |

**\*Note:** Either `job_url` OR `job_description` must be provided for each row.

**Example Row:**
```
job_url: https://www.linkedin.com/jobs/view/123456
job_description: (leave empty if URL provided)
additional_instructions: Emphasize Python and Django experience
generate_resume: yes
generate_cover: yes
generate_new_resume: yes
```

### 3. Get Google Drive IDs

**Get Excel/Sheet File ID:**
1. Open your Google Sheet
2. Look at URL: `https://docs.google.com/spreadsheets/d/FILE_ID_HERE/edit`
3. Copy the FILE_ID_HERE part

**Get Output Folder ID:**
1. Open Google Drive folder where documents should be saved
2. Look at URL: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`
3. Copy the FOLDER_ID_HERE part

**Share with Service Account:**
1. Open `credentials.json` and copy the `client_email`
2. Share the Sheet and Folder with this email (Editor permissions)

### 4. Configure System Settings

1. Navigate to [http://127.0.0.1:8000/settings/](http://127.0.0.1:8000/settings/)
2. Enter:
   - **Excel File ID**: The FILE_ID from your Google Sheet
   - **Output Folder ID**: The FOLDER_ID for generated documents
3. Configure generation preferences:
   - ✅ **Generate Tailored Resume**: Creates customized resume for each job
   - ✅ **Generate AI Recommendations**: Provides improvement suggestions
   - ✅ **Always Generate Cover Letter**: Generates cover letter even if resume generation is off
4. Click "Save Settings"

### 5. Setup Headers (First Time Only)

1. Go to [http://127.0.0.1:8000/setup-google-drive/](http://127.0.0.1:8000/setup-google-drive/)
2. Check "Setup headers in Excel file"
3. Click "Initialize Headers"
4. System will add all required column headers to your sheet

### 6. Start Processing Jobs

**Method 1: Continuous Monitoring (Recommended)**
```bash
python manage.py monitor_drive --interval 60
```
- Checks every 60 seconds for new/updated jobs
- Automatically processes changes
- Runs continuously in background
- Press `Ctrl+C` to stop

**Method 2: Manual Processing**
1. Go to [http://127.0.0.1:8000/monitoring-status/](http://127.0.0.1:8000/monitoring-status/)
2. Click "Process Now" button
3. Processes all pending jobs immediately

**Method 3: Web-Based Monitoring**
1. Go to [http://127.0.0.1:8000/monitoring-status/](http://127.0.0.1:8000/monitoring-status/)
2. Click "Start Monitoring"
3. Stop monitoring when needed

### 7. Add Jobs to Your Sheet

Simply add job information to your Google Sheet:

**Example 1 - Using Job URL:**
```
job_url: https://www.linkedin.com/jobs/view/3845261234
additional_instructions: Focus on cloud architecture experience
```

**Example 2 - Using Job Description:**
```
job_url: (leave empty)
job_description: We are seeking a Senior Python Developer with 5+ years experience in Django, REST APIs, and PostgreSQL. Must have experience with AWS and Docker.
additional_instructions: Highlight my DevOps skills
```

The system will automatically:
- ✅ Detect new/changed rows
- ✅ Extract or use job description
- ✅ Generate tailored resume and cover letter
- ✅ Create combined Google Doc
- ✅ Upload to output folder
- ✅ Update sheet with status and link

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

# Create sample Excel template
python create_sample_excel.py

# Generate Django secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Troubleshooting

### Common Issues

**1. `credentials.json` not found**
- Ensure `credentials.json` is in the project root
- Check file name is exactly `credentials.json`
- Verify service account has Drive and Docs API enabled

**2. Permission denied on Google Drive**
- Open `credentials.json` and copy `client_email`
- Share your Google Sheet with this email (Editor access)
- Share your output folder with this email (Editor access)

**3. Gemini API errors**
- Verify `GEMINI_API_KEY` in `.env` file
- Check API key is active at [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- Ensure you haven't exceeded free tier limits

**4. "Job URL column not found"**
- Use "Setup Headers" feature in web interface
- OR manually add column headers to your sheet
- Column names are case-insensitive but must match exactly

**5. Job scraping fails (403 Forbidden)**
- Some websites block automated scraping
- Solution: Paste job description in `job_description` column instead
- Leave `job_url` empty and provide full description text

**6. Module import errors**
```bash
pip install -r requirements.txt  # Reinstall dependencies
python manage.py migrate          # Update database
```

**7. Database migration issues**
```bash
# Delete db.sqlite3 and migrations (WARNING: loses data)
rm db.sqlite3
rm -rf resume_generator/migrations/
python manage.py makemigrations resume_generator
python manage.py migrate
```

### Environment Variables

Create `.env` file in project root:

```env
# Required
SECRET_KEY=your-django-secret-key
GEMINI_API_KEY=your-gemini-api-key

# Optional
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### File Structure Requirements

```
cover_resume_ai/
├── .env                    # Environment variables (create this)
├── credentials.json        # Google service account (download from Cloud Console)
├── db.sqlite3             # Database (auto-created)
├── manage.py
├── requirements.txt
└── ...
```

## FAQ

### Q: Do I need to pay for Gemini API?
A: Gemini API has a generous free tier. Check [pricing](https://ai.google.dev/pricing) for current limits.

### Q: Can I use Excel files instead of Google Sheets?
A: Yes! Upload Excel files to Google Drive and share with service account. The system reads .xlsx files.

### Q: What happens if job scraping fails?
A: Paste the job description in the `job_description` column. The system will use it instead of scraping.

### Q: Can I process jobs manually?
A: Yes! Use the "Process Now" button at `/monitoring-status/` or run one-time processing.

### Q: How do I update my resume?
A: Upload a new resume at `/upload-resume/`. The latest resume will be used for all new generations.

### Q: Can I delete old jobs from the sheet?
A: Yes, just delete rows. System only processes rows with pending status.

### Q: Where are generated documents stored?
A: In the Google Drive output folder you specified. Each job gets a combined resume+cover letter document.

## Tips for Best Results

### Resume Tips
- Upload a comprehensive master resume with all skills and experiences
- Use clear section headers (Education, Experience, Skills, etc.)
- Include quantifiable achievements

### Job Description Tips
- Provide complete job descriptions (not just snippets)
- Include requirements, responsibilities, and company info
- Use the `additional_instructions` field to highlight specific experiences

### Additional Instructions Examples
- "Emphasize cloud architecture and AWS experience"
- "Focus on leadership and team management skills"
- "Highlight open-source contributions"
- "Mention experience with healthcare industry"
- "Include relevant certifications prominently"

### Processing Tips
- Start with monitoring interval of 60-120 seconds to avoid rate limits
- Process 5-10 jobs at a time for best performance
- Review and edit generated documents before sending
- Use `generate_new_resume: no` if you only need cover letters

## Tech Stack

- **Backend**: Django 4.2
- **AI**: Google Gemini 2.5 Flash
- **Cloud**: Google Drive API, Google Docs API
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Architecture**: MVC with Repository Pattern
- **Web Scraping**: BeautifulSoup4, Requests

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Support

For issues or questions:
- Open an issue on GitHub
- Check the [Troubleshooting](#troubleshooting) section
- Review [SETTINGS_FEATURE.md](SETTINGS_FEATURE.md) for configuration details

## License

MIT License
