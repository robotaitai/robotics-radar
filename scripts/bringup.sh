#!/bin/bash

# Robotics Radar Bringup Script
# This script initializes the database and sets up the environment

set -e  # Exit on any error

echo "🤖 Robotics Radar - Bringup Script"
echo "=================================="

# Check if virtual environment exists
if [ ! -d "robotics-radar-env" ]; then
    echo "❌ Virtual environment not found. Please run './scripts/install.sh' first"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source robotics-radar-env/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please run './scripts/install.sh' first"
    exit 1
fi

# Load environment variables
echo "Loading environment variables..."
set -a  # automatically export all variables
source .env
set +a

# Check required environment variables
echo "Checking required environment variables..."
required_vars=(
    "TWITTER_API_KEY"
    "TWITTER_API_SECRET"
    "TWITTER_ACCESS_TOKEN"
    "TWITTER_ACCESS_TOKEN_SECRET"
)

missing_vars=()
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ] || [ "${!var}" = "your_$(echo $var | tr '[:upper:]' '[:lower:]')_here" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ Missing or invalid environment variables:"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Please update the .env file with your actual credentials"
    exit 1
fi

echo "✅ All required environment variables are set"

# Initialize database
echo "Initializing database..."
python -c "
import sys
sys.path.append('.')
from storage.database import DatabaseManager

try:
    db = DatabaseManager()
    print('✅ Database initialized successfully')
except Exception as e:
    print(f'❌ Error initializing database: {e}')
    exit(1)
"

# Test database connection
echo "Testing database connection..."
python -c "
import sys
sys.path.append('.')
from storage.database import DatabaseManager

try:
    db = DatabaseManager()
    analytics = db.get_analytics_summary()
    print('✅ Database connection test successful')
    print(f'   - Total tweets: {analytics[\"total_tweets\"]}')
    print(f'   - Total authors: {analytics[\"total_authors\"]}')
except Exception as e:
    print(f'❌ Database connection test failed: {e}')
    exit(1)
"

# Test scoring model
echo "Testing scoring model..."
python -c "
import sys
sys.path.append('.')
from scoring.scoring_model import ScoringModel

try:
    model = ScoringModel()
    test_data = {
        'likes': 100,
        'retweets': 50,
        'replies': 25,
        'author_followers': 10000
    }
    score = model.calculate_final_score(test_data)
    print(f'✅ Scoring model test successful (score: {score:.2f})')
except Exception as e:
    print(f'❌ Scoring model test failed: {e}')
    exit(1)
"

# Test NLP module
echo "Testing NLP module..."
python -c "
import sys
sys.path.append('.')
from nlp.keyword_extraction import KeywordExtractor

try:
    extractor = KeywordExtractor()
    keywords = extractor.extract_keywords('This is a test robotics tweet about autonomous systems.')
    print(f'✅ NLP module test successful (keywords: {keywords[:3]})')
except Exception as e:
    print(f'❌ NLP module test failed: {e}')
    exit(1)
"

# Create log directory
echo "Setting up logging..."
mkdir -p logs
touch logs/robotics-radar.log

# Test configuration
echo "Testing configuration..."
python -c "
import sys
sys.path.append('.')
import yaml

try:
    with open('config/keywords.yaml', 'r') as file:
        config = yaml.safe_load(file)
    print(f'✅ Configuration test successful')
    print(f'   - Domain: {config.get(\"domain\", \"unknown\")}')
    print(f'   - Keywords: {len(config.get(\"keywords\", []))}')
    print(f'   - Languages: {config.get(\"languages\", [])}')
except Exception as e:
    print(f'❌ Configuration test failed: {e}')
    exit(1)
"

echo ""
echo "🎉 Bringup completed successfully!"
echo ""
echo "The Robotics Radar system is ready to run."
echo ""
echo "Available commands:"
echo "  ./scripts/test.sh    - Run tests"
echo "  ./scripts/run.sh     - Start the scheduler"
echo "  streamlit run analytics/dashboard.py  - Start the dashboard"
echo ""
echo "For more information, see the README.md file" 