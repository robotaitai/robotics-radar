#!/usr/bin/env python3
"""
Reddit scraper for Robotics Radar.
Fetches content from robotics-related subreddits using Reddit's JSON endpoints.
"""

import requests
import logging
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sys
import os
from urllib.parse import urljoin

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.database import DatabaseManager, Article

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedditScraper:
    """Scrapes robotics content from Reddit subreddits."""
    
    def __init__(self):
        """Initialize Reddit scraper."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RoboticsRadar/1.0 (Educational Research Tool)',
            'Accept': 'application/json'
        })
        self.db = DatabaseManager()
        
        # Reddit subreddits to monitor
        self.subreddits = [
            'robotics',
            'ROS',
            'AutonomousVehicles',
            'drones',
            'MachineLearning',  # Often has robotics content
            'artificial',
            'robots',
            'automation'
        ]
        
        # Reddit API endpoints
        self.base_url = "https://www.reddit.com"
        self.endpoints = {
            'new': '/r/{}/new.json',
            'hot': '/r/{}/hot.json',
            'top': '/r/{}/top.json'
        }
        
        # Rate limiting
        self.request_delay = 2  # seconds between requests
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Implement rate limiting to respect Reddit's API."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def fetch_subreddit_posts(self, subreddit: str, sort: str = 'new', limit: int = 25) -> List[Dict]:
        """Fetch posts from a specific subreddit.
        
        Args:
            subreddit: Subreddit name
            sort: Sort method ('new', 'hot', 'top')
            limit: Number of posts to fetch
            
        Returns:
            List of post dictionaries
        """
        try:
            self._rate_limit()
            
            endpoint = self.endpoints.get(sort, self.endpoints['new'])
            url = urljoin(self.base_url, endpoint.format(subreddit))
            
            params = {
                'limit': limit,
                't': 'day' if sort == 'top' else None  # Time filter for top posts
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            posts = []
            
            if 'data' in data and 'children' in data['data']:
                for child in data['data']['children']:
                    post_data = child['data']
                    
                    # Filter for robotics-related content
                    if self._is_robotics_related(post_data):
                        posts.append({
                            'id': f"reddit_{post_data['id']}",
                            'title': post_data.get('title', ''),
                            'author': post_data.get('author', '[deleted]'),
                            'score': post_data.get('score', 0),
                            'num_comments': post_data.get('num_comments', 0),
                            'url': post_data.get('url', ''),
                            'permalink': f"https://reddit.com{post_data.get('permalink', '')}",
                            'created_utc': post_data.get('created_utc', 0),
                            'subreddit': subreddit,
                            'flair': post_data.get('link_flair_text', ''),
                            'selftext': post_data.get('selftext', ''),
                            'domain': post_data.get('domain', ''),
                            'is_self': post_data.get('is_self', False)
                        })
            
            logger.info(f"Fetched {len(posts)} robotics-related posts from r/{subreddit}")
            return posts
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from r/{subreddit}: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from r/{subreddit}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching from r/{subreddit}: {e}")
            return []
    
    def _is_robotics_related(self, post_data: Dict) -> bool:
        """Check if a Reddit post is robotics-related.
        
        Args:
            post_data: Reddit post data
            
        Returns:
            True if post is robotics-related
        """
        # Keywords that indicate robotics content
        robotics_keywords = [
            'robot', 'robotics', 'autonomous', 'automation', 'AI', 'artificial intelligence',
            'machine learning', 'computer vision', 'ROS', 'drone', 'UAV', 'self-driving',
            'cobot', 'collaborative robot', 'humanoid', 'swarm', 'soft robotics',
            'exoskeleton', 'prosthetic', 'surgical robot', 'industrial robot',
            'service robot', 'mobile robot', 'manipulator', 'gripper', 'sensor',
            'actuator', 'control system', 'path planning', 'SLAM', 'localization'
        ]
        
        # Keywords to exclude
        exclude_keywords = [
            'job posting', 'hiring', 'career', 'webinar', 'advertisement',
            'sponsored', 'sales pitch', 'apply now', 'remote work', 'internship',
            'event registration', 'conference', 'workshop', 'training'
        ]
        
        title = post_data.get('title', '').lower()
        selftext = post_data.get('selftext', '').lower()
        content = f"{title} {selftext}"
        
        # Check for exclude keywords first
        for keyword in exclude_keywords:
            if keyword in content:
                return False
        
        # Check for robotics keywords
        for keyword in robotics_keywords:
            if keyword in content:
                return True
        
        # Check subreddit-specific content
        subreddit = post_data.get('subreddit', '').lower()
        if subreddit in ['robotics', 'ros', 'autonomousvehicles', 'drones']:
            return True
        
        return False
    
    def calculate_reddit_score(self, post: Dict) -> float:
        """Calculate a relevance score for a Reddit post.
        
        Args:
            post: Reddit post data
            
        Returns:
            Calculated score
        """
        base_score = 50.0
        
        # Score based on Reddit upvotes
        upvotes = post.get('score', 0)
        score_bonus = min(upvotes * 2, 100)  # Cap at 100 bonus points
        
        # Comments indicate engagement
        comments = post.get('num_comments', 0)
        comment_bonus = min(comments * 1.5, 50)  # Cap at 50 bonus points
        
        # Recency bonus (newer posts get higher scores)
        created_time = post.get('created_utc', 0)
        if created_time:
            age_hours = (datetime.now() - datetime.fromtimestamp(created_time)).total_seconds() / 3600
            recency_bonus = max(0, 20 - (age_hours / 6))  # Decay over 5 days
        else:
            recency_bonus = 0
        
        # Subreddit bonus (more relevant subreddits get higher scores)
        subreddit = post.get('subreddit', '').lower()
        subreddit_bonus = {
            'robotics': 15,
            'ros': 12,
            'autonomousvehicles': 10,
            'drones': 8,
            'machinelearning': 5,
            'artificial': 5
        }.get(subreddit, 0)
        
        # Flair bonus (posts with relevant flair)
        flair = post.get('flair', '').lower()
        flair_bonus = 5 if any(keyword in flair for keyword in ['research', 'news', 'breakthrough']) else 0
        
        total_score = base_score + score_bonus + comment_bonus + recency_bonus + subreddit_bonus + flair_bonus
        
        return total_score
    
    def convert_to_articles(self, posts: List[Dict]) -> List[Article]:
        """Convert Reddit posts to Article objects.
        
        Args:
            posts: List of Reddit post dictionaries
            
        Returns:
            List of Article objects
        """
        articles = []
        
        for post in posts:
            try:
                # Create content text
                title = post.get('title', '')
                selftext = post.get('selftext', '')
                content = f"{title}\n\n{selftext}" if selftext else title
                
                # Use post URL or permalink
                url = post.get('url', post.get('permalink', ''))
                
                # Generate intelligent summary using ArticleReader
                try:
                    from agent_integration.article_reader import ArticleReader
                    article_reader = ArticleReader()
                    
                    # Try to get full content from the Reddit post URL
                    post_url = f"https://reddit.com{post.get('permalink', '')}"
                    enhanced_summary = article_reader.enhance_tweet_summary(
                        title=title,
                        content=content,
                        url=post_url,
                        topics=[post.get('subreddit', ''), 'reddit', 'community']
                    )
                    summary = enhanced_summary
                except Exception as e:
                    logger.debug(f"Could not generate intelligent summary for Reddit post: {e}")
                    # Fallback to basic summary
                    summary = selftext[:200] + "..." if len(selftext) > 200 else selftext
                    if not summary:
                        summary = f"Reddit post from r/{post.get('subreddit', '')} with {post.get('score', 0)} upvotes"
                
                # Create article
                article = Article(
                    id=post['id'],
                    text=content,
                    author_id=post.get('author') or '[deleted]',
                    author_username=post.get('author') or '[deleted]',
                    author_name=post.get('author') or '[deleted]',
                    author_followers=0,  # Reddit doesn't provide this easily
                    likes=post.get('score', 0),
                    retweets=0,  # Not applicable for Reddit
                    replies=post.get('num_comments', 0),
                    url=url,
                    created_at=datetime.fromtimestamp(post.get('created_utc', time.time())),
                    score=self.calculate_reddit_score(post),
                    topics=[post.get('subreddit', ''), 'reddit'],
                    categories=['reddit_community'],
                    summary=summary
                )
                
                articles.append(article)
                
            except Exception as e:
                logger.error(f"Error converting post {post.get('id', 'unknown')}: {e}")
                continue
        
        return articles
    
    def fetch_all_subreddits(self, sort: str = 'new', limit: int = 25) -> List[Article]:
        """Fetch posts from all monitored subreddits.
        
        Args:
            sort: Sort method ('new', 'hot', 'top')
            limit: Number of posts per subreddit
            
        Returns:
            List of Article objects
        """
        all_articles = []
        
        for subreddit in self.subreddits:
            try:
                posts = self.fetch_subreddit_posts(subreddit, sort, limit)
                articles = self.convert_to_articles(posts)
                all_articles.extend(articles)
                
                logger.info(f"Processed {len(articles)} articles from r/{subreddit}")
                
            except Exception as e:
                logger.error(f"Error processing subreddit r/{subreddit}: {e}")
                continue
        
        # Sort by score
        all_articles.sort(key=lambda x: x.score, reverse=True)
        
        logger.info(f"Total Reddit articles fetched: {len(all_articles)}")
        return all_articles
    
    def store_articles(self, articles: List[Article]) -> int:
        """Store Reddit articles in database.
        
        Args:
            articles: List of Article objects
            
        Returns:
            Number of articles stored
        """
        stored_count = 0
        
        for article in articles:
            try:
                # Check if URL already exists
                if not self.db.url_exists(article.url):
                    self.db.insert_article(article)
                    stored_count += 1
                else:
                    logger.debug(f"Reddit post already exists: {article.url}")
            except Exception as e:
                logger.error(f"Error storing Reddit article {article.id}: {e}")
        
        logger.info(f"Stored {stored_count} new Reddit articles")
        return stored_count
    
    def run_fetch_cycle(self) -> Dict:
        """Run a complete Reddit fetch cycle.
        
        Returns:
            Dictionary with fetch results
        """
        try:
            logger.info("Starting Reddit fetch cycle")
            
            # Fetch from multiple sort methods
            new_articles = self.fetch_all_subreddits('new', limit=15)
            hot_articles = self.fetch_all_subreddits('hot', limit=10)
            
            # Combine and deduplicate
            all_articles = new_articles + hot_articles
            seen_ids = set()
            unique_articles = []
            
            for article in all_articles:
                if article.id not in seen_ids:
                    seen_ids.add(article.id)
                    unique_articles.append(article)
            
            # Sort by score
            unique_articles.sort(key=lambda x: x.score, reverse=True)
            
            # Store articles
            stored_count = self.store_articles(unique_articles)
            
            # Get top articles from database
            top_articles = self.db.get_top_articles(limit=10)
            
            return {
                'total_fetched': len(unique_articles),
                'stored_count': stored_count,
                'top_articles': top_articles,
                'timestamp': datetime.now().isoformat(),
                'mode': 'reddit'
            }
            
        except Exception as e:
            logger.error(f"Error in Reddit fetch cycle: {e}")
            return {
                'total_fetched': 0,
                'stored_count': 0,
                'top_articles': [],
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'mode': 'reddit'
            }


def main():
    """Main function to test the Reddit scraper."""
    try:
        scraper = RedditScraper()
        
        # Test fetch
        result = scraper.run_fetch_cycle()
        
        print(f"Reddit fetch completed:")
        print(f"  Total fetched: {result.get('total_fetched', 0)}")
        print(f"  Stored: {result.get('stored_count', 0)}")
        print(f"  Top articles: {len(result.get('top_articles', []))}")
        
        if result.get('top_articles'):
            print("\nTop Reddit articles:")
            for i, article in enumerate(result['top_articles'][:3], 1):
                print(f"{i}. {article.text[:60]}... | Score: {article.score:.1f}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    main() 