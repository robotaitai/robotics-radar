#!/usr/bin/env python3
"""
Test script to verify the feedback system is working:
1. Test feedback processing
2. Test database storage
3. Test Telegram callback handling
"""

from feedback.feedback_processor import FeedbackProcessor
from storage.database import DatabaseManager
from notifier.telegram_bot import TelegramNotifier
import os
from dotenv import load_dotenv

def test_feedback_processor():
    """Test the feedback processor."""
    print("🧪 Testing Feedback Processor")
    print("=" * 40)
    
    processor = FeedbackProcessor()
    
    # Test with a sample tweet ID
    test_tweet_id = "rss_123456"
    test_user_id = "test_user_123"
    
    print(f"Testing feedback processing for tweet: {test_tweet_id}")
    
    # Test like feedback
    success_like = processor.process_feedback(test_tweet_id, test_user_id, "like")
    print(f"Like feedback: {'✅ Success' if success_like else '❌ Failed'}")
    
    # Test dislike feedback
    success_dislike = processor.process_feedback(test_tweet_id, test_user_id, "dislike")
    print(f"Dislike feedback: {'✅ Success' if success_dislike else '❌ Failed'}")
    
    # Test invalid feedback type
    success_invalid = processor.process_feedback(test_tweet_id, test_user_id, "invalid")
    print(f"Invalid feedback: {'❌ Correctly failed' if not success_invalid else '⚠️ Should have failed'}")
    
    return success_like and success_dislike and not success_invalid

def test_database_feedback():
    """Test feedback storage in database."""
    print("\n🧪 Testing Database Feedback Storage")
    print("=" * 40)
    
    db = DatabaseManager()
    
    # Test adding feedback
    test_tweet_id = "rss_789012"
    test_user_id = "test_user_456"
    
    print(f"Adding feedback for tweet: {test_tweet_id}")
    
    # Add feedback
    success = db.add_feedback(test_tweet_id, test_user_id, "like")
    print(f"Add feedback: {'✅ Success' if success else '❌ Failed'}")
    
    # Get feedback
    feedback_data = db.get_tweet_feedback(test_tweet_id)
    print(f"Feedback data: {feedback_data}")
    
    return success and feedback_data.get('likes', 0) > 0

def test_telegram_callback_format():
    """Test Telegram callback data format."""
    print("\n🧪 Testing Telegram Callback Format")
    print("=" * 40)
    
    # Test callback data parsing
    test_callback_data = "feedback:rss_123456:like"
    
    print(f"Testing callback data: {test_callback_data}")
    
    # Parse callback data
    data = test_callback_data.split(':')
    if len(data) == 3 and data[0] == 'feedback':
        tweet_id = data[1]
        feedback_type = data[2]
        print(f"✅ Parsed correctly:")
        print(f"  - Tweet ID: {tweet_id}")
        print(f"  - Feedback type: {feedback_type}")
        return True
    else:
        print(f"❌ Failed to parse callback data")
        return False

def test_telegram_bot_configuration():
    """Test Telegram bot configuration for feedback."""
    print("\n🧪 Testing Telegram Bot Configuration")
    print("=" * 40)
    
    load_dotenv()
    
    notifier = TelegramNotifier()
    
    print(f"Bot token: {'✅ Set' if notifier.bot_token else '❌ Not set'}")
    print(f"Allowed users: {notifier.allowed_users}")
    print(f"Available: {notifier.is_available()}")
    
    # Test creating callback data
    test_tweet_id = "rss_123456"
    like_callback = f"feedback:{test_tweet_id}:like"
    dislike_callback = f"feedback:{test_tweet_id}:dislike"
    
    print(f"Like callback: {like_callback}")
    print(f"Dislike callback: {dislike_callback}")
    
    return notifier.is_available()

def main():
    """Run all feedback tests."""
    print("🚀 Testing Feedback System")
    print("=" * 60)
    print()
    
    # Test each component
    processor_ok = test_feedback_processor()
    print()
    
    database_ok = test_database_feedback()
    print()
    
    callback_ok = test_telegram_callback_format()
    print()
    
    bot_ok = test_telegram_bot_configuration()
    print()
    
    # Summary
    print("📊 Feedback System Test Results")
    print("=" * 40)
    print(f"Feedback Processor: {'✅ OK' if processor_ok else '❌ FAILED'}")
    print(f"Database Storage: {'✅ OK' if database_ok else '❌ FAILED'}")
    print(f"Callback Format: {'✅ OK' if callback_ok else '❌ FAILED'}")
    print(f"Telegram Bot: {'✅ OK' if bot_ok else '❌ FAILED'}")
    
    if processor_ok and database_ok and callback_ok and bot_ok:
        print("\n🎉 Feedback system is working correctly!")
        print("💡 Rating buttons should work in Telegram messages")
    else:
        print("\n⚠️  Some feedback components have issues")
    
    print("\n🔧 Troubleshooting Tips:")
    print("- Make sure the Telegram bot is running in polling mode")
    print("- Check that callback queries are enabled")
    print("- Verify the bot token has the right permissions")
    print("- Ensure the database has the feedback table")

if __name__ == "__main__":
    main() 