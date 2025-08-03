"""
Hybrid tweet fetching module for Robotics Radar.
Tries real Twitter API first, falls back to simulated data if access is limited.
"""

import tweepy
import logging
import yaml
import os
import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.database import DatabaseManager, Tweet
from scoring.scoring_model import ScoringModel
from nlp.keyword_extraction import KeywordExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HybridTweetFetcher:
    """Hybrid tweet fetcher that tries real API first, falls back to simulated data."""
    
    def __init__(self, config_path: str = "config/keywords.yaml"):
        """Initialize hybrid tweet fetcher.
        
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
    
    def fetch_tweets_hybrid(self, max_tweets: int = 20) -> List[Tweet]:
        """Try to fetch real tweets first, fall back to simulated data.
        
        Args:
            max_tweets: Maximum number of tweets to fetch
            
        Returns:
            List of Tweet objects
        """
        # Try real API first
        if self.api:
            try:
                logger.info("Attempting to fetch real tweets from Twitter API...")
                real_tweets = self._fetch_real_tweets(max_tweets)
                if real_tweets:
                    logger.info(f"Successfully fetched {len(real_tweets)} real tweets")
                    return real_tweets
                else:
                    logger.info("No real tweets found, falling back to simulated data")
            except Exception as e:
                logger.warning(f"Real API failed: {e}, falling back to simulated data")
        
        # Fall back to simulated data
        logger.info("Using simulated data due to API limitations")
        return self._generate_simulated_tweets(max_tweets)
    
    def _fetch_real_tweets(self, max_tweets: int) -> List[Tweet]:
        """Fetch real tweets from Twitter API.
        
        Args:
            max_tweets: Maximum number of tweets to fetch
            
        Returns:
            List of Tweet objects
        """
        if not self.api:
            return []
        
        try:
            keywords = self.config.get('keywords', [])
            languages = self.config.get('languages', ['en'])
            exclude_keywords = self.config.get('exclude_keywords', [])
            
            all_tweets = []
            
            for keyword in keywords[:3]:  # Limit to first 3 keywords to avoid rate limits
                logger.info(f"Fetching tweets for keyword: {keyword}")
                
                try:
                    # Search tweets
                    tweets = self.api.search_tweets(
                        q=keyword,
                        lang=','.join(languages),
                        count=min(50, max_tweets // len(keywords)),
                        tweet_mode='extended',
                        result_type='recent'
                    )
                    
                    # Process tweets
                    for tweet in tweets:
                        processed_tweet = self._process_real_tweet(tweet, exclude_keywords)
                        if processed_tweet:
                            all_tweets.append(processed_tweet)
                            
                except tweepy.TweepError as e:
                    logger.error(f"Error fetching tweets for keyword '{keyword}': {e}")
                    continue
                    
            return all_tweets[:max_tweets]
            
        except Exception as e:
            logger.error(f"Error in real tweet fetch: {e}")
            return []
    
    def _process_real_tweet(self, tweet, exclude_keywords: List[str]) -> Optional[Tweet]:
        """Process a real tweet from Twitter API.
        
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
            summary = self._generate_summary(tweet_text, topics)
            
            # Create Tweet object with real URL
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
                url=f"https://x.com/{tweet.user.screen_name}/status/{tweet.id}",
                created_at=tweet.created_at,
                topics=topics,
                summary=summary
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
            
            return processed_tweet
            
        except Exception as e:
            logger.error(f"Error processing real tweet {getattr(tweet, 'id', 'unknown')}: {e}")
            return None
    
    def _generate_simulated_tweets(self, count: int = 10) -> List[Tweet]:
        """Generate simulated tweets with real robotics news URLs.
        
        Args:
            count: Number of tweets to generate
            
        Returns:
            List of Tweet objects
        """
        logger.info(f"Generating {count} simulated tweets with real URLs")
        
        # Sample robotics-related content
        sample_tweets = [
            "Exciting breakthrough in autonomous robotics! Researchers at MIT developed a new algorithm for dynamic obstacle avoidance. #robotics #AI #autonomous",
            "Just published our latest paper on soft robotics applications in medical devices. The potential for minimally invasive surgery is incredible! #softrobotics #medical",
            "Open source robotics project update: ROS2 integration with computer vision is now complete. Check out the GitHub repo! #opensource #ROS #computervision",
            "Industrial robotics market expected to grow 15% this year. Collaborative robots are leading the trend. #industrial #cobots #manufacturing",
            "New humanoid robot prototype can now perform complex household tasks. The future of service robots is here! #humanoid #servicerobots #AI",
            "Swarm robotics research shows promising results for search and rescue operations. Coordinated behavior is key! #swarmrobotics #searchandrescue",
            "Computer vision breakthrough: Real-time object recognition in robotics applications. Processing speed improved by 40%! #computervision #realtime",
            "Bio-inspired robotics: New design mimics octopus tentacles for underwater exploration. Nature is the best engineer! #bioinspired #underwater #robotics",
            "Drone technology advances: Autonomous delivery systems now operational in test cities. The sky's the limit! #drones #autonomous #delivery",
            "Robotic learning: AI agents can now learn complex tasks through observation. Transfer learning is the future! #roboticlearning #AI #transferlearning",
            "Self-driving cars: Latest safety improvements reduce accident rates by 60%. Autonomous vehicles are getting safer! #selfdriving #autonomous #safety",
            "Robotic surgery: New minimally invasive techniques reduce recovery time by 50%. Precision is everything! #roboticsurgery #medical #precision",
            "Mobile robotics: Autonomous navigation in unstructured environments. Robots can now go anywhere! #mobilerobotics #navigation #autonomous",
            "Collaborative robots: Human-robot interaction safety standards updated. Working together safely! #cobots #safety #collaboration",
            "Robotic arm precision: New control algorithms achieve sub-millimeter accuracy. Perfect for delicate operations! #roboticarm #precision #control"
        ]
        
        # Real robotics news sources with actual URLs
        real_robotics_sources = [
            {
                "name": "MIT Technology Review",
                "url": "https://www.technologyreview.com/topic/robotics/",
                "topics": ["research", "academic", "breakthrough"]
            },
            {
                "name": "IEEE Spectrum Robotics",
                "url": "https://spectrum.ieee.org/robotics",
                "topics": ["industrial", "technical", "engineering"]
            },
            {
                "name": "Robohub",
                "url": "https://robohub.org/",
                "topics": ["research", "academic", "general"]
            },
            {
                "name": "Robotics.org",
                "url": "https://www.robotics.org/",
                "topics": ["industrial", "manufacturing", "commercial"]
            },
            {
                "name": "Automation World",
                "url": "https://www.automationworld.com/robotics",
                "topics": ["industrial", "automation", "manufacturing"]
            },
            {
                "name": "Medical Robotics News",
                "url": "https://www.medicalrobotics.org/",
                "topics": ["medical", "healthcare", "surgery"]
            },
            {
                "name": "Autonomous Robotics News",
                "url": "https://www.autonomousrobotics.org/",
                "topics": ["autonomous", "self-driving", "navigation"]
            }
        ]
        
        # Sample usernames
        usernames = [
            "robotics_researcher", "ai_engineer", "tech_innovator", "robot_dev", 
            "autonomous_systems", "soft_robotics_lab", "industrial_robotics", 
            "computer_vision_ai", "bio_robotics", "swarm_robotics", "drone_tech",
            "self_driving_ai", "medical_robotics", "mobile_robotics", "cobot_expert"
        ]
        
        simulated_tweets = []
        
        for i in range(count):
            # Select random content
            tweet_text = random.choice(sample_tweets)
            username = random.choice(usernames)
            
            # Generate random engagement metrics
            likes = random.randint(10, 500)
            retweets = random.randint(5, 100)
            replies = random.randint(2, 50)
            followers = random.randint(1000, 50000)
            
            # Generate random timestamp within last 24 hours
            timestamp = datetime.now() - timedelta(
                hours=random.randint(0, 24),
                minutes=random.randint(0, 60)
            )
            
            # Extract topics
            topics = self.keyword_extractor.extract_topics(tweet_text)
            
            # Generate summary
            summary = self._generate_summary(tweet_text, topics)
            
            # Choose appropriate real robotics news source based on content
            best_source = None
            best_match_score = 0
            
            for source in real_robotics_sources:
                match_score = 0
                for topic in source["topics"]:
                    if topic.lower() in tweet_text.lower():
                        match_score += 1
                if match_score > best_match_score:
                    best_match_score = match_score
                    best_source = source
            
            # Use best matching source or default to Robohub
            url = best_source["url"] if best_source else "https://robohub.org/"
            
            # Create Tweet object
            tweet = Tweet(
                id=f"sim_{i}_{int(time.time())}",
                text=tweet_text,
                author_id=f"sim_user_{i}",
                author_username=username,
                author_name=f"{username.title()}",
                author_followers=followers,
                likes=likes,
                retweets=retweets,
                replies=replies,
                url=url,
                created_at=timestamp,
                topics=topics,
                summary=summary
            )
            
            # Calculate score
            tweet_data = {
                'id': tweet.id,
                'text': tweet.text,
                'likes': tweet.likes,
                'retweets': tweet.retweets,
                'replies': tweet.replies,
                'author_followers': tweet.author_followers
            }
            
            tweet.score = self.scoring_model.calculate_final_score(tweet_data)
            
            simulated_tweets.append(tweet)
        
        return simulated_tweets
    
    def _generate_summary(self, text: str, topics: List[str]) -> str:
        """Generate a concise summary of the tweet for agent usage."""
        try:
            key_topics = topics[:3] if topics else []
            if "breakthrough" in text.lower() or "new" in text.lower():
                summary = f"New breakthrough in {', '.join(key_topics)}: {text[:100]}..."
            elif "research" in text.lower() or "study" in text.lower():
                summary = f"Research update on {', '.join(key_topics)}: {text[:100]}..."
            elif "announcement" in text.lower() or "launch" in text.lower():
                summary = f"Announcement in {', '.join(key_topics)}: {text[:100]}..."
            else:
                summary = f"Update on {', '.join(key_topics)}: {text[:100]}..."
            return summary
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"Robotics update: {text[:80]}..."
    
    def store_tweets(self, tweets: List[Tweet]) -> int:
        """Store tweets in database.
        
        Args:
            tweets: List of tweets to store
            
        Returns:
            Number of tweets stored
        """
        stored_count = 0
        for tweet in tweets:
            try:
                self.db.insert_tweet(tweet)
                stored_count += 1
            except Exception as e:
                logger.error(f"Error storing tweet {tweet.id}: {e}")
        
        logger.info(f"Stored {stored_count} tweets in database")
        return stored_count
    
    def run_fetch_cycle(self) -> Dict:
        """Run a complete fetch cycle.
        
        Returns:
            Dictionary with fetch results
        """
        try:
            logger.info("Starting hybrid tweet fetch cycle")
            
            # Fetch tweets (real or simulated)
            tweets = self.fetch_tweets_hybrid(max_tweets=20)
            
            if not tweets:
                logger.warning("No tweets fetched in this cycle")
                return {
                    'total_fetched': 0,
                    'stored_count': 0,
                    'top_tweets': [],
                    'error': 'No tweets available',
                    'timestamp': datetime.now().isoformat(),
                    'mode': 'hybrid'
                }
            
            # Store tweets
            stored_count = self.store_tweets(tweets)
            
            # Get top tweets from current fetch cycle only
            if tweets:
                # Sort tweets by score and take top 10
                sorted_tweets = sorted(tweets, key=lambda x: x.score, reverse=True)
                top_tweets = sorted_tweets[:10]
                logger.info(f"Selected top {len(top_tweets)} tweets from current fetch cycle")
            else:
                top_tweets = []
            
            return {
                'total_fetched': len(tweets),
                'stored_count': stored_count,
                'top_tweets': top_tweets,
                'timestamp': datetime.now().isoformat(),
                'mode': 'hybrid'
            }
            
        except Exception as e:
            logger.error(f"Error in fetch cycle: {e}")
            return {
                'total_fetched': 0,
                'stored_count': 0,
                'top_tweets': [],
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'mode': 'hybrid'
            }
    
    def get_fetch_stats(self) -> Dict:
        """Get fetch statistics.
        
        Returns:
            Dictionary with fetch statistics
        """
        try:
            total_tweets = self.db.get_total_tweets()
            recent_tweets = self.db.get_recent_tweets(hours=24)
            
            return {
                'total_tweets': total_tweets,
                'recent_tweets_24h': len(recent_tweets),
                'api_available': self.api is not None,
                'last_fetch': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting fetch stats: {e}")
            return {}


def main():
    """Main function to test the hybrid fetcher."""
    try:
        fetcher = HybridTweetFetcher()
        
        # Run a test fetch cycle
        result = fetcher.run_fetch_cycle()
        
        print(f"Fetch cycle completed: {result}")
        
        if result['top_tweets']:
            print(f"\nTop {len(result['top_tweets'])} tweets:")
            for i, tweet in enumerate(result['top_tweets'][:3], 1):
                print(f"{i}. @{tweet.author_username}: {tweet.text[:100]}...")
                print(f"   URL: {tweet.url}")
                print(f"   Score: {tweet.score:.2f}")
                print()
        
    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    main() 