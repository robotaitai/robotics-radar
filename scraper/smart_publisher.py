#!/usr/bin/env python3
"""
Smart Publisher for Robotics Radar
Sends one article every 30 minutes with intelligent selection:
1. New articles (created in last 2 hours) get priority
2. If no new articles, sends best unpublished article
3. Tracks publication status to avoid duplicates
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.database import DatabaseManager, Article
from notifier.telegram_bot import TelegramNotifier
from scraper.multi_source_scraper import MultiSourceScraper
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartPublisher:
    """Smart publisher that sends one article every 30 minutes."""
    
    def __init__(self):
        """Initialize the smart publisher."""
        self.db = DatabaseManager()
        self.telegram_notifier = TelegramNotifier()
        self.scraper = MultiSourceScraper()
        self.publish_interval = 30  # minutes
        self.last_publish_time = None
        
    def should_publish_now(self) -> bool:
        """Check if it's time to publish based on interval."""
        if self.last_publish_time is None:
            return True
        
        time_since_last = datetime.now() - self.last_publish_time
        return time_since_last.total_seconds() >= (self.publish_interval * 60)
    
    def get_next_article(self) -> Optional[Article]:
        """Get the next article to publish with smart selection."""
        # First, try to get a new article (created in last 2 hours)
        article = self.db.get_next_article_to_publish()
        
        if article:
            logger.info(f"Selected article for publishing: {article.text[:50]}... (Score: {article.score:.1f})")
            return article
        
        logger.warning("No articles available for publishing")
        return None
    
    def publish_single_article(self, article: Article) -> bool:
        """Publish a single article to Telegram.
        
        Args:
            article: Article to publish
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Publishing article: {article.text[:50]}...")
            
            # Send the article to Telegram
            success = self.telegram_notifier.send_single_article_sync(article)
            
            if success:
                # Mark as published in database
                self.db.mark_article_published(article.id)
                self.last_publish_time = datetime.now()
                logger.info(f"✅ Article published successfully: {article.id}")
                return True
            else:
                logger.error(f"❌ Failed to publish article: {article.id}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing article: {e}")
            return False
    
    def publish_cycle(self) -> bool:
        """Run one publish cycle - fetch new content and publish if needed."""
        try:
            logger.info("🔄 Starting smart publish cycle...")
            
            # Check if it's time to publish
            if not self.should_publish_now():
                time_until_next = (self.publish_interval * 60) - (datetime.now() - self.last_publish_time).total_seconds()
                logger.info(f"⏰ Not time to publish yet. Next publish in {time_until_next/60:.1f} minutes")
                return True
            
            # Fetch new content first
            logger.info("📡 Fetching new content...")
            fetch_result = self.scraper.fetch_all_sources()
            
            if fetch_result.get('error'):
                logger.error(f"Fetch cycle failed: {fetch_result['error']}")
                return False
            
            new_articles_count = fetch_result.get('total_stored', 0)
            logger.info(f"📊 Fetched {fetch_result.get('total_fetched', 0)} articles, stored {new_articles_count}")
            
            # Get next article to publish
            article = self.get_next_article()
            
            if article:
                # Publish the article
                success = self.publish_single_article(article)
                
                if success:
                    logger.info("✅ Publish cycle completed successfully")
                    return True
                else:
                    logger.error("❌ Publish cycle failed")
                    return False
            else:
                logger.warning("⚠️ No articles available to publish")
                return True
                
        except Exception as e:
            logger.error(f"Error in publish cycle: {e}")
            return False
    
    def run_continuous(self):
        """Run the publisher continuously."""
        logger.info(f"🚀 Starting Smart Publisher (interval: {self.publish_interval} minutes)")
        
        while True:
            try:
                # Run one publish cycle
                success = self.publish_cycle()
                
                if not success:
                    logger.error("Publish cycle failed, will retry in 5 minutes")
                    time.sleep(300)  # Wait 5 minutes before retry
                    continue
                
                # Wait for next cycle
                logger.info(f"💤 Waiting {self.publish_interval} minutes until next publish...")
                time.sleep(self.publish_interval * 60)
                
            except KeyboardInterrupt:
                logger.info("🛑 Smart Publisher stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in continuous run: {e}")
                time.sleep(60)  # Wait 1 minute before retry
    
    def run_once(self) -> bool:
        """Run one publish cycle and return success status."""
        return self.publish_cycle()
    
    def get_status(self) -> dict:
        """Get current status of the publisher."""
        unpublished_count = self.db.get_unpublished_articles_count()
        published_count = self.db.get_published_articles_count()
        
        status = {
            'unpublished_articles': unpublished_count,
            'published_articles': published_count,
            'total_articles': unpublished_count + published_count,
            'publish_interval_minutes': self.publish_interval,
            'last_publish_time': self.last_publish_time.isoformat() if self.last_publish_time else None,
            'next_publish_in_minutes': None
        }
        
        if self.last_publish_time:
            time_since_last = datetime.now() - self.last_publish_time
            time_until_next = (self.publish_interval * 60) - time_since_last.total_seconds()
            status['next_publish_in_minutes'] = max(0, time_until_next / 60)
        
        return status

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Smart Publisher for Robotics Radar")
    parser.add_argument("--once", action="store_true", help="Run one publish cycle and exit")
    parser.add_argument("--interval", type=int, default=30, help="Publish interval in minutes (default: 30)")
    parser.add_argument("--status", action="store_true", help="Show status and exit")
    
    args = parser.parse_args()
    
    publisher = SmartPublisher()
    publisher.publish_interval = args.interval
    
    if args.status:
        status = publisher.get_status()
        print("📊 Smart Publisher Status:")
        print(f"   Unpublished articles: {status['unpublished_articles']}")
        print(f"   Published articles: {status['published_articles']}")
        print(f"   Total articles: {status['total_articles']}")
        print(f"   Publish interval: {status['publish_interval_minutes']} minutes")
        print(f"   Last publish: {status['last_publish_time']}")
        if status['next_publish_in_minutes'] is not None:
            print(f"   Next publish in: {status['next_publish_in_minutes']:.1f} minutes")
        return
    
    if args.once:
        print("🔄 Running one publish cycle...")
        success = publisher.run_once()
        if success:
            print("✅ Publish cycle completed successfully")
        else:
            print("❌ Publish cycle failed")
            sys.exit(1)
    else:
        publisher.run_continuous()

if __name__ == "__main__":
    main() 