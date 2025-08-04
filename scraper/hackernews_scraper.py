#!/usr/bin/env python3
"""
Hacker News scraper for Robotics Radar.
Fetches robotics-related content from Hacker News using the official API.
"""

import requests
import logging
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.database import DatabaseManager, Article

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HackerNewsScraper:
    """Scrapes robotics content from Hacker News."""
    
    def __init__(self):
        """Initialize Hacker News scraper."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RoboticsRadar/1.0 (Educational Research Tool)',
            'Accept': 'application/json'
        })
        self.db = DatabaseManager()
        
        # HN API endpoints
        self.base_url = "https://hacker-news.firebaseio.com/v0"
        self.endpoints = {
            'top_stories': '/topstories.json',
            'new_stories': '/newstories.json',
            'ask_stories': '/askstories.json',
            'show_stories': '/showstories.json',
            'item': '/item/{}.json'
        }
        
        # Rate limiting
        self.request_delay = 0.1  # HN API is very permissive
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Implement rate limiting for HN API."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def fetch_story_ids(self, story_type: str = 'new', limit: int = 100) -> List[int]:
        """Fetch story IDs from HN API.
        
        Args:
            story_type: Type of stories ('top', 'new', 'ask', 'show')
            limit: Maximum number of IDs to fetch
            
        Returns:
            List of story IDs
        """
        try:
            self._rate_limit()
            
            endpoint = self.endpoints.get(f'{story_type}_stories', self.endpoints['new_stories'])
            url = f"{self.base_url}{endpoint}"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            story_ids = response.json()
            return story_ids[:limit]
            
        except Exception as e:
            logger.error(f"Error fetching {story_type} story IDs: {e}")
            return []
    
    def fetch_story_details(self, story_id: int) -> Optional[Dict]:
        """Fetch detailed information for a specific story.
        
        Args:
            story_id: HN story ID
            
        Returns:
            Story details dictionary or None
        """
        try:
            self._rate_limit()
            
            endpoint = self.endpoints['item'].format(story_id)
            url = f"{self.base_url}{endpoint}"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            story_data = response.json()
            
            # Only return story-type items (not comments)
            if story_data and story_data.get('type') == 'story':
                return story_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching story {story_id}: {e}")
            return None
    
    def _is_robotics_related(self, story_data: Dict) -> bool:
        """Check if a HN story is robotics-related.
        
        Args:
            story_data: HN story data
            
        Returns:
            True if story is robotics-related
        """
        # Keywords that indicate robotics content
        robotics_keywords = [
            'robot', 'robotics', 'autonomous', 'automation', 'AI', 'artificial intelligence',
            'machine learning', 'computer vision', 'ROS', 'drone', 'UAV', 'self-driving',
            'cobot', 'collaborative robot', 'humanoid', 'swarm', 'soft robotics',
            'exoskeleton', 'prosthetic', 'surgical robot', 'industrial robot',
            'service robot', 'mobile robot', 'manipulator', 'gripper', 'sensor',
            'actuator', 'control system', 'path planning', 'SLAM', 'localization',
            'neural network', 'deep learning', 'reinforcement learning', 'computer vision',
            'autonomous vehicle', 'tesla', 'waymo', 'cruise', 'boston dynamics'
        ]
        
        # Keywords to exclude
        exclude_keywords = [
            'job posting', 'hiring', 'career', 'webinar', 'advertisement',
            'sponsored', 'sales pitch', 'apply now', 'remote work', 'internship',
            'event registration', 'conference', 'workshop', 'training'
        ]
        
        title = story_data.get('title', '').lower()
        content = title
        
        # Check for exclude keywords first
        for keyword in exclude_keywords:
            if keyword in content:
                return False
        
        # Check for robotics keywords
        for keyword in robotics_keywords:
            if keyword in content:
                return True
        
        # Check URL domain for robotics-related sites
        url = story_data.get('url', '')
        robotics_domains = [
            'arxiv.org', 'ieee.org', 'robohub.org', 'therobotreport.com',
            'robotics.org', 'mit.edu', 'stanford.edu', 'berkeley.edu',
            'cmu.edu', 'bostondynamics.com', 'openai.com', 'nvidia.com',
            'tesla.com', 'waymo.com', 'cruise.com'
        ]
        
        for domain in robotics_domains:
            if domain in url:
                return True
        
        return False
    
    def calculate_hn_score(self, story_data: Dict) -> float:
        """Calculate a relevance score for a HN story.
        
        Args:
            story_data: HN story data
            
        Returns:
            Calculated score
        """
        base_score = 50.0
        
        # Score based on HN points
        points = story_data.get('score', 0)
        points_bonus = min(points * 3, 150)  # Cap at 150 bonus points
        
        # Comments indicate engagement
        comments = story_data.get('descendants', 0)
        comment_bonus = min(comments * 2, 100)  # Cap at 100 bonus points
        
        # Recency bonus (newer stories get higher scores)
        created_time = story_data.get('time', 0)
        if created_time:
            age_hours = (datetime.now() - datetime.fromtimestamp(created_time)).total_seconds() / 3600
            recency_bonus = max(0, 25 - (age_hours / 4))  # Decay over 4 days
        else:
            recency_bonus = 0
        
        # URL domain bonus (more relevant domains get higher scores)
        url = story_data.get('url', '')
        domain_bonus = 0
        if 'arxiv.org' in url:
            domain_bonus = 20
        elif 'ieee.org' in url or 'robohub.org' in url:
            domain_bonus = 15
        elif 'mit.edu' in url or 'stanford.edu' in url or 'berkeley.edu' in url:
            domain_bonus = 12
        elif 'bostondynamics.com' in url or 'openai.com' in url:
            domain_bonus = 10
        
        # Title keyword bonus
        title = story_data.get('title', '').lower()
        keyword_bonus = 0
        high_value_keywords = ['breakthrough', 'new', 'first', 'revolutionary', 'groundbreaking']
        for keyword in high_value_keywords:
            if keyword in title:
                keyword_bonus += 5
        
        total_score = base_score + points_bonus + comment_bonus + recency_bonus + domain_bonus + keyword_bonus
        
        return total_score
    
    def convert_to_articles(self, stories: List[Dict]) -> List[Article]:
        """Convert HN stories to Article objects.
        
        Args:
            stories: List of HN story dictionaries
            
        Returns:
            List of Article objects
        """
        articles = []
        
        for story in stories:
            try:
                # Create content text
                title = story.get('title', '')
                url = story.get('url', '')
                
                # Generate intelligent summary using ArticleReader
                try:
                    from agent_integration.article_reader import ArticleReader
                    article_reader = ArticleReader()
                    
                    # Try to get full content from the story URL
                    if url and url.startswith('http'):
                        enhanced_summary = article_reader.enhance_tweet_summary(
                            title=title,
                            content=title,
                            url=url,
                            topics=['hackernews', 'tech', 'robotics']
                        )
                        summary = enhanced_summary
                    else:
                        # Fallback for text-only posts
                        summary = f"HN story with {story.get('score', 0)} points and {story.get('descendants', 0)} comments"
                except Exception as e:
                    logger.debug(f"Could not generate intelligent summary for HN story: {e}")
                    # Fallback to basic summary
                    summary = f"HN story with {story.get('score', 0)} points and {story.get('descendants', 0)} comments"
                
                # Create article
                article = Article(
                    id=f"hn_{story['id']}",
                    text=title,
                    author_id=story.get('by', 'anonymous'),
                    author_username=story.get('by', 'anonymous'),
                    author_name=story.get('by', 'anonymous'),
                    author_followers=0,  # HN doesn't provide this
                    likes=story.get('score', 0),
                    retweets=0,  # Not applicable for HN
                    replies=story.get('descendants', 0),
                    url=url,
                    created_at=datetime.fromtimestamp(story.get('time', time.time())),
                    score=self.calculate_hn_score(story),
                    topics=['hackernews', 'tech'],
                    categories=['hackernews_community'],
                    summary=summary
                )
                
                articles.append(article)
                
            except Exception as e:
                logger.error(f"Error converting story {story.get('id', 'unknown')}: {e}")
                continue
        
        return articles
    
    def fetch_robotics_stories(self, story_type: str = 'new', limit: int = 100) -> List[Article]:
        """Fetch robotics-related stories from HN.
        
        Args:
            story_type: Type of stories ('top', 'new', 'ask', 'show')
            limit: Maximum number of stories to fetch
            
        Returns:
            List of Article objects
        """
        try:
            # Fetch story IDs
            story_ids = self.fetch_story_ids(story_type, limit)
            logger.info(f"Fetched {len(story_ids)} story IDs from HN {story_type}")
            
            # Fetch story details
            stories = []
            for story_id in story_ids:
                story_data = self.fetch_story_details(story_id)
                if story_data and self._is_robotics_related(story_data):
                    stories.append(story_data)
            
            # Convert to articles
            articles = self.convert_to_articles(stories)
            
            logger.info(f"Found {len(articles)} robotics-related stories from HN {story_type}")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching HN stories: {e}")
            return []
    
    def fetch_all_story_types(self) -> List[Article]:
        """Fetch robotics stories from all HN story types.
        
        Returns:
            List of Article objects
        """
        all_articles = []
        
        # Fetch from different story types
        story_types = ['new', 'top', 'ask', 'show']
        limits = [50, 30, 20, 20]  # Different limits for different types
        
        for story_type, limit in zip(story_types, limits):
            try:
                articles = self.fetch_robotics_stories(story_type, limit)
                all_articles.extend(articles)
                logger.info(f"Processed {len(articles)} articles from HN {story_type}")
                
            except Exception as e:
                logger.error(f"Error processing HN {story_type}: {e}")
                continue
        
        # Sort by score
        all_articles.sort(key=lambda x: x.score, reverse=True)
        
        logger.info(f"Total HN articles fetched: {len(all_articles)}")
        return all_articles
    
    def store_articles(self, articles: List[Article]) -> int:
        """Store HN articles in database.
        
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
                    logger.debug(f"HN story already exists: {article.url}")
            except Exception as e:
                logger.error(f"Error storing HN article {article.id}: {e}")
        
        logger.info(f"Stored {stored_count} new HN articles")
        return stored_count
    
    def run_fetch_cycle(self) -> Dict:
        """Run a complete HN fetch cycle.
        
        Returns:
            Dictionary with fetch results
        """
        try:
            logger.info("Starting Hacker News fetch cycle")
            
            # Fetch all story types
            articles = self.fetch_all_story_types()
            
            # Store articles
            stored_count = self.store_articles(articles)
            
            # Get top articles from database
            top_articles = self.db.get_top_articles(limit=10)
            
            return {
                'total_fetched': len(articles),
                'stored_count': stored_count,
                'top_articles': top_articles,
                'timestamp': datetime.now().isoformat(),
                'mode': 'hackernews'
            }
            
        except Exception as e:
            logger.error(f"Error in HN fetch cycle: {e}")
            return {
                'total_fetched': 0,
                'stored_count': 0,
                'top_articles': [],
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'mode': 'hackernews'
            }


def main():
    """Main function to test the HN scraper."""
    try:
        scraper = HackerNewsScraper()
        
        # Test fetch
        result = scraper.run_fetch_cycle()
        
        print(f"Hacker News fetch completed:")
        print(f"  Total fetched: {result.get('total_fetched', 0)}")
        print(f"  Stored: {result.get('stored_count', 0)}")
        print(f"  Top articles: {len(result.get('top_articles', []))}")
        
        if result.get('top_articles'):
            print("\nTop HN articles:")
            for i, article in enumerate(result['top_articles'][:3], 1):
                print(f"{i}. {article.text[:60]}... | Score: {article.score:.1f}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    main() 