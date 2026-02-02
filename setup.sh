#!/bin/bash

# Setup script for AI Resume & Cover Letter Generator

echo "🚀 Setting up AI Resume & Cover Letter Generator..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python found"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your GEMINI_API_KEY"
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p media/resumes
mkdir -p media/temp
mkdir -p static

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Create sample Excel template
echo "📊 Creating sample Excel template..."
python create_sample_excel.py

# Create superuser prompt
echo ""
echo "👤 Would you like to create a superuser account? (y/n)"
read -r create_superuser

if [ "$create_superuser" = "y" ] || [ "$create_superuser" = "Y" ]; then
    python manage.py createsuperuser
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file and add your GEMINI_API_KEY"
echo "   Get it from: https://makersuite.google.com/app/apikey"
echo ""
echo "2. (Optional) Set up Google Sheets integration:"
echo "   - Create a Google Cloud project"
echo "   - Enable Google Sheets API"
echo "   - Create service account and download credentials"
echo "   - Update GOOGLE_SHEETS_CREDENTIALS_FILE in .env"
echo ""
echo "3. Start the development server:"
echo "   python manage.py runserver"
echo ""
echo "4. Visit http://127.0.0.1:8000"
echo ""
echo "Happy coding! 🎉"
