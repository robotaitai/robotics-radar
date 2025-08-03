#!/usr/bin/env python3
"""
Test script to check what Twitter API permissions and endpoints are available.
"""

import os
import sys
import tweepy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_twitter_permissions():
    """Test what Twitter API permissions are available."""
    print("🔍 Testing Twitter API Permissions")
    print("=" * 50)
    
    # Get credentials
    api_key = os.getenv('TWITTER_API_KEY')
    api_secret = os.getenv('TWITTER_API_SECRET')
    access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    
    print(f"API Key: {api_key[:10]}...{api_key[-10:] if api_key else 'None'}")
    print(f"API Secret: {api_secret[:10]}...{api_secret[-10:] if api_secret else 'None'}")
    print(f"Access Token: {access_token[:10]}...{access_token[-10:] if access_token else 'None'}")
    print(f"Access Token Secret: {access_token_secret[:10]}...{access_token_secret[-10:] if access_token_secret else 'None'}")
    print()
    
    if not all([api_key, api_secret, access_token, access_token_secret]):
        print("❌ Missing Twitter API credentials")
        return
    
    try:
        # Authenticate
        auth = tweepy.OAuthHandler(api_key, api_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth, wait_on_rate_limit=True)
        
        print("🔐 Testing Authentication...")
        
        # Test 1: Verify credentials
        try:
            user = api.verify_credentials()
            print(f"✅ Authentication successful!")
            print(f"   Authenticated as: @{user.screen_name}")
            print(f"   User ID: {user.id}")
            print(f"   Followers: {user.followers_count}")
            print(f"   Following: {user.friends_count}")
            print(f"   Account created: {user.created_at}")
            print()
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return
        
        # Test 2: Get user timeline
        print("📱 Testing User Timeline...")
        try:
            tweets = api.user_timeline(count=5)
            print(f"✅ User timeline accessible: {len(tweets)} tweets retrieved")
            for i, tweet in enumerate(tweets[:3], 1):
                print(f"   {i}. {tweet.text[:50]}... (ID: {tweet.id})")
            print()
        except Exception as e:
            print(f"❌ User timeline failed: {e}")
        
        # Test 3: Get user info
        print("👤 Testing User Info...")
        try:
            user_info = api.get_user(screen_name=user.screen_name)
            print(f"✅ User info accessible")
            print(f"   Name: {user_info.name}")
            print(f"   Location: {user_info.location or 'Not set'}")
            print(f"   Description: {user_info.description[:50]}...")
            print()
        except Exception as e:
            print(f"❌ User info failed: {e}")
        
        # Test 4: Search tweets
        print("🔍 Testing Search Tweets...")
        try:
            search_results = api.search_tweets(q="robotics", count=5)
            print(f"✅ Search tweets accessible: {len(search_results)} results")
            for i, tweet in enumerate(search_results[:3], 1):
                print(f"   {i}. @{tweet.user.screen_name}: {tweet.text[:50]}...")
            print()
        except Exception as e:
            print(f"❌ Search tweets failed: {e}")
        
        # Test 5: Get trending topics
        print("📈 Testing Trending Topics...")
        try:
            trends = api.get_place_trends(id=1)  # Worldwide trends
            print(f"✅ Trending topics accessible: {len(trends[0]['trends'])} trends")
            for i, trend in enumerate(trends[0]['trends'][:5], 1):
                print(f"   {i}. {trend['name']} ({trend['tweet_volume']} tweets)")
            print()
        except Exception as e:
            print(f"❌ Trending topics failed: {e}")
        
        # Test 6: Get followers
        print("👥 Testing Followers...")
        try:
            followers = api.get_followers(count=5)
            print(f"✅ Followers accessible: {len(followers)} followers retrieved")
            for i, follower in enumerate(followers[:3], 1):
                print(f"   {i}. @{follower.screen_name} ({follower.followers_count} followers)")
            print()
        except Exception as e:
            print(f"❌ Followers failed: {e}")
        
        # Test 7: Get friends (following)
        print("👥 Testing Friends (Following)...")
        try:
            friends = api.get_friends(count=5)
            print(f"✅ Friends accessible: {len(friends)} friends retrieved")
            for i, friend in enumerate(friends[:3], 1):
                print(f"   {1}. @{friend.screen_name} ({friend.followers_count} followers)")
            print()
        except Exception as e:
            print(f"❌ Friends failed: {e}")
        
        # Test 8: Rate limit status
        print("⏱️ Testing Rate Limits...")
        try:
            rate_limit_status = api.rate_limit_status()
            print(f"✅ Rate limit status accessible")
            search_limits = rate_limit_status['resources']['search']['/search/tweets']
            print(f"   Search tweets remaining: {search_limits['remaining']}/{search_limits['limit']}")
            print(f"   Reset time: {search_limits['reset']}")
            print()
        except Exception as e:
            print(f"❌ Rate limit status failed: {e}")
        
        # Test 9: Get specific user timeline
        print("📱 Testing Other User Timeline...")
        try:
            # Try to get a well-known robotics account
            other_user_tweets = api.user_timeline(screen_name="MIT_CSAIL", count=3)
            print(f"✅ Other user timeline accessible: {len(other_user_tweets)} tweets")
            for i, tweet in enumerate(other_user_tweets, 1):
                print(f"   {i}. {tweet.text[:50]}... (ID: {tweet.id})")
            print()
        except Exception as e:
            print(f"❌ Other user timeline failed: {e}")
        
        # Test 10: Get user by ID
        print("🆔 Testing Get User by ID...")
        try:
            user_by_id = api.get_user(user_id=user.id)
            print(f"✅ Get user by ID accessible: @{user_by_id.screen_name}")
            print()
        except Exception as e:
            print(f"❌ Get user by ID failed: {e}")
        
        print("🎉 Twitter API Permission Test Complete!")
        print("\n📋 Summary:")
        print("✅ = Available")
        print("❌ = Not available")
        
    except Exception as e:
        print(f"❌ General error: {e}")

if __name__ == "__main__":
    test_twitter_permissions() 