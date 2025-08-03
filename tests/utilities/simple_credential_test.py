#!/usr/bin/env python3
"""
Simple credential test for Twitter and Telegram APIs.
This test only checks basic connectivity without complex dependencies.
"""

import os
import sys
import asyncio
import tweepy
from telegram import Bot

def load_env_vars():
    """Load environment variables from .env file."""
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

def test_twitter_credentials():
    """Test Twitter API credentials."""
    print("\n🔍 Testing Twitter API Credentials...")
    print("=" * 50)
    
    # Get credentials
    api_key = os.getenv('TWITTER_API_KEY')
    api_secret = os.getenv('TWITTER_API_SECRET')
    access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    
    # Check if credentials are set
    credentials = [api_key, api_secret, access_token, access_token_secret]
    if any(not cred or cred.startswith('your_') for cred in credentials):
        print("❌ Twitter API credentials not properly configured")
        print("   Please check your .env file")
        return False
    
    print("✅ Twitter API credentials found in .env file")
    
    try:
        # Test API connection
        auth = tweepy.OAuthHandler(api_key, api_secret)
        auth.set_access_token(access_token, access_token_secret)
        
        api = tweepy.API(auth, wait_on_rate_limit=True)
        
        # Test authentication
        user = api.verify_credentials()
        print(f"✅ Twitter API authentication successful!")
        print(f"   Authenticated as: @{user.screen_name}")
        print(f"   User ID: {user.id}")
        print(f"   Followers: {user.followers_count:,}")
        
        # Test search functionality (may not be available with limited API access)
        print("\n🔍 Testing Twitter Search...")
        try:
            search_results = api.search_tweets(
                q="robotics",
                lang="en",
                count=3,
                tweet_mode='extended'
            )
            
            print(f"✅ Twitter search successful!")
            print(f"   Found {len(search_results)} tweets")
            
            if search_results:
                sample_tweet = search_results[0]
                print(f"   Sample tweet: {sample_tweet.full_text[:100]}...")
                print(f"   Author: @{sample_tweet.user.screen_name}")
                print(f"   Likes: {sample_tweet.favorite_count}, Retweets: {sample_tweet.retweet_count}")
        except Exception as search_error:
            print(f"⚠️  Twitter search not available: {search_error}")
            print("   This is normal with limited API access")
            print("   The Robotics Radar system will work with available endpoints")
        
        return True
        
    except tweepy.errors.Forbidden as e:
        print(f"❌ Twitter API access denied: {e}")
        print("   You may need to upgrade your Twitter API access level")
        return False
    except tweepy.errors.Unauthorized as e:
        print(f"❌ Twitter API unauthorized: {e}")
        print("   Please check your API credentials")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

async def test_telegram_credentials():
    """Test Telegram bot credentials."""
    print("\n🔍 Testing Telegram Bot Credentials...")
    print("=" * 50)
    
    # Get credentials
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    allowed_users = os.getenv('TELEGRAM_ALLOWED_USERS', '')
    
    # Check if bot token is set
    if not bot_token or bot_token.startswith('your_'):
        print("❌ Telegram bot token not properly configured")
        print("   Please check your .env file")
        return False
    
    print("✅ Telegram bot token found in .env file")
    
    # Check allowed users
    if allowed_users:
        users = [u.strip() for u in allowed_users.split(',')]
        print(f"✅ Allowed users configured: {len(users)} users")
        for i, user in enumerate(users, 1):
            print(f"   {i}. User ID: {user}")
    else:
        print("ℹ️  No allowed users configured (all users allowed)")
    
    try:
        # Test bot connection
        bot = Bot(token=bot_token)
        
        # Get bot info
        bot_info = await bot.get_me()
        print(f"✅ Telegram bot connection successful!")
        print(f"   Bot username: @{bot_info.username}")
        print(f"   Bot name: {bot_info.first_name}")
        print(f"   Bot ID: {bot_info.id}")
        print(f"   Can join groups: {bot_info.can_join_groups}")
        print(f"   Can read all group messages: {bot_info.can_read_all_group_messages}")
        
        return True
        
    except Exception as e:
        print(f"❌ Telegram bot error: {e}")
        return False

async def main():
    """Main test function."""
    print("🤖 Robotics Radar - Simple Credential Test")
    print("=" * 60)
    
    # Load environment variables
    print("📋 Loading environment variables...")
    load_env_vars()
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("Please create a .env file with your credentials:")
        print("cp env.example .env")
        print("Then edit .env with your actual API keys")
        return False
    
    print("✅ Environment variables loaded")
    
    # Run tests
    twitter_success = test_twitter_credentials()
    telegram_success = await test_telegram_credentials()
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Test Summary")
    print(f"{'='*60}")
    
    if twitter_success:
        print("✅ Twitter API: Working correctly")
    else:
        print("❌ Twitter API: Issues detected")
    
    if telegram_success:
        print("✅ Telegram Bot: Working correctly")
    else:
        print("❌ Telegram Bot: Issues detected")
    
    if twitter_success and telegram_success:
        print("\n🎉 All credentials are working correctly!")
        print("You're ready to run the Robotics Radar system!")
        return True
    else:
        print("\n⚠️  Some issues detected. Please check your credentials.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 