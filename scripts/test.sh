#!/bin/bash

# Robotics Radar Test Script
# This script runs unit and integration tests

set -e  # Exit on any error

echo "🤖 Robotics Radar - Test Script"
echo "==============================="

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

# Create test directory if it doesn't exist
mkdir -p tests

# Run unit tests
echo "Running unit tests..."
python -m pytest tests/ -v --tb=short

# Run integration tests
echo "Running integration tests..."

# Test database operations
echo "Testing database operations..."
python -c "
import sys
sys.path.append('.')
from storage.database import DatabaseManager, Tweet
from datetime import datetime

try:
    db = DatabaseManager()
    
    # Test tweet insertion
    test_tweet = Tweet(
        id='test_123',
        text='This is a test robotics tweet',
        author_id='test_author',
        author_username='test_user',
        author_name='Test User',
        author_followers=1000,
        likes=50,
        retweets=10,
        replies=5,
        url='https://twitter.com/test_user/status/test_123',
        created_at=datetime.now(),
        score=85.5
    )
    
    success = db.insert_tweet(test_tweet)
    if success:
        print('✅ Database tweet insertion test passed')
    else:
        print('❌ Database tweet insertion test failed')
        exit(1)
    
    # Test analytics
    analytics = db.get_analytics_summary()
    if analytics['total_tweets'] > 0:
        print('✅ Database analytics test passed')
    else:
        print('❌ Database analytics test failed')
        exit(1)
        
except Exception as e:
    print(f'❌ Database integration test failed: {e}')
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
    
    # Test scoring calculation
    test_data = {
        'likes': 100,
        'retweets': 50,
        'replies': 25,
        'author_followers': 10000
    }
    
    score = model.calculate_final_score(test_data)
    if score > 0:
        print(f'✅ Scoring model test passed (score: {score:.2f})')
    else:
        print('❌ Scoring model test failed')
        exit(1)
        
    # Test score breakdown
    breakdown = model.get_score_breakdown(test_data)
    if 'final_score' in breakdown:
        print('✅ Score breakdown test passed')
    else:
        print('❌ Score breakdown test failed')
        exit(1)
        
except Exception as e:
    print(f'❌ Scoring model integration test failed: {e}')
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
    
    # Test keyword extraction
    test_text = 'This is a robotics research paper about autonomous systems and machine learning.'
    keywords = extractor.extract_keywords(test_text)
    if keywords:
        print(f'✅ Keyword extraction test passed (keywords: {keywords[:3]})')
    else:
        print('❌ Keyword extraction test failed')
        exit(1)
    
    # Test topic extraction
    topics = extractor.extract_topics(test_text)
    if topics:
        print(f'✅ Topic extraction test passed (topics: {topics})')
    else:
        print('❌ Topic extraction test failed')
        exit(1)
    
    # Test sentiment analysis
    sentiment = extractor.analyze_sentiment(test_text)
    if 'positive' in sentiment and 'negative' in sentiment:
        print('✅ Sentiment analysis test passed')
    else:
        print('❌ Sentiment analysis test failed')
        exit(1)
        
except Exception as e:
    print(f'❌ NLP module integration test failed: {e}')
    exit(1)
"

# Test feedback processor
echo "Testing feedback processor..."
python -c "
import sys
sys.path.append('.')
from feedback.feedback_processor import FeedbackProcessor

try:
    processor = FeedbackProcessor()
    
    # Test feedback processing
    success = processor.process_feedback(
        tweet_id='test_123',
        user_id='test_user',
        feedback_type='like'
    )
    
    if success:
        print('✅ Feedback processing test passed')
    else:
        print('❌ Feedback processing test failed')
        exit(1)
    
    # Test feedback summary
    summary = processor.get_feedback_summary('test_123')
    if 'total_feedback' in summary:
        print('✅ Feedback summary test passed')
    else:
        print('❌ Feedback summary test failed')
        exit(1)
        
except Exception as e:
    print(f'❌ Feedback processor integration test failed: {e}')
    exit(1)
"

