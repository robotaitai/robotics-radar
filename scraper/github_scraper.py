#!/usr/bin/env python3
"""
GitHub scraper for Robotics Radar.
Fetches trending robotics repositories and searches for robotics-related projects.
"""

import requests
import logging
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sys
import os
from urllib.parse import urljoin, quote

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.database import DatabaseManager, Article

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitHubScraper:
    """Scrapes robotics content from GitHub."""
    
    def __init__(self, github_token: str = None):
        """Initialize GitHub scraper.
        
        Args:
            github_token: GitHub API token for higher rate limits
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RoboticsRadar/1.0 (Educational Research Tool)',
            'Accept': 'application/vnd.github.v3+json'
        })
        
        # Add GitHub token if provided
        if github_token:
            self.session.headers.update({
                'Authorization': f'token {github_token}'
            })
            self.rate_limit = 5000  # Authenticated rate limit
        else:
            self.rate_limit = 60  # Unauthenticated rate limit
        
        self.db = DatabaseManager()
        
        # GitHub API endpoints
        self.base_url = "https://api.github.com"
        self.endpoints = {
            'search_repos': '/search/repositories',
            'trending': 'https://github.com/trending',  # HTML scraping
            'topics': '/search/repositories'
        }
        
        # Rate limiting
        self.request_delay = 1.0  # GitHub API rate limiting
        self.last_request_time = 0
        self.request_count = 0
    
    def _rate_limit(self):
        """Implement rate limiting for GitHub API."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
        self.request_count += 1
    
    def search_robotics_repos(self, query: str = 'robotics', sort: str = 'stars', order: str = 'desc', limit: int = 30) -> List[Dict]:
        """Search for robotics repositories using GitHub API.
        
        Args:
            query: Search query
            sort: Sort method ('stars', 'forks', 'updated')
            order: Sort order ('desc', 'asc')
            limit: Maximum number of repositories to fetch
            
        Returns:
            List of repository dictionaries
        """
        try:
            self._rate_limit()
            
            url = f"{self.base_url}{self.endpoints['search_repos']}"
            
            params = {
                'q': query,
                'sort': sort,
                'order': order,
                'per_page': min(limit, 100)  # GitHub API max is 100
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            repos = data.get('items', [])
            
            logger.info(f"Found {len(repos)} repositories for query '{query}'")
            return repos[:limit]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching GitHub repos: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing GitHub API response: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error searching GitHub: {e}")
            return []
    
    def _is_robotics_related(self, repo_data: Dict) -> bool:
        """Check if a GitHub repository is robotics-related.
        
        Args:
            repo_data: GitHub repository data
            
        Returns:
            True if repository is robotics-related
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
        
        name = repo_data.get('name', '').lower()
        description = (repo_data.get('description') or '').lower()
        topics = [topic.lower() for topic in repo_data.get('topics', [])]
        content = f"{name} {description} {' '.join(topics)}"
        
        # Check for exclude keywords first
        for keyword in exclude_keywords:
            if keyword in content:
                return False
        
        # Check for robotics keywords
        for keyword in robotics_keywords:
            if keyword in content:
                return True
        
        # Check topics for robotics-related tags
        robotics_topics = ['robotics', 'robot', 'autonomous', 'automation', 'ai', 'machine-learning']
        for topic in topics:
            if topic in robotics_topics:
                return True
        
        return False
    
    def calculate_github_score(self, repo_data: Dict) -> float:
        """Calculate a relevance score for a GitHub repository.
        
        Args:
            repo_data: GitHub repository data
            
        Returns:
            Calculated score
        """
        base_score = 50.0
        
        # Score based on stars
        stars = repo_data.get('stargazers_count', 0)
        stars_bonus = min(stars * 0.5, 200)  # Cap at 200 bonus points
        
        # Forks indicate community interest
        forks = repo_data.get('forks_count', 0)
        forks_bonus = min(forks * 1.0, 100)  # Cap at 100 bonus points
        
        # Recent activity bonus
        updated_at = repo_data.get('updated_at', '')
        if updated_at:
            try:
                updated_time = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                age_days = (datetime.now(updated_time.tzinfo) - updated_time).days
                activity_bonus = max(0, 30 - age_days)  # Decay over 30 days
            except:
                activity_bonus = 0
        else:
            activity_bonus = 0
        
        # Language bonus (robotics-related languages)
        language = repo_data.get('language', '').lower()
        language_bonus = {
            'python': 10,
            'c++': 8,
            'c': 8,
            'javascript': 5,
            'java': 5,
            'matlab': 8,
            'ros': 12
        }.get(language, 0)
        
        # Repository size bonus (larger projects might be more substantial)
        size = repo_data.get('size', 0)
        size_bonus = min(size / 100, 20)  # Cap at 20 bonus points
        
        # Topics bonus
        topics = repo_data.get('topics', [])
        topic_bonus = 0
        high_value_topics = ['robotics', 'robot', 'autonomous', 'ai', 'machine-learning', 'computer-vision']
        for topic in topics:
            if topic.lower() in high_value_topics:
                topic_bonus += 5
        
        total_score = base_score + stars_bonus + forks_bonus + activity_bonus + language_bonus + size_bonus + topic_bonus
        
        return total_score
    
    def convert_to_articles(self, repos: List[Dict]) -> List[Article]:
        """Convert GitHub repositories to Article objects.
        
        Args:
            repos: List of GitHub repository dictionaries
            
        Returns:
            List of Article objects
        """
        articles = []
        
        # Initialize ArticleReader for intelligent summaries
        try:
            from agent_integration.article_reader import ArticleReader
            article_reader = ArticleReader()
        except ImportError:
            article_reader = None
            logger.warning("ArticleReader not available, using basic summaries")
        
        for repo in repos:
            try:
                # Create content text
                name = repo.get('name', '')
                description = repo.get('description', '')
                content = f"{name}\n\n{description}" if description else name
                
                # Generate intelligent summary using ArticleReader
                if article_reader:
                    try:
                        # Try to get README content from the repository
                        readme_url = f"{repo.get('html_url', '')}/blob/main/README.md"
                        summary = article_reader.enhance_tweet_summary(
                            title=name,
                            content=content,
                            url=repo.get('html_url', ''),
                            topics=['github', 'open-source'] + repo.get('topics', [])
                        )
                    except Exception as e:
                        logger.debug(f"Could not generate intelligent summary for {name}: {e}")
                        # Fallback to basic summary
                        stars = repo.get('stargazers_count', 0)
                        forks = repo.get('forks_count', 0)
                        language = repo.get('language', 'Unknown')
                        summary = f"GitHub repository with {stars} stars, {forks} forks, written in {language}"
                else:
                    # Fallback to basic summary
                    stars = repo.get('stargazers_count', 0)
                    forks = repo.get('forks_count', 0)
                    language = repo.get('language', 'Unknown')
                    summary = f"GitHub repository with {stars} stars, {forks} forks, written in {language}"
                
                # Create article
                article = Article(
                    id=f"github_{repo['id']}",
                    text=content,
                    author_id=repo.get('owner', {}).get('login', 'unknown'),
                    author_username=repo.get('owner', {}).get('login', 'unknown'),
                    author_name=repo.get('owner', {}).get('login', 'unknown'),
                    author_followers=repo.get('owner', {}).get('followers', 0),
                    likes=repo.get('stargazers_count', 0),
                    retweets=repo.get('forks_count', 0),
                    replies=0,  # Not applicable for GitHub
                    url=repo.get('html_url', ''),
                    created_at=datetime.fromisoformat(repo.get('created_at', datetime.now().isoformat()).replace('Z', '+00:00')),
                    score=self.calculate_github_score(repo),
                    topics=['github', 'open-source'] + repo.get('topics', []),
                    categories=['github_repository'],
                    summary=summary
                )
                
                articles.append(article)
                
            except Exception as e:
                logger.error(f"Error converting repo {repo.get('id', 'unknown')}: {e}")
                continue
        
        return articles
    
    def fetch_robotics_repos(self, limit: int = 50) -> List[Article]:
        """Fetch robotics-related repositories from GitHub.
        
        Args:
            limit: Maximum number of repositories to fetch
            
        Returns:
            List of Article objects
        """
        all_articles = []
        
        # Search queries for robotics content
        search_queries = [
            'robotics',
            'robot',
            'autonomous',
            'ROS',
            'drone',
            'self-driving',
            'machine learning robotics',
            'computer vision robot',
            'SLAM',
            'path planning'
        ]
        
        for query in search_queries:
            try:
                repos = self.search_robotics_repos(query, limit=limit//len(search_queries))
                
                # Filter for robotics-related repos
                robotics_repos = [repo for repo in repos if self._is_robotics_related(repo)]
                
                # Convert to articles
                articles = self.convert_to_articles(robotics_repos)
                all_articles.extend(articles)
                
                logger.info(f"Found {len(articles)} robotics articles for query '{query}'")
                
                # Rate limiting between queries
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing query '{query}': {e}")
                continue
        
        # Sort by score
        all_articles.sort(key=lambda x: x.score, reverse=True)
        
        logger.info(f"Total GitHub articles fetched: {len(all_articles)}")
        return all_articles
    
    def store_articles(self, articles: List[Article]) -> int:
        """Store GitHub articles in database.
        
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
                    logger.debug(f"GitHub repo already exists: {article.url}")
            except Exception as e:
                logger.error(f"Error storing GitHub article {article.id}: {e}")
        
        logger.info(f"Stored {stored_count} new GitHub articles")
        return stored_count
    
    def run_fetch_cycle(self) -> Dict:
        """Run a complete GitHub fetch cycle.
        
        Returns:
            Dictionary with fetch results
        """
        try:
            logger.info("Starting GitHub fetch cycle")
            
            # Fetch robotics repositories
            articles = self.fetch_robotics_repos(limit=50)
            
            # Store articles
            stored_count = self.store_articles(articles)
            
            # Get top articles from database
            top_articles = self.db.get_top_articles(limit=10)
            
            return {
                'total_fetched': len(articles),
                'stored_count': stored_count,
                'top_articles': top_articles,
                'timestamp': datetime.now().isoformat(),
                'mode': 'github'
            }
            
        except Exception as e:
            logger.error(f"Error in GitHub fetch cycle: {e}")
            return {
                'total_fetched': 0,
                'stored_count': 0,
                'top_articles': [],
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'mode': 'github'
            }


def main():
    """Main function to test the GitHub scraper."""
    try:
        # Check for GitHub token in environment
        github_token = os.getenv('GITHUB_TOKEN')
        
        scraper = GitHubScraper(github_token=github_token)
        
        # Test fetch
        result = scraper.run_fetch_cycle()
        
        print(f"GitHub fetch completed:")
        print(f"  Total fetched: {result.get('total_fetched', 0)}")
        print(f"  Stored: {result.get('stored_count', 0)}")
        print(f"  Top articles: {len(result.get('top_articles', []))}")
        
        if result.get('top_articles'):
            print("\nTop GitHub articles:")
            for i, article in enumerate(result['top_articles'][:3], 1):
                print(f"{i}. {article.text[:60]}... | Score: {article.score:.1f}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    main() 