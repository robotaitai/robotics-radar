"""
Tweet fetching module for Robotics Radar.
Fetches tweets from X (Twitter) API using tweepy.
"""

import tweepy
import logging
import yaml
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.database import DatabaseManager, Tweet
from scoring.scoring_model import ScoringModel
from nlp.keyword_extraction import KeywordExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TweetFetcher:
    """Fetches tweets from X API based on configured keywords."""
    
    def __init__(self, config_path: str = "config/keywords.yaml"):
        """Initialize tweet fetcher.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.api = self._initialize_api()
        self.db = DatabaseManager()
        self.scoring_model = ScoringModel(config_path)
        self.keyword_extractor = KeywordExtractor()
        
    def _load_config(self) -> Dict:
        """Load configuration from YAML file.
        
        Returns:
            Configuration dictionary
        """
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
            logger.info("Configuration loaded successfully")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
    
    def _initialize_api(self) -> Optional[tweepy.API]:
        """Initialize Twitter API client.
        
        Returns:
            tweepy API client or None if initialization fails
        """
        try:
            # Get API credentials from environment variables
            api_key = os.getenv('TWITTER_API_KEY')
            api_secret = os.getenv('TWITTER_API_SECRET')
            access_token = os.getenv('TWITTER_ACCESS_TOKEN')
            access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
            
            if not all([api_key, api_secret, access_token, access_token_secret]):
                logger.error("Missing Twitter API credentials in environment variables")
                return None
            
            # Authenticate with Twitter
            auth = tweepy.OAuthHandler(api_key, api_secret)
            auth.set_access_token(access_token, access_token_secret)
            
            # Create API object
            api = tweepy.API(auth, wait_on_rate_limit=True)
            
            # Test API connection
            api.verify_credentials()
            logger.info("Twitter API initialized successfully")
            return api
            
        except Exception as e:
            logger.error(f"Error initializing Twitter API: {e}")
            return None
    
    def fetch_tweets(self, max_tweets: int = 100) -> List[Tweet]:
        """Fetch tweets based on configured keywords.
        
        Args:
            max_tweets: Maximum number of tweets to fetch per keyword
            
        Returns:
            List of Tweet objects
        """
        if not self.api:
            logger.error("Twitter API not initialized")
            return []
        
        try:
            keywords = self.config.get('keywords', [])
            languages = self.config.get('languages', ['en'])
            exclude_keywords = self.config.get('exclude_keywords', [])
            
            all_tweets = []
            
            for keyword in keywords:
                logger.info(f"Fetching tweets for keyword: {keyword}")
                
                try:
                    # Search tweets
                    tweets = self.api.search_tweets(
                        q=keyword,
                        lang=','.join(languages),
                        count=min(max_tweets, 100),  # Twitter API limit
                        tweet_mode='extended',
                        result_type='mixed'  # Include both recent and popular tweets
                    )
                    
                    # Process tweets
                    for tweet in tweets:
                        processed_tweet = self._process_tweet(tweet, exclude_keywords)
                        if processed_tweet:
                            all_tweets.append(processed_tweet)
                    
                    # Rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error fetching tweets for keyword '{keyword}': {e}")
                    continue
            
            logger.info(f"Fetched {len(all_tweets)} tweets total")
            return all_tweets
            
        except Exception as e:
            logger.error(f"Error fetching tweets: {e}")
            return []
    
    def _process_tweet(self, tweet, exclude_keywords: List[str]) -> Optional[Tweet]:
        """Process a single tweet and convert to Tweet object.
        
        Args:
            tweet: tweepy Tweet object
            exclude_keywords: List of keywords to exclude
            
        Returns:
            Tweet object or None if tweet should be excluded
        """
        try:
            # Check if tweet should be excluded
            tweet_text = tweet.full_text.lower()
            for exclude_keyword in exclude_keywords:
                if exclude_keyword.lower() in tweet_text:
                    return None
            
            # Check if tweet is robotics-related
            if not self.keyword_extractor.is_robotics_related(tweet_text):
                return None
            
            # Extract topics and keywords
            topics = self.keyword_extractor.extract_topics(tweet_text)
            
            # Create Tweet object
            processed_tweet = Tweet(
                id=str(tweet.id),
                text=tweet.full_text,
                author_id=str(tweet.user.id),
                author_username=tweet.user.screen_name,
                author_name=tweet.user.name,
                author_followers=tweet.user.followers_count,
                likes=tweet.favorite_count,
                retweets=tweet.retweet_count,
                replies=getattr(tweet, 'reply_count', 0),
                url=f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}",
                created_at=tweet.created_at,
                topics=topics
            )
            
            # Calculate score
            tweet_data = {
                'id': processed_tweet.id,
                'text': processed_tweet.text,
                'likes': processed_tweet.likes,
                'retweets': processed_tweet.retweets,
                'replies': processed_tweet.replies,
                'author_followers': processed_tweet.author_followers
            }
            
            processed_tweet.score = self.scoring_model.calculate_final_score(tweet_data)
            
            # Update topic frequencies in database
            for topic in topics:
                self.db.update_topic_frequency(topic)
            
            return processed_tweet
            
        except Exception as e:
            logger.error(f"Error processing tweet {getattr(tweet, 'id', 'unknown')}: {e}")
            return None
    
    def fetch_recent_tweets(self, hours: int = 2) -> List[Tweet]:
        """Fetch tweets from the last N hours.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of Tweet objects
        """
        if not self.api:
            logger.error("Twitter API not initialized")
            return []
        
        try:
            keywords = self.config.get('keywords', [])
            languages = self.config.get('languages', ['en'])
            exclude_keywords = self.config.get('exclude_keywords', [])
            
            # Calculate time range
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            all_tweets = []
            
            for keyword in keywords:
                logger.info(f"Fetching recent tweets for keyword: {keyword}")
                
                try:
                    # Search tweets with time constraints
                    tweets = self.api.search_tweets(
                        q=f"{keyword} since:{start_time.strftime('%Y-%m-%d')}",
                        lang=','.join(languages),
                        count=100,
                        tweet_mode='extended',
                        result_type='recent'
                    )
                    
                    # Filter by time
                    recent_tweets = [
                        tweet for tweet in tweets 
                        if start_time <= tweet.created_at <= end_time
                    ]
                    
                    # Process tweets
                    for tweet in recent_tweets:
                        processed_tweet = self._process_tweet(tweet, exclude_keywords)
                        if processed_tweet:
                            all_tweets.append(processed_tweet)
                    
                    # Rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error fetching recent tweets for keyword '{keyword}': {e}")
                    continue
            
            logger.info(f"Fetched {len(all_tweets)} recent tweets")
            return all_tweets
            
        except Exception as e:
            logger.error(f"Error fetching recent tweets: {e}")
            return []
    
    def store_tweets(self, tweets: List[Tweet]) -> int:
        """Store tweets in database.
        
        Args:
            tweets: List of Tweet objects to store
            
        Returns:
            Number of tweets successfully stored
        """
        try:
            stored_count = 0
            
            for tweet in tweets:
                if self.db.insert_tweet(tweet):
                    stored_count += 1
            
            logger.info(f"Stored {stored_count} tweets in database")
            return stored_count
            
        except Exception as e:
            logger.error(f"Error storing tweets: {e}")
            return 0
    
    def run_fetch_cycle(self) -> Dict:
        """Run a complete fetch cycle.
        
        Returns:
            Dictionary with fetch results
        """
        try:
            logger.info("Starting tweet fetch cycle")
            
            # Fetch recent tweets
            tweets = self.fetch_recent_tweets(hours=2)
            
            # Store tweets
            stored_count = self.store_tweets(tweets)
            
            # Get top tweets for notifications
            top_tweets = self.db.get_top_tweets(limit=10)
            
            result = {
                'total_fetched': len(tweets),
                'stored_count': stored_count,
                'top_tweets': top_tweets,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Fetch cycle completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in fetch cycle: {e}")
            return {
                'total_fetched': 0,
                'stored_count': 0,
                'top_tweets': [],
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def get_fetch_stats(self) -> Dict:
        """Get statistics about the last fetch operation.
        
        Returns:
            Dictionary with fetch statistics
        """
        try:
            analytics = self.db.get_analytics_summary()
            
            return {
                'total_tweets': analytics['total_tweets'],
                'total_authors': analytics['total_authors'],
                'avg_score': analytics['avg_score'],
                'recent_tweets': analytics['recent_tweets'],
                'top_authors': self.db.get_top_authors(limit=5),
                'trending_topics': self.db.get_trending_topics(limit=5)
            }
            
        except Exception as e:
            logger.error(f"Error getting fetch stats: {e}")
            return {}


def main():
    """Main function for testing tweet fetching."""
    try:
        fetcher = TweetFetcher()
        result = fetcher.run_fetch_cycle()
        
        print("Fetch Results:")
        print(f"Total fetched: {result['total_fetched']}")
        print(f"Stored: {result['stored_count']}")
        print(f"Top tweets: {len(result['top_tweets'])}")
        
        if result['top_tweets']:
            print("\nTop tweets:")
            for i, tweet in enumerate(result['top_tweets'][:3], 1):
                print(f"{i}. {tweet.author_username}: {tweet.text[:100]}... (Score: {tweet.score:.2f})")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    main() 