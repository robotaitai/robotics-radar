#!/usr/bin/env python3
"""
Test script to verify the complete system is working:
1. Database has articles
2. RSS fetcher can get top articles
3. Telegram bot can send messages
"""

from storage.database import DatabaseManager
from scraper.rss_fetcher import RSSFetcher
from notifier.telegram_bot import TelegramNotifier
import os
from dotenv import load_dotenv

def test_database():
    """Test database functionality."""
    print("🧪 Testing Database")
    print("=" * 40)
    
    db = DatabaseManager()
    tweets = db.get_top_tweets(limit=5)
    
    print(f"📊 Found {len(tweets)} articles in database")
    
    if tweets:
        print("📋 Sample articles:")
        for i, tweet in enumerate(tweets[:3], 1):
            print(f"  {i}. {tweet.text[:60]}...")
            print(f"     Score: {tweet.score:.1f} | URL: {tweet.url[:50]}...")
            print()
    
    return len(tweets) > 0

def test_rss_fetcher():
    """Test RSS fetcher functionality."""
    print("🧪 Testing RSS Fetcher")
    print("=" * 40)
    
    fetcher = RSSFetcher()
    result = fetcher.run_fetch_cycle()
    
    print(f"📡 RSS Fetch Result:")
    print(f"  - Total fetched: {result.get('total_fetched', 0)}")
    print(f"  - Stored: {result.get('stored_count', 0)}")
    print(f"  - Top tweets: {len(result.get('top_tweets', []))}")
    print(f"  - Error: {result.get('error', 'None')}")
    
    return result.get('error') is None

def test_telegram_bot():
    """Test Telegram bot functionality."""
    print("🧪 Testing Telegram Bot")
    print("=" * 40)
    
    # Load environment
    load_dotenv()
    
    notifier = TelegramNotifier()
    
    print(f"🤖 Bot Configuration:")
    print(f"  - Token: {'✅ Set' if notifier.bot_token else '❌ Not set'}")
    print(f"  - Allowed users: {notifier.allowed_users}")
    print(f"  - Available: {notifier.is_available()}")
    
    if not notifier.is_available():
        print("❌ Telegram bot not available")
        return False
    
    # Test with a small message
    db = DatabaseManager()
    tweets = db.get_top_tweets(limit=1)
    
    if not tweets:
        print("❌ No articles available for testing")
        return False
    
    print(f"📤 Sending test message with 1 article...")
    
    try:
        notifier.send_top_tweets_sync(tweets)
        print("✅ Telegram message sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Error sending Telegram message: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Complete Robotics Radar System")
    print("=" * 60)
    print()
    
    # Test each component
    db_ok = test_database()
    print()
    
    rss_ok = test_rss_fetcher()
    print()
    
    telegram_ok = test_telegram_bot()
    print()
    
    # Summary
    print("📊 Test Results Summary")
    print("=" * 40)
    print(f"Database: {'✅ OK' if db_ok else '❌ FAILED'}")
    print(f"RSS Fetcher: {'✅ OK' if rss_ok else '❌ FAILED'}")
    print(f"Telegram Bot: {'✅ OK' if telegram_ok else '❌ FAILED'}")
    
    if db_ok and rss_ok and telegram_ok:
        print("\n🎉 All systems are working correctly!")
        print("💡 You should receive Telegram messages every 10 seconds")
    else:
        print("\n⚠️  Some systems have issues that need to be fixed")

if __name__ == "__main__":
    main() 