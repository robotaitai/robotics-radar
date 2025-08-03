#!/usr/bin/env python3
"""
Test script to send a Telegram message using the exact same format as the scheduler.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from notifier.telegram_bot import TelegramNotifier

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Test Telegram notification with scheduler format."""
    print("🤖 Robotics Radar - Scheduler Telegram Test")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Check environment variables
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    allowed_users = os.getenv('TELEGRAM_ALLOWED_USERS')
    
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment")
        return False
    
    if not allowed_users:
        print("❌ TELEGRAM_ALLOWED_USERS not found in environment")
        return False
    
    print(f"✅ Telegram bot token found")
    print(f"✅ Allowed users: {allowed_users}")
    
    # Create notifier
    notifier = TelegramNotifier()
    
    if not notifier.is_available():
        print("❌ Telegram notifier is not available")
        return False
    
    # Create a test message similar to what the scheduler sends
    from storage.database import Tweet
    
    # Create a test tweet
    test_tweet = Tweet(
        id="test_123",
        text="This is a test message from the scheduler to verify Telegram notifications are working!",
        author_id="test_user",
        author_username="test_user",
        author_name="Test User",
        author_followers=1000,
        likes=50,
        retweets=10,
        replies=5,
        url="https://x.com/test_user/status/test_123",
        created_at=datetime.now(),
        score=100.0,
        topics=["test", "robotics"],
        summary="Test summary for debugging Telegram notifications"
    )
    
    test_tweets = [test_tweet]
    
    print("Sending test message using scheduler format...")
    
    try:
        # Send using the same method as scheduler
        notifier.send_top_tweets_sync(test_tweets)
        print("✅ Test message sent successfully using scheduler format")
        return True
    except Exception as e:
        print(f"❌ Error sending test message: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Scheduler Telegram test completed successfully!")
        print("Check your Telegram for the test message from @RoboticsRadarBot")
    else:
        print("\n❌ Scheduler Telegram test failed!")
    sys.exit(0 if success else 1) 