#!/usr/bin/env python3
"""
Multi-source scraper for Robotics Radar.
Coordinates RSS, Reddit, Hacker News, and GitHub scrapers.
"""

import logging
import time
from datetime import datetime
from typing import List, Dict, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.database import DatabaseManager, Article
from scraper.rss_fetcher import RSSFetcher
from scraper.reddit_scraper import RedditScraper
from scraper.hackernews_scraper import HackerNewsScraper
from scraper.github_scraper import GitHubScraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiSourceScraper:
    """Coordinates multiple content sources for comprehensive robotics content discovery."""
    
    def __init__(self, config_path: str = "config/feeds.yaml"):
        """Initialize multi-source scraper.
        
        Args:
            config_path: Path to RSS feeds configuration
        """
        self.db = DatabaseManager()
        
        # Initialize individual scrapers
        self.rss_fetcher = RSSFetcher(config_path)
        self.reddit_scraper = RedditScraper()
        self.hn_scraper = HackerNewsScraper()
        
        # Initialize GitHub scraper with token if available
        github_token = os.getenv('GITHUB_TOKEN')
        self.github_scraper = GitHubScraper(github_token=github_token)
        
        # Source configuration
        self.sources = {
            'rss': {
                'enabled': True,
                'name': 'RSS Feeds',
                'scraper': self.rss_fetcher,
                'weight': 1.0
            },
            'reddit': {
                'enabled': True,
                'name': 'Reddit',
                'scraper': self.reddit_scraper,
                'weight': 0.8
            },
            'hackernews': {
                'enabled': True,
                'name': 'Hacker News',
                'scraper': self.hn_scraper,
                'weight': 0.9
            },
            'github': {
                'enabled': True,
                'name': 'GitHub',
                'scraper': self.github_scraper,
                'weight': 0.7
            }
        }
    
    def fetch_from_source(self, source_key: str) -> Dict:
        """Fetch content from a specific source.
        
        Args:
            source_key: Source identifier ('rss', 'reddit', 'hackernews', 'github')
            
        Returns:
            Dictionary with fetch results
        """
        source_config = self.sources.get(source_key)
        if not source_config or not source_config['enabled']:
            return {
                'total_fetched': 0,
                'stored_count': 0,
                'top_articles': [],
                'error': f'Source {source_key} not enabled',
                'timestamp': datetime.now().isoformat(),
                'mode': source_key
            }
        
        try:
            logger.info(f"Fetching from {source_config['name']}...")
            result = source_config['scraper'].run_fetch_cycle()
            
            # Apply source weight to scores
            if result.get('top_articles'):
                for article in result['top_articles']:
                    article.score *= source_config['weight']
            
            logger.info(f"✅ {source_config['name']}: {result.get('total_fetched', 0)} articles")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error fetching from {source_config['name']}: {e}")
            return {
                'total_fetched': 0,
                'stored_count': 0,
                'top_articles': [],
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'mode': source_key
            }
    
    def fetch_all_sources(self, sources: List[str] = None) -> Dict:
        """Fetch content from all enabled sources or specified sources.
        
        Args:
            sources: List of source keys to fetch from (None for all enabled)
            
        Returns:
            Dictionary with combined results
        """
        if sources is None:
            sources = [key for key, config in self.sources.items() if config['enabled']]
        
        logger.info(f"Starting multi-source fetch cycle for: {', '.join(sources)}")
        
        all_results = {}
        total_fetched = 0
        total_stored = 0
        all_articles = []
        
        for source_key in sources:
            try:
                result = self.fetch_from_source(source_key)
                all_results[source_key] = result
                
                total_fetched += result.get('total_fetched', 0)
                total_stored += result.get('stored_count', 0)
                
                # Collect top articles from each source
                if result.get('top_articles'):
                    all_articles.extend(result['top_articles'])
                
                # Small delay between sources
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing source {source_key}: {e}")
                all_results[source_key] = {
                    'total_fetched': 0,
                    'stored_count': 0,
                    'top_articles': [],
                    'error': str(e),
                    'timestamp': datetime.now().isoformat(),
                    'mode': source_key
                }
        
        # Get overall top articles from database
        top_articles = self.db.get_top_articles(limit=15)
        
        # Create combined result
        combined_result = {
            'total_fetched': total_fetched,
            'total_stored': total_stored,
            'top_articles': top_articles,
            'source_results': all_results,
            'timestamp': datetime.now().isoformat(),
            'mode': 'multi_source'
        }
        
        logger.info(f"Multi-source fetch completed: {total_fetched} total fetched, {total_stored} stored")
        return combined_result
    
    def fetch_quick_update(self) -> Dict:
        """Fetch a quick update from all sources (optimized for speed).
        
        Returns:
            Dictionary with quick update results
        """
        logger.info("Starting quick multi-source update...")
        
        # Use smaller limits for quick updates
        quick_config = {
            'rss': {'limit': 20},
            'reddit': {'limit': 15},
            'hackernews': {'limit': 25},
            'github': {'limit': 20}
        }
        
        all_results = {}
        total_fetched = 0
        total_stored = 0
        
        for source_key, config in self.sources.items():
            if not config['enabled']:
                continue
            
            try:
                # For RSS, we can't easily change limits, so use existing
                if source_key == 'rss':
                    result = self.rss_fetcher.run_fetch_cycle()
                elif source_key == 'reddit':
                    # Fetch fewer posts for quick update
                    articles = self.reddit_scraper.fetch_all_subreddits('new', limit=10)
                    stored_count = self.reddit_scraper.store_articles(articles)
                    result = {
                        'total_fetched': len(articles),
                        'stored_count': stored_count,
                        'top_articles': self.db.get_top_articles(limit=5),
                        'timestamp': datetime.now().isoformat(),
                        'mode': 'reddit'
                    }
                elif source_key == 'hackernews':
                    # Fetch fewer stories for quick update
                    articles = self.hn_scraper.fetch_robotics_stories('new', limit=20)
                    stored_count = self.hn_scraper.store_articles(articles)
                    result = {
                        'total_fetched': len(articles),
                        'stored_count': stored_count,
                        'top_articles': self.db.get_top_articles(limit=5),
                        'timestamp': datetime.now().isoformat(),
                        'mode': 'hackernews'
                    }
                elif source_key == 'github':
                    # Fetch fewer repos for quick update
                    articles = self.github_scraper.fetch_robotics_repos(limit=15)
                    stored_count = self.github_scraper.store_articles(articles)
                    result = {
                        'total_fetched': len(articles),
                        'stored_count': stored_count,
                        'top_articles': self.db.get_top_articles(limit=5),
                        'timestamp': datetime.now().isoformat(),
                        'mode': 'github'
                    }
                
                all_results[source_key] = result
                total_fetched += result.get('total_fetched', 0)
                total_stored += result.get('stored_count', 0)
                
            except Exception as e:
                logger.error(f"Error in quick update for {source_key}: {e}")
                all_results[source_key] = {
                    'total_fetched': 0,
                    'stored_count': 0,
                    'top_articles': [],
                    'error': str(e),
                    'timestamp': datetime.now().isoformat(),
                    'mode': source_key
                }
        
        # Get diverse articles (mix of high-score and recent)
        top_articles = self.db.get_diverse_articles(limit=10)
        
        return {
            'total_fetched': total_fetched,
            'total_stored': total_stored,
            'top_articles': top_articles,
            'source_results': all_results,
            'timestamp': datetime.now().isoformat(),
            'mode': 'quick_update'
        }
    
    def get_source_status(self) -> Dict:
        """Get status of all sources.
        
        Returns:
            Dictionary with source status information
        """
        status = {}
        
        for source_key, config in self.sources.items():
            status[source_key] = {
                'enabled': config['enabled'],
                'name': config['name'],
                'weight': config['weight']
            }
        
        return status
    
    def enable_source(self, source_key: str, enabled: bool = True):
        """Enable or disable a specific source.
        
        Args:
            source_key: Source identifier
            enabled: Whether to enable the source
        """
        if source_key in self.sources:
            self.sources[source_key]['enabled'] = enabled
            logger.info(f"{'Enabled' if enabled else 'Disabled'} source: {source_key}")
        else:
            logger.error(f"Unknown source: {source_key}")
    
    def set_source_weight(self, source_key: str, weight: float):
        """Set the weight for a specific source.
        
        Args:
            source_key: Source identifier
            weight: Weight multiplier for scores
        """
        if source_key in self.sources:
            self.sources[source_key]['weight'] = weight
            logger.info(f"Set weight for {source_key}: {weight}")
        else:
            logger.error(f"Unknown source: {source_key}")


