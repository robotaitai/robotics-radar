"""
Scheduler module for Robotics Radar.
Runs the tweet fetching pipeline on a schedule using APScheduler.
"""

import logging
import os
import sys
from datetime import datetime
from typing import Dict, Optional
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from dotenv import load_dotenv

from scraper.multi_source_scraper import MultiSourceScraper
from notifier.telegram_bot import TelegramNotifier
from notifier.email_sender import EmailNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RadarScheduler:
    """Scheduler for Robotics Radar pipeline."""
    
    def __init__(self):
        """Initialize the scheduler."""
        # Load environment variables
        load_dotenv()
        
        self.scheduler = BlockingScheduler()
        self.fetcher = MultiSourceScraper()
        self.telegram_notifier = TelegramNotifier()
        self.email_notifier = EmailNotifier()
        self.setup_event_listeners()
        
        # Initialize Telegram bot if available (but don't start polling yet)
        if self.telegram_notifier.is_available():
            logger.info("Telegram bot configured successfully")
        else:
            logger.warning("Telegram bot not available - check TELEGRAM_BOT_TOKEN")
    
    def setup_event_listeners(self):
        """Setup event listeners for job execution."""
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )
    
    def _job_executed_listener(self, event):
        """Handle job execution events.
        
        Args:
            event: Job execution event
        """
        if event.exception:
            logger.error(f"Job {event.job_id} failed: {event.exception}")
        else:
            logger.info(f"Job {event.job_id} completed successfully")
    
    def fetch_and_notify_job(self):
        """Main job that fetches articles from all sources and sends notifications."""
        try:
            logger.info("Starting scheduled multi-source fetch and notify job")
            
            # Run fetch cycle from all sources
            result = self.fetcher.fetch_all_sources()
            
            if result.get('error'):
                logger.error(f"Fetch cycle failed: {result['error']}")
                return
            
            # Send notifications if we have top articles
            if result['top_articles']:
                self._send_notifications(result['top_articles'])
            
            logger.info(f"Fetch and notify job completed: {result['total_stored']} articles stored")
            
        except Exception as e:
            logger.error(f"Error in fetch and notify job: {e}")
    
    def _send_notifications(self, top_articles):
        """Send notifications for top articles.
        
        Args:
            top_articles: List of top articles to notify about
        """
        try:
            # Send Telegram notification
            if self.telegram_notifier.is_available():
                logger.info("Sending Telegram notification...")
                self.telegram_notifier.send_top_articles_sync(top_articles)
                logger.info("Telegram notification sent successfully")
            
            # Send email notification
            if self.email_notifier.is_available():
                logger.info("Sending email notification...")
                self.email_notifier.send_top_articles(top_articles)
                logger.info("Email notification sent successfully")
                
        except Exception as e:
            logger.error(f"Error sending notifications: {e}")
    
    def add_fetch_job(self, interval_minutes: int = None):
        """Add the main fetch job to the scheduler.
        
        Args:
            interval_minutes: Interval between fetch jobs in minutes (overrides env)
        """
        try:
            # Get interval from environment variable if not provided
            if interval_minutes is None:
                # Try FETCH_INTERVAL_SECONDS first, then FETCH_INTERVAL_HOURS
                fetch_interval_seconds = os.getenv('FETCH_INTERVAL_SECONDS')
                if fetch_interval_seconds:
                    interval_seconds = int(fetch_interval_seconds)
                    logger.info(f"Using fetch interval from environment: {fetch_interval_seconds} seconds")
                    
                    # Use IntervalTrigger for sub-minute intervals, CronTrigger for minute+ intervals
                    if interval_seconds < 60:
                        from apscheduler.triggers.interval import IntervalTrigger
                        self.scheduler.add_job(
                            func=self.fetch_and_notify_job,
                            trigger=IntervalTrigger(seconds=interval_seconds),
                            id='fetch_and_notify',
                            name='Fetch articles and send notifications',
                            replace_existing=True,
                            max_instances=1
                        )
                    else:
                        interval_minutes = interval_seconds // 60
                        self.scheduler.add_job(
                            func=self.fetch_and_notify_job,
                            trigger=CronTrigger(minute=f"*/{interval_minutes}"),
                            id='fetch_and_notify',
                            name='Fetch articles and send notifications',
                            replace_existing=True,
                            max_instances=1
                        )
                else:
                    fetch_interval_hours = os.getenv('FETCH_INTERVAL_HOURS', '2')  # Default 2 hours
                    interval_minutes = int(fetch_interval_hours) * 60
                    logger.info(f"Using fetch interval from environment: {fetch_interval_hours} hours ({interval_minutes} minutes)")
                    
                    self.scheduler.add_job(
                        func=self.fetch_and_notify_job,
                        trigger=CronTrigger(minute=f"*/{interval_minutes}"),
                        id='fetch_and_notify',
                        name='Fetch articles and send notifications',
                        replace_existing=True,
                        max_instances=1
                    )
            else:
                # Use provided interval_minutes
                self.scheduler.add_job(
                    func=self.fetch_and_notify_job,
                    trigger=CronTrigger(minute=f"*/{interval_minutes}"),
                    id='fetch_and_notify',
                    name='Fetch articles and send notifications',
                    replace_existing=True,
                    max_instances=1
                )
            
            env_value = os.getenv('FETCH_INTERVAL_SECONDS') or f"{os.getenv('FETCH_INTERVAL_HOURS', '2')}h"
            logger.info(f"Added fetch job with {interval_minutes}-minute interval (from env: {env_value})")
            
        except Exception as e:
            logger.error(f"Error adding fetch job: {e}")
    
    def add_analytics_job(self, hour: int = 8):
        """Add daily analytics job.
        
        Args:
            hour: Hour of day to run analytics (0-23)
        """
        try:
            self.scheduler.add_job(
                func=self._daily_analytics_job,
                trigger=CronTrigger(hour=hour, minute=0),
                id='daily_analytics',
                name='Daily analytics report',
                replace_existing=True,
                max_instances=1
            )
            
            logger.info(f"Added daily analytics job at {hour}:00")
            
        except Exception as e:
            logger.error(f"Error adding analytics job: {e}")
    
    def _daily_analytics_job(self):
        """Daily analytics job."""
        try:
            logger.info("Starting daily analytics job")
            
            # Get fetch statistics
            stats = self.fetcher.get_fetch_stats()
            
            # Send analytics report
            if self.telegram_notifier.is_available():
                self.telegram_notifier.send_analytics_report(stats)
            
            if self.email_notifier.is_available():
                self.email_notifier.send_analytics_report(stats)
            
            logger.info("Daily analytics job completed")
            
        except Exception as e:
            logger.error(f"Error in daily analytics job: {e}")
    
    def add_cleanup_job(self, hour: int = 2):
        """Add daily cleanup job.
        
        Args:
            hour: Hour of day to run cleanup (0-23)
        """
        try:
            self.scheduler.add_job(
                func=self._cleanup_job,
                trigger=CronTrigger(hour=hour, minute=30),
                id='cleanup',
                name='Daily cleanup',
                replace_existing=True,
                max_instances=1
            )
            
            logger.info(f"Added cleanup job at {hour}:30")
            
        except Exception as e:
            logger.error(f"Error adding cleanup job: {e}")
    
    def _cleanup_job(self):
        """Daily cleanup job."""
        try:
            logger.info("Starting daily cleanup job")
            
            # Clean up old data (keep last 30 days)
            # This could include:
            # - Removing old tweets
            # - Archiving old data
            # - Optimizing database
            
            logger.info("Daily cleanup job completed")
            
        except Exception as e:
            logger.error(f"Error in cleanup job: {e}")
    
    def start(self):
        """Start the scheduler."""
        try:
            logger.info("Starting Robotics Radar scheduler")
            
            # Add jobs
            self.add_fetch_job()  # Use config setting
            self.add_analytics_job(hour=8)
            self.add_cleanup_job(hour=2)
            
            # Print job information
            self._print_job_info()
            
            # Start Telegram bot in polling mode if available
            if self.telegram_notifier.is_available():
                import threading
                import asyncio
                
                def run_bot():
                    """Run the bot in polling mode."""
                    try:
                        asyncio.run(self.telegram_notifier.start_bot())
                    except Exception as e:
                        logger.error(f"Error running Telegram bot: {e}")
                
                # Start bot in a separate thread
                bot_thread = threading.Thread(target=run_bot, daemon=True)
                bot_thread.start()
                logger.info("Telegram bot started in polling mode")
            
            # Start the scheduler
            self.scheduler.start()
            
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the scheduler."""
        try:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    def _print_job_info(self):
        """Print information about scheduled jobs."""
        logger.info("Scheduled jobs:")
        for job in self.scheduler.get_jobs():
            try:
                next_run = job.next_run_time
                logger.info(f"  - {job.name} (ID: {job.id}) - Next run: {next_run}")
            except AttributeError:
                logger.info(f"  - {job.name} (ID: {job.id}) - Next run: Unknown")
    
    def run_once(self):
        """Run the fetch job once immediately."""
        try:
            logger.info("Running fetch job once")
            self.fetch_and_notify_job()
        except Exception as e:
            logger.error(f"Error running fetch job once: {e}")


def main():
    """Main function to start the scheduler."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Check if required environment variables are set
        required_vars = [
            'TELEGRAM_BOT_TOKEN',
            'TELEGRAM_ALLOWED_USERS'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            logger.error("Please set the required environment variables before running the scheduler")
            return
        
        # Create scheduler and start
        scheduler = RadarScheduler()
        scheduler.start()
        
    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    main() 