# Test configuration loading
echo "Testing configuration loading..."
python -c "
import sys
sys.path.append('.')
import yaml

try:
    with open('config/keywords.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    required_keys = ['domain', 'keywords', 'languages', 'exclude_keywords']
    for key in required_keys:
        if key not in config:
            print(f'❌ Configuration test failed: missing {key}')
            exit(1)
    
    print('✅ Configuration loading test passed')
    print(f'   - Domain: {config[\"domain\"]}')
    print(f'   - Keywords: {len(config[\"keywords\"])}')
    print(f'   - Languages: {config[\"languages\"]}')
    
except Exception as e:
    print(f'❌ Configuration loading test failed: {e}')
    exit(1)
"

# Test notification modules (without actually sending)
echo "Testing notification modules..."
python -c "
import sys
sys.path.append('.')
from notifier.telegram_bot import TelegramNotifier
from notifier.email_sender import EmailNotifier

try:
    # Test Telegram notifier initialization
    telegram = TelegramNotifier()
    if hasattr(telegram, 'bot_token'):
        print('✅ Telegram notifier initialization test passed')
    else:
        print('❌ Telegram notifier initialization test failed')
        exit(1)
    
    # Test email notifier initialization
    email = EmailNotifier()
    if hasattr(email, 'smtp_server'):
        print('✅ Email notifier initialization test passed')
    else:
        print('❌ Email notifier initialization test failed')
        exit(1)
        
except Exception as e:
    print(f'❌ Notification modules test failed: {e}')
    exit(1)
"

# Test tweet fetcher (without API calls)
echo "Testing tweet fetcher..."
python -c "
import sys
sys.path.append('.')
from scraper.fetch_tweets import TweetFetcher

try:
    fetcher = TweetFetcher()
    
    # Test configuration loading
    if hasattr(fetcher, 'config') and fetcher.config:
        print('✅ Tweet fetcher configuration test passed')
    else:
        print('❌ Tweet fetcher configuration test failed')
        exit(1)
    
    # Test scoring model integration
    if hasattr(fetcher, 'scoring_model'):
        print('✅ Tweet fetcher scoring model integration test passed')
    else:
        print('❌ Tweet fetcher scoring model integration test failed')
        exit(1)
        
except Exception as e:
    print(f'❌ Tweet fetcher test failed: {e}')
    exit(1)
"

# Performance tests
echo "Running performance tests..."
python -c "
import sys
sys.path.append('.')
import time
from storage.database import DatabaseManager
from scoring.scoring_model import ScoringModel

try:
    # Test database performance
    start_time = time.time()
    db = DatabaseManager()
    analytics = db.get_analytics_summary()
    db_time = time.time() - start_time
    
    if db_time < 1.0:  # Should be under 1 second
        print(f'✅ Database performance test passed ({db_time:.3f}s)')
    else:
        print(f'❌ Database performance test failed ({db_time:.3f}s)')
        exit(1)
    
    # Test scoring performance
    start_time = time.time()
    model = ScoringModel()
    test_data = {'likes': 100, 'retweets': 50, 'replies': 25, 'author_followers': 10000}
    score = model.calculate_final_score(test_data)
    score_time = time.time() - start_time
    
    if score_time < 0.1:  # Should be under 0.1 seconds
        print(f'✅ Scoring performance test passed ({score_time:.3f}s)')
    else:
        print(f'❌ Scoring performance test failed ({score_time:.3f}s)')
        exit(1)
        
except Exception as e:
    print(f'❌ Performance test failed: {e}')
    exit(1)
"

echo ""
echo "🎉 All tests completed successfully!"
echo ""
echo "Test Summary:"
echo "✅ Unit tests passed"
echo "✅ Database integration tests passed"
echo "✅ Scoring model tests passed"
echo "✅ NLP module tests passed"
echo "✅ Feedback processor tests passed"
echo "✅ Configuration tests passed"
echo "✅ Notification module tests passed"
echo "✅ Tweet fetcher tests passed"
echo "✅ Performance tests passed"
echo ""
echo "The Robotics Radar system is ready for production use!" 