def main():
    """Main function to test the multi-source scraper."""
    try:
        scraper = MultiSourceScraper()
        
        # Show source status
        status = scraper.get_source_status()
        print("Source Status:")
        for source, info in status.items():
            print(f"  {source}: {'✅' if info['enabled'] else '❌'} {info['name']} (weight: {info['weight']})")
        
        print("\n" + "="*50)
        
        # Test quick update
        print("Running quick multi-source update...")
        result = scraper.fetch_quick_update()
        
        print(f"\nQuick update completed:")
        print(f"  Total fetched: {result.get('total_fetched', 0)}")
        print(f"  Total stored: {result.get('total_stored', 0)}")
        print(f"  Top articles: {len(result.get('top_articles', []))}")
        
        # Show results by source
        print("\nResults by source:")
        for source, source_result in result.get('source_results', {}).items():
            print(f"  {source}: {source_result.get('total_fetched', 0)} fetched, {source_result.get('stored_count', 0)} stored")
        
        if result.get('top_articles'):
            print("\nTop articles across all sources:")
            for i, article in enumerate(result['top_articles'][:5], 1):
                source = article.id.split('_')[0] if '_' in article.id else 'unknown'
                print(f"{i}. [{source}] {article.text[:60]}... | Score: {article.score:.1f}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    main() 