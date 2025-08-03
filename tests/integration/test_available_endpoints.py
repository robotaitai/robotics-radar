#!/usr/bin/env python3
"""
Test to check what Twitter API endpoints are available with current access level.
"""

import os
import sys
import tweepy
from dotenv import load_dotenv

def load_env_vars():
    """Load environment variables from .env file."""
    load_dotenv()

def test_available_endpoints():
    """Test what Twitter API endpoints are available."""
    print("🔍 Testing Available Twitter API Endpoints...")
    print("=" * 60)
    
    # Load environment variables
    load_env_vars()
    
    # Get credentials
    api_key = os.getenv('TWITTER_API_KEY')
    api_secret = os.getenv('TWITTER_API_SECRET')
    access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    
    if not all([api_key, api_secret, access_token, access_token_secret]):
        print("❌ Missing Twitter API credentials")
        return
    
    try:
        # Initialize API
        auth = tweepy.OAuthHandler(api_key, api_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth, wait_on_rate_limit=True)
        
        # Test authentication
        user = api.verify_credentials()
        print(f"✅ Authenticated as: @{user.screen_name}")
        print(f"   User ID: {user.id}")
        print(f"   Followers: {user.followers_count:,}")
        print()
        
        # Test different endpoints
        endpoints_to_test = [
            ("User Timeline", lambda: api.user_timeline(count=5)),
            ("Home Timeline", lambda: api.home_timeline(count=5)),
            ("Mentions", lambda: api.mentions_timeline(count=5)),
            ("User Info", lambda: api.get_user(screen_name=user.screen_name)),
            ("Followers", lambda: api.followers(count=5)),
            ("Friends", lambda: api.friends(count=5)),
            ("Search Tweets", lambda: api.search_tweets(q="robotics", count=5)),
            ("Trending Topics", lambda: api.trends_place(1)),
            ("Rate Limit Status", lambda: api.rate_limit_status()),
        ]
        
        available_endpoints = []
        unavailable_endpoints = []
        
        for endpoint_name, test_func in endpoints_to_test:
            try:
                print(f"Testing {endpoint_name}...", end=" ")
                result = test_func()
                print("✅ Available")
                available_endpoints.append(endpoint_name)
                
                # Show sample data for some endpoints
                if endpoint_name == "User Timeline" and result:
                    print(f"   Sample: {result[0].text[:50]}...")
                elif endpoint_name == "Home Timeline" and result:
                    print(f"   Sample: {result[0].text[:50]}...")
                    
            except Exception as e:
                print(f"❌ Not available: {str(e)[:50]}...")
                unavailable_endpoints.append(endpoint_name)
        
        print("\n" + "=" * 60)
        print("📊 Endpoint Availability Summary:")
        print("=" * 60)
        
        print("✅ Available Endpoints:")
        for endpoint in available_endpoints:
            print(f"   - {endpoint}")
        
        print("\n❌ Unavailable Endpoints:")
        for endpoint in unavailable_endpoints:
            print(f"   - {endpoint}")
        
        # Suggest alternative approaches
        print("\n💡 Suggested Alternative Approaches:")
        if "User Timeline" in available_endpoints:
            print("   - Use your own timeline to find robotics-related tweets")
        if "Home Timeline" in available_endpoints:
            print("   - Use your home timeline to find robotics-related tweets")
        if "Mentions" in available_endpoints:
            print("   - Monitor mentions for robotics-related discussions")
        if "Followers" in available_endpoints:
            print("   - Analyze your followers' tweets for robotics content")
        
        return available_endpoints, unavailable_endpoints
        
    except Exception as e:
        print(f"❌ Error testing endpoints: {e}")
        return [], []

if __name__ == "__main__":
    test_available_endpoints() 