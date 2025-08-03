#!/bin/bash

# Robotics Radar Installation Script
# This script sets up the Python environment and installs all dependencies

set -e  # Exit on any error

echo "🤖 Robotics Radar - Installation Script"
echo "========================================"

# Check if Python 3.11+ is available
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | sed 's/Python //' | cut -d. -f1,2)
required_version="3.11"

# Compare versions using awk for better compatibility
if python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
    echo "✅ Python $python_version found (>= $required_version)"
else
    echo "❌ Python $python_version found, but $required_version+ is required"
    echo "Please install Python 3.11 or higher"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "robotics-radar-env" ]; then
    echo "Virtual environment already exists. Removing..."
    rm -rf robotics-radar-env
fi

python3 -m venv robotics-radar-env
echo "✅ Virtual environment created"

# Activate virtual environment
echo "Activating virtual environment..."
source robotics-radar-env/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Download spaCy model
echo "Downloading spaCy model..."
python -m spacy download en_core_web_sm

# Create necessary directories
echo "Creating directories..."
mkdir -p data
mkdir -p logs

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOF
# Twitter API Credentials
TWITTER_API_KEY=your_twitter_api_key_here
TWITTER_API_SECRET=your_twitter_api_secret_here
TWITTER_ACCESS_TOKEN=your_twitter_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret_here

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_ALLOWED_USERS=your_telegram_user_id_here

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
EMAIL_RECIPIENTS=recipient1@example.com,recipient2@example.com

# Database Configuration
DATABASE_PATH=data/radar.db

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/robotics-radar.log
EOF
    echo "✅ .env file created - Please update with your credentials"
else
    echo "✅ .env file already exists"
fi

# Make scripts executable
echo "Making scripts executable..."
chmod +x scripts/*.sh

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Update the .env file with your API credentials"
echo "2. Run './scripts/bringup.sh' to initialize the database"
echo "3. Run './scripts/test.sh' to run tests"
echo "4. Run './scripts/run.sh' to start the application"
echo ""
echo "For more information, see the README.md file" 