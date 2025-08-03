"""
Test Twitter API connectivity and functionality.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import tweepy

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.fetch_tweets import TweetFetcher


class TestTwitterAPI(unittest.TestCase):
    """Test Twitter API connectivity and functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Load environment variables
        self.api_key = os.getenv('TWITTER_API_KEY')
        self.api_secret = os.getenv('TWITTER_API_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        
    def test_environment_variables_set(self):
        """Test that all required Twitter API environment variables are set."""
        print("\n🔍 Testing Twitter API Environment Variables...")
        
        required_vars = [
            'TWITTER_API_KEY',
            'TWITTER_API_SECRET', 
            'TWITTER_ACCESS_TOKEN',
            'TWITTER_ACCESS_TOKEN_SECRET'
        ]
        
        missing_vars = []
        for var in required_vars:
            value = os.getenv(var)
            if not value or value.startswith('your_'):
                missing_vars.append(var)
            else:
                print(f"✅ {var}: {'*' * (len(value) - 4) + value[-4:] if len(value) > 4 else '*' * len(value)}")
        
        if missing_vars:
            print(f"❌ Missing or invalid environment variables: {missing_vars}")
            self.fail(f"Missing or invalid environment variables: {missing_vars}")
        else:
            print("✅ All Twitter API environment variables are properly set!")
    
    def test_twitter_api_connection(self):
        """Test actual Twitter API connection and authentication."""
        print("\n🔍 Testing Twitter API Connection...")
        
        try:
            # Initialize Twitter API
            auth = tweepy.OAuthHandler(self.api_key, self.api_secret)
            auth.set_access_token(self.access_token, self.access_token_secret)
            
            api = tweepy.API(auth, wait_on_rate_limit=True)
            
            # Test API connection by getting user info
            user = api.verify_credentials()
            
            print(f"✅ Twitter API connection successful!")
            print(f"   Authenticated as: @{user.screen_name}")
            print(f"   User ID: {user.id}")
            print(f"   Followers: {user.followers_count:,}")
            
            # Test search functionality
            print("\n🔍 Testing Twitter Search...")
            search_results = api.search_tweets(
                q="robotics",
                lang="en",
                count=5,
                tweet_mode='extended'
            )
            
            print(f"✅ Search test successful!")
            print(f"   Found {len(search_results)} tweets")
            
            if search_results:
                print(f"   Sample tweet: {search_results[0].full_text[:100]}...")
            
            self.assertTrue(True, "Twitter API connection and search working correctly")
            
        except Exception as e:
            print(f"❌ Twitter API error: {e}")
            self.fail(f"Twitter API connection failed: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            self.fail(f"Unexpected error: {e}")
    
    def test_tweet_fetcher_initialization(self):
        """Test TweetFetcher initialization with real credentials."""
        print("\n🔍 Testing TweetFetcher Initialization...")
        
        try:
            fetcher = TweetFetcher()
            
            # Check if API was initialized
            if fetcher.api:
                print("✅ TweetFetcher initialized successfully!")
                print(f"   API object: {type(fetcher.api).__name__}")
                print(f"   Configuration loaded: {len(fetcher.config.get('keywords', []))} keywords")
            else:
                print("❌ TweetFetcher API not initialized")
                self.fail("TweetFetcher API not initialized")
                
        except Exception as e:
            print(f"❌ TweetFetcher initialization failed: {e}")
            self.fail(f"TweetFetcher initialization failed: {e}")
    
    def test_configuration_loading(self):
        """Test that configuration is properly loaded."""
        print("\n🔍 Testing Configuration Loading...")
        
        try:
            fetcher = TweetFetcher()
            config = fetcher.config
            
            # Check required configuration sections
            required_sections = ['keywords', 'languages', 'exclude_keywords']
            for section in required_sections:
                if section in config:
                    print(f"✅ {section}: {len(config[section])} items")
                else:
                    print(f"❌ Missing configuration section: {section}")
                    self.fail(f"Missing configuration section: {section}")
            
            print("✅ Configuration loaded successfully!")
            
        except Exception as e:
            print(f"❌ Configuration loading failed: {e}")
            self.fail(f"Configuration loading failed: {e}")


def run_twitter_tests():
    """Run all Twitter API tests."""
    print("🤖 Twitter API Tests")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTwitterAPI)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("🎉 All Twitter API tests passed!")
        return True
    else:
        print("❌ Some Twitter API tests failed!")
        return False


if __name__ == "__main__":
    run_twitter_tests() 