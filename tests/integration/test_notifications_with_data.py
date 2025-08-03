#!/usr/bin/env python3
"""
Test notifications with actual data from the database.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.database import DatabaseManager
from notifier.telegram_bot import TelegramNotifier
from notifier.email_sender import EmailNotifier

def load_env_vars():
    """Load environment variables from .env file."""
    load_dotenv()

async def test_notifications_with_data():
    """Test notifications with actual data from database."""
    print("🔍 Testing Notifications with Real Data...")
    print("=" * 60)
    
    # Load environment variables
    load_env_vars()
    
    # Initialize database and get top tweets
    db = DatabaseManager()
    top_tweets = db.get_top_tweets(limit=5)
    
    print(f"✅ Found {len(top_tweets)} top tweets in database")
    
    if not top_tweets:
        print("❌ No tweets found in database. Run the limited fetcher first.")
        return False
    
    # Show top tweets
    print("\n📊 Top Tweets from Database:")
    print("-" * 40)
    for i, tweet in enumerate(top_tweets, 1):
        print(f"{i}. Score: {tweet.score:.1f}")
        print(f"   Author: @{tweet.author_username}")
        print(f"   Text: {tweet.text[:80]}...")
        print(f"   Engagement: {tweet.likes} likes, {tweet.retweets} RTs")
        print()
    
    # Test Telegram notifications
    print("📤 Testing Telegram Notifications...")
    telegram_notifier = TelegramNotifier()
    
    if telegram_notifier.is_available():
        print("✅ Telegram notifier is available")
        
        # Send top tweets notification
        try:
            await telegram_notifier.send_top_tweets_sync(top_tweets)
            print("✅ Top tweets notification sent successfully")
        except Exception as e:
            print(f"❌ Error sending top tweets: {e}")
        
        # Send analytics report
        try:
            await telegram_notifier.send_analytics_report_sync()
            print("✅ Analytics report sent successfully")
        except Exception as e:
            print(f"❌ Error sending analytics report: {e}")
    else:
        print("❌ Telegram notifier not available")
    
    # Test Email notifications
    print("\n📧 Testing Email Notifications...")
    email_notifier = EmailNotifier()
    
    if email_notifier.is_available():
        print("✅ Email notifier is available")
        
        # Send top tweets notification
        try:
            email_notifier.send_top_tweets(top_tweets)
            print("✅ Top tweets email sent successfully")
        except Exception as e:
            print(f"❌ Error sending top tweets email: {e}")
        
        # Send analytics report
        try:
            email_notifier.send_analytics_report()
            print("✅ Analytics email sent successfully")
        except Exception as e:
            print(f"❌ Error sending analytics email: {e}")
    else:
        print("❌ Email notifier not available")
    
    print("\n" + "=" * 60)
    print("✅ Notification Test Complete!")
    print("=" * 60)
    
    return True

def main():
    """Main function."""
    print("🤖 Robotics Radar - Notification Test with Data")
    print("=" * 60)
    
    success = asyncio.run(test_notifications_with_data())
    
    if success:
        print("\n🎉 Notification test completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Check your Telegram for notifications from @RoboticsRadarBot")
        print("2. Check your email for notifications (if configured)")
        print("3. Visit the dashboard at http://localhost:8501")
        print("4. Run the system with: ./scripts/run.sh start")
    else:
        print("\n❌ Notification test failed!")
    
    return success

if __name__ == "__main__":
    main() 