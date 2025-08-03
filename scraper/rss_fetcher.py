"""
RSS/Atom feed fetching module for Robotics Radar.
Fetches content from RSS/Atom feeds and Medium publications.
"""

import feedparser
import logging
import yaml
import os
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sys
import re
from urllib.parse import urlparse

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.database import DatabaseManager, Article
from scoring.scoring_model import ScoringModel
from nlp.keyword_extraction import KeywordExtractor
from agent_integration.article_reader import ArticleReader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RSSFetcher:
    """Fetches content from RSS/Atom feeds and Medium publications."""
    
    def __init__(self, config_path: str = "config/feeds.yaml"):
        """Initialize RSS fetcher.
        
        Args:
            config_path: Path to feeds configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.db = DatabaseManager()
        self.scoring_model = ScoringModel("config/keywords.yaml")
        self.keyword_extractor = KeywordExtractor()
        self.article_reader = ArticleReader()
        
    def _load_config(self) -> Dict:
        """Load configuration from YAML file.
        
        Returns:
            Configuration dictionary
        """
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
            logger.info("RSS feeds configuration loaded successfully")
            return config
        except Exception as e:
            logger.error(f"Error loading RSS configuration: {e}")
            raise
    
    def fetch_feeds(self, max_items: int = 50) -> List[Article]:
        """Fetch content from all configured feeds.
        
        Args:
            max_items: Maximum number of items to fetch total
            
        Returns:
            List of Article objects
        """
        all_items = []
        feeds = self.config.get('feeds', [])
        
        for feed_config in feeds:
            if not feed_config.get('enabled', True):
                continue
                
            try:
                items = self._fetch_single_feed(feed_config)
                all_items.extend(items)
                logger.info(f"Fetched {len(items)} items from {feed_config['name']}")
                
                # Small delay to be respectful to servers
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error fetching feed {feed_config.get('name', 'Unknown')}: {e}")
                continue
        
        # Filter and process items
        filtered_items = self._filter_items(all_items)
        
        # Convert to Article objects
        articles = self._convert_to_articles(filtered_items)
        
        # Sort by score and limit
        articles.sort(key=lambda x: x.score, reverse=True)
        return articles[:max_items]
    
    def _fetch_single_feed(self, feed_config: Dict) -> List[Dict]:
        """Fetch content from a single feed.
        
        Args:
            feed_config: Feed configuration dictionary
            
        Returns:
            List of feed items
        """
        url = feed_config['url']
        name = feed_config.get('name', 'Unknown')
        tags = feed_config.get('tags', [])
        
        logger.info(f"Fetching feed: {name} ({url})")
        
        try:
            # Parse the feed
            feed = feedparser.parse(url)
            
            if feed.bozo:
                logger.warning(f"Feed {name} has parsing issues: {feed.bozo_exception}")
            
            items = []
            for entry in feed.entries:
                try:
                    item = self._process_feed_entry(entry, feed_config)
                    if item:
                        items.append(item)
                except Exception as e:
                    logger.error(f"Error processing entry from {name}: {e}")
                    continue
            
            logger.info(f"Successfully fetched {len(items)} items from {name}")
            return items
            
        except Exception as e:
            logger.error(f"Error fetching feed {name}: {e}")
            return []
    
    def _process_feed_entry(self, entry, feed_config: Dict) -> Optional[Dict]:
        """Process a single feed entry.
        
        Args:
            entry: Feed entry object
            feed_config: Feed configuration
            
        Returns:
            Processed item dictionary or None if filtered out
        """
        try:
            # Extract basic information
            title = getattr(entry, 'title', 'No Title')
            link = getattr(entry, 'link', '')
            summary = getattr(entry, 'summary', '')
            content = getattr(entry, 'content', [{}])[0].get('value', '') if hasattr(entry, 'content') else ''
            
            # Use content if available, otherwise summary
            full_content = content if content else summary
            
            # Get author
            author = getattr(entry, 'author', 'Unknown')
            if hasattr(entry, 'authors') and entry.authors:
                author = entry.authors[0].get('name', author)
            
            # Get published date
            published = getattr(entry, 'published_parsed', None)
            if published:
                published_date = datetime(*published[:6])
            else:
                published_date = datetime.now()
            
            # Get tags/categories
            tags = []
            if hasattr(entry, 'tags'):
                tags.extend([tag.term for tag in entry.tags])
            if hasattr(entry, 'category'):
                tags.append(entry.category)
            if hasattr(entry, 'categories'):
                tags.extend(entry.categories)
            
            # Add feed tags
            tags.extend(feed_config.get('tags', []))
            
            # Create item
            item = {
                'title': title,
                'link': link,
                'content': full_content,
                'author': author,
                'published_date': published_date,
                'tags': list(set(tags)),  # Remove duplicates
                'source_name': feed_config.get('name', 'Unknown'),
                'source_url': feed_config.get('url', ''),
                'feed_tags': feed_config.get('tags', [])
            }
            
            return item
            
        except Exception as e:
            logger.error(f"Error processing feed entry: {e}")
            return None
    
    def _filter_items(self, items: List[Dict]) -> List[Dict]:
        """Filter items based on configuration.
        
        Args:
            items: List of feed items
            
        Returns:
            Filtered list of items
        """
        filters = self.config.get('filters', {})
        include_keywords = filters.get('include_keywords', [])
        exclude_keywords = filters.get('exclude_keywords', [])
        min_content_length = filters.get('min_content_length', 100)
        max_age_days = filters.get('max_age_days', 7)
        
        filtered_items = []
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        for item in items:
            # Check content length
            content_length = len(item.get('content', '')) + len(item.get('title', ''))
            if content_length < min_content_length:
                continue
            
            # Check age
            if item.get('published_date', datetime.now()) < cutoff_date:
                continue
            
            # Check for exclude keywords
            content_text = f"{item.get('title', '')} {item.get('content', '')}".lower()
            if any(keyword.lower() in content_text for keyword in exclude_keywords):
                continue
            
            # Check for include keywords (at least one must be present)
            if include_keywords:
                if not any(keyword.lower() in content_text for keyword in include_keywords):
                    continue
            
            # Check if content is robotics-related
            if not self.keyword_extractor.is_robotics_related(content_text):
                continue
            
            filtered_items.append(item)
        
        logger.info(f"Filtered {len(items)} items down to {len(filtered_items)}")
        return filtered_items
    
    def _convert_to_articles(self, items: List[Dict]) -> List[Article]:
        """Convert feed items to Article objects.
        
        Args:
            items: List of feed items
            
        Returns:
            List of Article objects
        """
        tweets = []
        scoring_weights = self.config.get('scoring_weights', {})
        
        for item in items:
            try:
                # Extract topics and categories
                content_text = f"{item['title']} {item['content']}"
                topics = self.keyword_extractor.extract_topics(content_text)
                categories = self.keyword_extractor.extract_categories(content_text)
                
                # Generate summary
                summary = self._generate_summary(item['title'], item['content'], topics, item['link'])
                
                # Try to enhance summary by reading the actual article
                try:
                    enhanced_summary = self.article_reader.enhance_tweet_summary(
                        type('MockTweet', (), {'url': item['link'], 'summary': summary})()
                    )
                    if enhanced_summary and enhanced_summary != summary:
                        summary = enhanced_summary
                except Exception as e:
                    logger.debug(f"Could not enhance summary for {item['link']}: {e}")
                
                # Calculate score
                score = self._calculate_rss_score(item, scoring_weights)
                
                # Create Article object
                article = Article(
                    id=f"rss_{hash(item['link']) % 1000000}_{int(time.time())}",
                    text=f"{item['title']}\n\n{item['content'][:200]}...",
                    author_id=f"rss_{hash(item['author']) % 1000000}",
                    author_username=item['author'].replace(' ', '_').lower()[:20],
                    author_name=item['author'],
                    author_followers=1000,  # Default for RSS authors
                    likes=0,  # RSS doesn't have likes
                    retweets=0,  # RSS doesn't have retweets
                    replies=0,  # RSS doesn't have replies
                    url=item['link'],  # This is the real URL!
                    created_at=item['published_date'],
                    topics=topics,
                    categories=categories,
                    summary=summary,
                    score=score
                )
                
                tweets.append(article)
                
            except Exception as e:
                logger.error(f"Error converting item to article: {e}")
                continue
        
        return tweets
    
    def _calculate_rss_score(self, item: Dict, weights: Dict) -> float:
        """Calculate score for RSS content.
        
        Args:
            item: Feed item
            weights: Scoring weights configuration
            
        Returns:
            Calculated score
        """
        score = weights.get('base_score', 50.0)
        
        # Content length bonus
        content_length = len(item.get('content', ''))
        score += content_length * weights.get('content_length_bonus', 0.1)
        
        # Recency bonus
        age_hours = (datetime.now() - item.get('published_date', datetime.now())).total_seconds() / 3600
        recency_bonus = weights.get('recency_bonus', 10.0)
        score += max(0, recency_bonus - (age_hours / 24))  # Decay over days
        
        # Source bonus
        source_name = item.get('source_name', '').lower()
        source_bonus = weights.get('source_bonus', {})
        for source, bonus in source_bonus.items():
            if source in source_name:
                score += bonus
                break
        
        # Tag bonus
        tags = item.get('tags', [])
        tag_bonus = weights.get('tag_bonus', {})
        for tag in tags:
            if tag.lower() in tag_bonus:
                score += tag_bonus[tag.lower()]
        
        return score
    
    def _generate_summary(self, title: str, content: str, topics: List[str], url: str = None) -> str:
        """Generate a summary for RSS content.
        
        Args:
            title: Article title
            content: Article content
            topics: Extracted topics
            url: Article URL for enhanced analysis
            
        Returns:
            Generated summary
        """
        try:
            # Try to use ArticleReader for enhanced summary if URL is available
            if url and url.startswith('http'):
                try:
                    from agent_integration.article_reader import ArticleReader
                    article_reader = ArticleReader()
                    article_content = article_reader.read_article(url)
                    
                    if article_content and article_content.get('summary'):
                        enhanced_summary = article_content['summary']
                        # Clean and truncate enhanced summary
                        clean_summary = self._clean_content_for_summary(enhanced_summary)
                        if len(clean_summary) > 200:
                            clean_summary = clean_summary[:200] + "..."
                        return clean_summary
                except Exception as e:
                    logger.debug(f"Could not enhance summary with ArticleReader for {url}: {e}")
            
            # Fallback to content-based summary
            clean_content = self._clean_content_for_summary(content)
            
            # Extract first meaningful sentence
            sentences = clean_content.split('.')
            meaningful_sentences = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 20 and not self._is_metadata_sentence(sentence):
                    meaningful_sentences.append(sentence)
                    if len(meaningful_sentences) >= 2:
                        break
            
            if meaningful_sentences:
                summary = '. '.join(meaningful_sentences) + '.'
                summary = summary[:200] + "..." if len(summary) > 200 else summary
            else:
                # Fallback to title-based summary
                key_topics = topics[:3] if topics else []
                if "breakthrough" in title.lower() or "new" in title.lower():
                    summary = f"🚀 New breakthrough in robotics: {title}"
                elif "research" in title.lower() or "study" in title.lower():
                    summary = f"🔬 Research update: {title}"
                elif "announcement" in title.lower() or "launch" in title.lower():
                    summary = f"📢 Announcement: {title}"
                else:
                    summary = f"📰 {title}"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"📰 {title[:100]}..."
    
    def _clean_content_for_summary(self, content: str) -> str:
        """Clean content for summary generation.
        
        Args:
            content: Raw content
            
        Returns:
            Cleaned content
        """
        import re
        
        # Remove HTML tags
        clean_content = re.sub(r'<[^>]+>', '', content)
        
        # Remove image descriptions and metadata more aggressively
        clean_content = re.sub(r'<img[^>]*alt="[^"]*"[^>]*>', '', clean_content)
        clean_content = re.sub(r'Source:\s*[^.]*\.', '', clean_content)
        clean_content = re.sub(r'Credit:\s*[^.]*\.', '', clean_content)
        clean_content = re.sub(r'Image:\s*[^.]*\.', '', clean_content)
        clean_content = re.sub(r'A computer-generated[^.]*\.', '', clean_content)
        clean_content = re.sub(r'AI-generated[^.]*\.', '', clean_content)
        clean_content = re.sub(r'This image shows[^.]*\.', '', clean_content)
        clean_content = re.sub(r'The image depicts[^.]*\.', '', clean_content)
        clean_content = re.sub(r'Photo:[^.]*\.', '', clean_content)
        clean_content = re.sub(r'Picture:[^.]*\.', '', clean_content)
        
        # Remove extra whitespace
        clean_content = re.sub(r'\s+', ' ', clean_content)
        
        return clean_content.strip()
    
    def _is_metadata_sentence(self, sentence: str) -> bool:
        """Check if a sentence is metadata rather than content.
        
        Args:
            sentence: Sentence to check
            
        Returns:
            True if it's metadata
        """
        metadata_patterns = [
            r'^Source:',
            r'^Credit:',
            r'^Image:',
            r'^<img',
            r'^A computer-generated',
            r'^AI-generated',
            r'^This image shows',
            r'^The image depicts',
            r'^Photo:',
            r'^Picture:'
        ]
        
        import re
        sentence_lower = sentence.lower()
        
        for pattern in metadata_patterns:
            if re.search(pattern, sentence_lower):
                return True
        
        return False
    
    def store_items(self, articles: List[Article]) -> int:
        """Store RSS items in database.
        
        Args:
            articles: List of Article objects
            
        Returns:
            Number of items stored
        """
        stored_count = 0
        for article in articles:
            try:
                # Check if this URL already exists in the database
                if not self.db.url_exists(article.url):
                    self.db.insert_article(article)
                    stored_count += 1
                else:
                    logger.debug(f"URL already exists, skipping: {article.url}")
            except Exception as e:
                logger.error(f"Error storing RSS item {article.id}: {e}")
        
        logger.info(f"Stored {stored_count} new RSS items in database")
        return stored_count
    
    def run_fetch_cycle(self) -> Dict:
        """Run a complete RSS fetch cycle.
        
        Returns:
            Dictionary with fetch results
        """
        try:
            logger.info("Starting RSS feed fetch cycle")
            
            # Fetch items from all feeds
            articles = self.fetch_feeds(max_items=30)
            
            if not articles:
                logger.warning("No RSS items fetched in this cycle")
                return {
                    'total_fetched': 0,
                    'stored_count': 0,
                    'top_articles': [],
                    'error': 'No RSS items available',
                    'timestamp': datetime.now().isoformat(),
                    'mode': 'rss'
                }
            
            # Store items
            stored_count = self.store_items(articles)
            
            # Get top items from database (not current cycle) to avoid duplicates
            top_articles = self.db.get_top_articles(limit=10)
            logger.info(f"Selected top {len(top_articles)} RSS items from database")
            
            return {
                'total_fetched': len(articles),
                'stored_count': stored_count,
                'top_articles': top_articles,
                'timestamp': datetime.now().isoformat(),
                'mode': 'rss'
            }
            
        except Exception as e:
            logger.error(f"Error in RSS fetch cycle: {e}")
            return {
                'total_fetched': 0,
                'stored_count': 0,
                'top_articles': [],
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'mode': 'rss'
            }
    
    def get_fetch_stats(self) -> Dict:
        """Get RSS fetch statistics.
        
        Returns:
            Dictionary with fetch statistics
        """
        try:
            # Get total articles count
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM articles")
                total_articles = cursor.fetchone()['count']
                
                # Get recent articles (last 24 hours)
                cursor.execute("""
                    SELECT COUNT(*) as count FROM articles 
                    WHERE created_at >= datetime('now', '-1 day')
                """)
                recent_articles = cursor.fetchone()['count']
            
            return {
                'total_articles': total_articles,
                'recent_articles_24h': recent_articles,
                'feeds_configured': len(self.config.get('feeds', [])),
                'last_fetch': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting RSS fetch stats: {e}")
            return {}


def main():
    """Main function to test the RSS fetcher."""
    try:
        fetcher = RSSFetcher()
        
        # Run a test fetch cycle
        result = fetcher.run_fetch_cycle()
        
        print(f"RSS fetch cycle completed: {result}")
        
        if result['top_articles']:
            print(f"\nTop {len(result['top_articles'])} RSS items:")
            for i, article in enumerate(result['top_articles'][:3], 1):
                print(f"{i}. {article.author_name}: {article.text[:100]}...")
                print(f"   URL: {article.url}")
                print(f"   Score: {article.score:.2f}")
                print()
        
    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    main() 