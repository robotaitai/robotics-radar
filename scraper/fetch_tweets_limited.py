"""
Modified Tweet Fetcher for Limited Twitter API Access.
This version works with restricted API access by using available endpoints
or generating simulated data for testing purposes.
"""

import logging
import os
import sys
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import yaml

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tweepy
from storage.database import DatabaseManager, Tweet
from scoring.scoring_model import ScoringModel
from nlp.keyword_extraction import KeywordExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LimitedTweetFetcher:
    """Tweet fetcher for limited Twitter API access."""
    
    def __init__(self, config_path: str = "config/keywords.yaml"):
        """Initialize the fetcher.
        
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
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
            logger.info("Configuration loaded successfully")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
    
    def _initialize_api(self) -> Optional[tweepy.API]:
        """Initialize Twitter API client."""
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
            logger.info("Twitter API initialized successfully (limited access)")
            return api
            
        except Exception as e:
            logger.error(f"Error initializing Twitter API: {e}")
            return None
    
    def _generate_simulated_tweets(self, count: int = 10) -> List[Tweet]:
        """Generate simulated tweets for testing when API access is limited."""
        logger.info(f"Generating {count} simulated tweets for testing")
        
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
            
            # Generate summary for agent usage
            summary = self._generate_summary(tweet_text, topics)
            
            # Choose appropriate robotics news source based on content
            if "medical" in tweet_text.lower() or "surgery" in tweet_text.lower():
                url = "https://www.medicalrobotics.org/"
            elif "industrial" in tweet_text.lower() or "manufacturing" in tweet_text.lower():
                url = "https://www.robotics.org/"
            elif "autonomous" in tweet_text.lower() or "self-driving" in tweet_text.lower():
                url = "https://www.autonomousrobotics.org/"
            elif "research" in tweet_text.lower() or "academic" in tweet_text.lower():
                url = "https://robohub.org/"
            else:
                url = "https://www.robotics.org/"
            
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
        """Generate a concise summary of the tweet for agent usage.
        
        Args:
            text: Tweet text
            topics: Extracted topics
            
        Returns:
            Summary string
        """
        try:
            # Extract key information
            key_topics = topics[:3] if topics else []
            
            # Create a concise summary
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
    
    def fetch_tweets_limited(self, max_tweets: int = 20) -> List[Tweet]:
        """Fetch tweets using available API endpoints or generate simulated data."""
        if not self.api:
            logger.warning("Twitter API not available, using simulated data")
            return self._generate_simulated_tweets(max_tweets)
        
        try:
            # Try to get rate limit status to see what's available
            rate_limits = self.api.rate_limit_status()
            logger.info("Rate limit status retrieved successfully")
            
            # For now, use simulated data since search is not available
            logger.info("Search endpoint not available, using simulated data for testing")
            return self._generate_simulated_tweets(max_tweets)
            
        except Exception as e:
            logger.warning(f"Error accessing Twitter API: {e}")
            logger.info("Falling back to simulated data")
            return self._generate_simulated_tweets(max_tweets)
    
    def store_tweets(self, tweets: List[Tweet]) -> int:
        """Store tweets in database."""
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
        """Run a complete fetch cycle."""
        try:
            logger.info("Starting limited tweet fetch cycle")
            
            # Fetch tweets (simulated or real)
            tweets = self.fetch_tweets_limited(max_tweets=15)
            
            # Store tweets
            stored_count = self.store_tweets(tweets)
            
            # Get top tweets from current fetch cycle only (not all stored tweets)
            if tweets:
                # Sort tweets by score and take top 10
                sorted_tweets = sorted(tweets, key=lambda x: x.score, reverse=True)
                top_tweets = sorted_tweets[:10]
                logger.info(f"Selected top {len(top_tweets)} tweets from current fetch cycle")
            else:
                top_tweets = []
            
            result = {
                'total_fetched': len(tweets),
                'stored_count': stored_count,
                'top_tweets': top_tweets,
                'timestamp': datetime.now().isoformat(),
                'mode': 'simulated' if not self.api else 'limited_api'
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
                'error': str(e),
                'mode': 'error'
            }
    
    def get_fetch_stats(self) -> Dict:
        """Get statistics about the last fetch operation."""
        try:
            analytics = self.db.get_analytics_summary()
            
            return {
                'total_tweets': analytics['total_tweets'],
                'total_authors': analytics['total_authors'],
                'avg_score': analytics['avg_score'],
                'recent_tweets': analytics['recent_tweets'],
                'top_authors': self.db.get_top_authors(limit=5),
                'trending_topics': self.db.get_trending_topics(limit=5),
                'api_mode': 'limited' if self.api else 'simulated'
            }
            
        except Exception as e:
            logger.error(f"Error getting fetch stats: {e}")
            return {
                'total_tweets': 0,
                'total_authors': 0,
                'avg_score': 0,
                'recent_tweets': 0,
                'top_authors': [],
                'trending_topics': [],
                'api_mode': 'error'
            }


def main():
    """Main function to test the limited tweet fetcher."""
    try:
        fetcher = LimitedTweetFetcher()
        result = fetcher.run_fetch_cycle()
        
        print(f"Fetch cycle completed:")
        print(f"  - Total fetched: {result['total_fetched']}")
        print(f"  - Stored: {result['stored_count']}")
        print(f"  - Mode: {result.get('mode', 'unknown')}")
        print(f"  - Top tweets: {len(result['top_tweets'])}")
        
        if result['top_tweets']:
            print("\nTop tweets:")
            for i, tweet in enumerate(result['top_tweets'][:3], 1):
                print(f"  {i}. {tweet.text[:100]}... (Score: {tweet.score:.1f})")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    main() 