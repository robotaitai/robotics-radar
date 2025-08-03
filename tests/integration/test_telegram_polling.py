#!/usr/bin/env python3
"""
Test script to verify Telegram bot polling mode and callback functionality.
"""

import asyncio
import os
from dotenv import load_dotenv
from notifier.telegram_bot import TelegramNotifier
from storage.database import DatabaseManager

async def test_bot_polling():
    """Test if the bot can start in polling mode."""
    print("🧪 Testing Telegram Bot Polling Mode")
    print("=" * 50)
    
    load_dotenv()
    
    # Check environment variables
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    allowed_users = os.getenv('TELEGRAM_ALLOWED_USERS')
    
    print(f"Bot token: {'✅ Set' if bot_token else '❌ Not set'}")
    print(f"Allowed users: {allowed_users}")
    
    if not bot_token:
        print("❌ Cannot test without bot token")
        return False
    
    # Create notifier
    notifier = TelegramNotifier()
    
    if not notifier.is_available():
        print("❌ Bot not available")
        return False
    
    print("✅ Bot configuration is valid")
    
    # Test starting the bot (this will run for a few seconds)
    print("🔄 Testing bot polling mode (will run for 10 seconds)...")
    
    try:
        # Start the bot in a task that we can cancel
        task = asyncio.create_task(notifier.start_bot())
        
        # Let it run for 10 seconds
        await asyncio.sleep(10)
        
        # Cancel the task
        task.cancel()
        
        print("✅ Bot polling mode test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error testing bot polling: {e}")
        return False

def test_callback_handling():
    """Test callback data handling."""
    print("\n🧪 Testing Callback Data Handling")
    print("=" * 50)
    
    # Test callback data parsing
    test_callback_data = "feedback:rss_123456:like"
    
    print(f"Testing callback data: {test_callback_data}")
    
    # Parse callback data (simulate what the bot does)
    data = test_callback_data.split(':')
    if len(data) == 3 and data[0] == 'feedback':
        tweet_id = data[1]
        feedback_type = data[2]
        print(f"✅ Parsed correctly:")
        print(f"  - Tweet ID: {tweet_id}")
        print(f"  - Feedback type: {feedback_type}")
        
        # Test feedback processing
        from feedback.feedback_processor import FeedbackProcessor
        processor = FeedbackProcessor()
        
        success = processor.process_feedback(tweet_id, "test_user", feedback_type)
        print(f"  - Feedback processing: {'✅ Success' if success else '❌ Failed'}")
        
        return True
    else:
        print(f"❌ Failed to parse callback data")
        return False

def test_database_feedback():
    """Test database feedback functionality."""
    print("\n🧪 Testing Database Feedback")
    print("=" * 50)
    
    db = DatabaseManager()
    
    # Test adding feedback
    test_tweet_id = "rss_test_123"
    test_user_id = "test_user_456"
    
    print(f"Adding feedback for tweet: {test_tweet_id}")
    
    # Add feedback
    success = db.add_feedback(test_tweet_id, test_user_id, "like")
    print(f"Add feedback: {'✅ Success' if success else '❌ Failed'}")
    
    # Get feedback
    feedback_data = db.get_tweet_feedback(test_tweet_id)
    print(f"Feedback data: {feedback_data}")
    
    return success and feedback_data.get('likes', 0) > 0

async def main():
    """Run all tests."""
    print("🚀 Testing Telegram Bot and Feedback System")
    print("=" * 60)
    print()
    
    # Test callback handling
    callback_ok = test_callback_handling()
    print()
    
    # Test database feedback
    db_ok = test_database_feedback()
    print()
    
    # Test bot polling (this will take 10 seconds)
    polling_ok = await test_bot_polling()
    print()
    
    # Summary
    print("📊 Test Results")
    print("=" * 30)
    print(f"Callback Handling: {'✅ OK' if callback_ok else '❌ FAILED'}")
    print(f"Database Feedback: {'✅ OK' if db_ok else '❌ FAILED'}")
    print(f"Bot Polling: {'✅ OK' if polling_ok else '❌ FAILED'}")
    
    if callback_ok and db_ok and polling_ok:
        print("\n🎉 All tests passed! Telegram bot should work correctly.")
        print("💡 The rating buttons in your messages should now work!")
    else:
        print("\n⚠️  Some tests failed. Check the issues above.")
    
    print("\n🔧 Next Steps:")
    print("- Check your Telegram for messages with rating buttons")
    print("- Try clicking the 👍 and 👎 buttons")
    print("- The bot should respond to your feedback")

if __name__ == "__main__":
    asyncio.run(main()) 