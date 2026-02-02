@echo off
REM Setup script for AI Resume & Cover Letter Generator (Windows)

echo Setting up AI Resume ^& Cover Letter Generator...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python 3.8 or higher.
    exit /b 1
)

echo Python found

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo Please edit .env file and add your GEMINI_API_KEY
) else (
    echo .env file already exists
)

REM Create necessary directories
echo Creating necessary directories...
if not exist media\resumes mkdir media\resumes
if not exist media\temp mkdir media\temp
if not exist static mkdir static

REM Run migrations
echo Running database migrations...
python manage.py makemigrations
python manage.py migrate

REM Create sample Excel template
echo Creating sample Excel template...
python create_sample_excel.py

REM Create superuser prompt
echo.
set /p create_superuser="Would you like to create a superuser account? (y/n): "

if /i "%create_superuser%"=="y" (
    python manage.py createsuperuser
)

echo.
echo Setup complete!
echo.
echo Next steps:
echo 1. Edit .env file and add your GEMINI_API_KEY
echo    Get it from: https://makersuite.google.com/app/apikey
echo.
echo 2. (Optional) Set up Google Sheets integration
echo.
echo 3. Start the development server:
echo    python manage.py runserver
echo.
echo 4. Visit http://127.0.0.1:8000
echo.
echo Happy coding!

pause
