#!/usr/bin/env python3
"""
Historical Data Import Script for Robotics Radar
Scans RSS feeds for content from the past 90 days and adds it to the database.
"""

import sys
import os
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.rss_fetcher import RSSFetcher
from storage.database import DatabaseManager
from notifier.telegram_bot import TelegramNotifier

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HistoricalDataImporter:
    """Imports historical data from RSS feeds."""
    
    def __init__(self):
        """Initialize the importer."""
        load_dotenv()
        self.fetcher = RSSFetcher()
        self.db = DatabaseManager()
        self.telegram_notifier = TelegramNotifier()
        
    def import_historical_data(self, days_back: int = 90, max_items_per_feed: int = 100):
        """Import historical data from RSS feeds.
        
        Args:
            days_back: Number of days to look back
            max_items_per_feed: Maximum items to fetch per feed
        """
        logger.info(f"Starting historical data import for the past {days_back} days")
        
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days_back)
        logger.info(f"Cutoff date: {cutoff_date.strftime('%Y-%m-%d')}")
        
        total_imported = 0
        total_processed = 0
        
        # Get all feeds from configuration
        feeds_config = self.fetcher._load_config()
        
        for feed_config in feeds_config['feeds']:
            try:
                feed_name = feed_config['name']
                feed_url = feed_config['url']
                
                logger.info(f"Processing feed: {feed_name}")
                
                # Fetch items from this feed
                items = self._fetch_feed_items(feed_url, max_items_per_feed)
                
                if not items:
                    logger.warning(f"No items found for {feed_name}")
                    continue
                
                # Filter items by date
                filtered_items = self._filter_items_by_date(items, cutoff_date)
                
                logger.info(f"Found {len(filtered_items)} items within date range for {feed_name}")
                
                # Process and store items
                imported_count = self._process_feed_items(filtered_items, feed_name)
                
                total_imported += imported_count
                total_processed += len(filtered_items)
                
                logger.info(f"Imported {imported_count}/{len(filtered_items)} items from {feed_name}")
                
            except Exception as e:
                logger.error(f"Error processing feed {feed_config.get('name', 'Unknown')}: {e}")
                continue
        
        logger.info(f"Historical import completed: {total_imported}/{total_processed} items imported")
        
        # Send summary notification
        self._send_import_summary(total_imported, total_processed, days_back)
        
        return total_imported, total_processed
    
    def _fetch_feed_items(self, feed_url: str, max_items: int) -> list:
        """Fetch items from a single RSS feed.
        
        Args:
            feed_url: URL of the RSS feed
            max_items: Maximum number of items to fetch
            
        Returns:
            List of feed items
        """
        try:
            import feedparser
            
            # Parse the feed
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                logger.warning(f"Feed parsing issues for {feed_url}: {feed.bozo_exception}")
            
            # Extract items
            items = []
            for entry in feed.entries[:max_items]:
                item = {
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'description': entry.get('description', ''),
                    'content': entry.get('content', [{}])[0].get('value', '') if entry.get('content') else '',
                    'published': entry.get('published_parsed', None),
                    'author': entry.get('author', ''),
                    'tags': [tag.term for tag in entry.get('tags', [])] if entry.get('tags') else []
                }
                items.append(item)
            
            return items
            
        except Exception as e:
            logger.error(f"Error fetching feed {feed_url}: {e}")
            return []
    
    def _filter_items_by_date(self, items: list, cutoff_date: datetime) -> list:
        """Filter items by publication date.
        
        Args:
            items: List of feed items
            cutoff_date: Cutoff date for filtering
            
        Returns:
            Filtered list of items
        """
        filtered_items = []
        
        for item in items:
            try:
                # Parse publication date
                if item['published']:
                    # Convert time tuple to datetime
                    import time
                    pub_date = datetime.fromtimestamp(time.mktime(item['published']))
                    
                    if pub_date >= cutoff_date:
                        filtered_items.append(item)
                else:
                    # If no date, include it (could be recent)
                    filtered_items.append(item)
                    
            except Exception as e:
                logger.debug(f"Error parsing date for item {item.get('title', 'Unknown')}: {e}")
                # Include items with date parsing errors
                filtered_items.append(item)
        
        return filtered_items
    
    def _process_feed_items(self, items: list, feed_name: str) -> int:
        """Process and store feed items.
        
        Args:
            items: List of feed items
            feed_name: Name of the feed
            
        Returns:
            Number of items successfully imported
        """
        imported_count = 0
        
        for item in items:
            try:
                # Check if URL already exists
                if self.db.url_exists(item['link']):
                    continue
                
                # Convert to Tweet object
                tweet = self._convert_item_to_tweet(item, feed_name)
                
                # Store in database
                if self.db.insert_tweet(tweet):
                    imported_count += 1
                
            except Exception as e:
                logger.error(f"Error processing item {item.get('title', 'Unknown')}: {e}")
                continue
        
        return imported_count
    
    def _convert_item_to_tweet(self, item: dict, feed_name: str):
        """Convert a feed item to a Tweet object.
        
        Args:
            item: Feed item dictionary
            feed_name: Name of the feed
            
        Returns:
            Tweet object
        """
        from storage.database import Tweet
        from nlp.keyword_extraction import KeywordExtractor
        
        # Extract content
        content = item.get('content', '') or item.get('description', '')
        
        # Extract topics
        keyword_extractor = KeywordExtractor()
        topics = keyword_extractor.extract_topics(item['title'] + " " + content)
        
        # Generate summary
        summary = self.fetcher._generate_summary(item['title'], content, topics, item['link'])
        
        # Create Tweet object
        tweet = Tweet(
            id=f"hist_{hash(item['link']) % 1000000}",
            text=item['title'],
            author_id=f"hist_{feed_name}",
            author_username=item.get('author', feed_name),
            author_name=item.get('author', feed_name),
            author_followers=1000,  # Default value for historical data
            likes=0,
            retweets=0,
            replies=0,
            url=item['link'],
            created_at=datetime.now(),  # Use current time for historical items
            score=100.0,  # Base score for historical items
            topics=topics,
            summary=summary
        )
        
        return tweet
    
    def _send_import_summary(self, imported: int, processed: int, days_back: int):
        """Send import summary notification.
        
        Args:
            imported: Number of items imported
            processed: Number of items processed
            days_back: Number of days looked back
        """
        try:
            if not self.telegram_notifier.is_available():
                return
            
            message = f"📊 *Historical Data Import Complete*\n\n"
            message += f"🔍 Scanned: Past {days_back} days\n"
            message += f"📝 Processed: {processed} articles\n"
            message += f"✅ Imported: {imported} new articles\n"
            message += f"📈 Success rate: {(imported/processed*100):.1f}%\n\n"
            message += f"🎉 Database now contains more historical robotics content!"
            
            # Send to all allowed users
            for user_id in self.telegram_notifier.allowed_users:
                try:
                    import asyncio
                    from telegram import Bot
                    bot = Bot(token=self.telegram_notifier.bot_token)
                    asyncio.run(bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode='Markdown'
                    ))
                except Exception as e:
                    logger.error(f"Error sending notification to user {user_id}: {e}")
            
            logger.info("Import summary notification sent")
            
        except Exception as e:
            logger.error(f"Error sending import summary: {e}")

def main():
    """Main function."""
    try:
        # Parse command line arguments
        import argparse
        parser = argparse.ArgumentParser(description='Import historical data from RSS feeds')
        parser.add_argument('--days', type=int, default=90, help='Number of days to look back (default: 90)')
        parser.add_argument('--max-items', type=int, default=100, help='Maximum items per feed (default: 100)')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be imported without actually importing')
        
        args = parser.parse_args()
        
        print(f"🤖 Robotics Radar - Historical Data Import")
        print(f"=" * 50)
        print(f"📅 Looking back: {args.days} days")
        print(f"📊 Max items per feed: {args.max_items}")
        print(f"🔍 Dry run: {args.dry_run}")
        print()
        
        if args.dry_run:
            print("🔍 Dry run mode - no data will be imported")
            print("Use --help for more options")
            return
        
        # Create importer and run import
        importer = HistoricalDataImporter()
        imported, processed = importer.import_historical_data(args.days, args.max_items)
        
        print(f"\n✅ Import completed successfully!")
        print(f"📊 Results: {imported}/{processed} items imported")
        
    except KeyboardInterrupt:
        print("\n⚠️  Import interrupted by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"\n❌ Import failed: {e}")

if __name__ == "__main__":
    main() 