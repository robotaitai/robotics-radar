"""
Telegram bot notification module for Robotics Radar.
Sends notifications and handles user feedback via Telegram bot.
"""

import logging
import os
from typing import List, Dict, Optional
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    ContextTypes, MessageHandler, filters
)
import asyncio

from storage.database import DatabaseManager, Article
from feedback.feedback_processor import FeedbackProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Telegram bot for sending notifications and handling feedback."""
    
    def __init__(self):
        """Initialize Telegram notifier."""
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.allowed_users = self._get_allowed_users()
        self.db = DatabaseManager()
        self.feedback_processor = FeedbackProcessor()
        self.application = None
        
    def _get_allowed_users(self) -> List[str]:
        """Get list of allowed user IDs from environment.
        
        Returns:
            List of allowed user IDs
        """
        allowed_users_str = os.getenv('TELEGRAM_ALLOWED_USERS', '')
        if allowed_users_str:
            return [user_id.strip() for user_id in allowed_users_str.split(',')]
        return []
    
    def is_available(self) -> bool:
        """Check if Telegram bot is available.
        
        Returns:
            True if bot token is configured
        """
        return bool(self.bot_token)
    
    async def start_bot(self):
        """Start the Telegram bot."""
        if not self.bot_token:
            logger.error("Telegram bot token not configured")
            return
        
        try:
            # Create application
            self.application = Application.builder().token(self.bot_token).build()
            
            # Add handlers
            self.application.add_handler(CommandHandler("start", self._start_command))
            self.application.add_handler(CommandHandler("help", self._help_command))
            self.application.add_handler(CommandHandler("stats", self._stats_command))
            self.application.add_handler(CommandHandler("top", self._top_command))
            self.application.add_handler(CallbackQueryHandler(self._button_callback))
            
            # Start the bot
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            logger.info("Telegram bot started successfully")
            
        except Exception as e:
            logger.error(f"Error starting Telegram bot: {e}")
    
    async def stop_bot(self):
        """Stop the Telegram bot."""
        if self.application:
            try:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                logger.info("Telegram bot stopped")
            except Exception as e:
                logger.error(f"Error stopping Telegram bot: {e}")
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        if not self._is_user_allowed(update.effective_user.id):
            await update.message.reply_text("Sorry, you are not authorized to use this bot.")
            return
        
        welcome_message = """
🤖 Welcome to Robotics Radar Bot!

I'll keep you updated with the latest robotics-related tweets from X (Twitter).

Commands:
/start - Show this welcome message
/help - Show help information
/stats - Show current statistics
/top - Show top tweets

You'll receive notifications every 2 hours with the best robotics content!
        """
        
        await update.message.reply_text(welcome_message)
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        if not self._is_user_allowed(update.effective_user.id):
            return
        
        help_message = """
📚 Robotics Radar Bot Help

Commands:
• /start - Welcome message
• /help - This help message
• /stats - Show analytics statistics
• /top - Show current top tweets

Features:
• Automatic tweet fetching every 2 hours
• Smart filtering for robotics content
• Interactive feedback (👍/👎) on tweets
• Daily analytics reports

The bot will automatically send you notifications with the best robotics tweets!
        """
        
        await update.message.reply_text(help_message)
    
    async def _stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command."""
        if not self._is_user_allowed(update.effective_user.id):
            return
        
        try:
            analytics = self.db.get_analytics_summary()
            
            stats_message = f"""
📊 Robotics Radar Statistics

📈 Total Tweets: {analytics['total_tweets']:,}
👥 Total Authors: {analytics['total_authors']:,}
⭐ Average Score: {analytics['avg_score']:.2f}
💬 Total Feedback: {analytics['total_feedback']:,}
🕐 Recent Tweets (24h): {analytics['recent_tweets']:,}

Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            await update.message.reply_text(stats_message)
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            await update.message.reply_text("Sorry, couldn't retrieve statistics at the moment.")
    
    async def _top_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /top command."""
        if not self._is_user_allowed(update.effective_user.id):
            return
        
        try:
            top_tweets = self.db.get_top_tweets(limit=5)
            
            if not top_tweets:
                await update.message.reply_text("No tweets available at the moment.")
                return
            
            message = "🔥 Top Robotics Tweets:\n\n"
            
            for i, tweet in enumerate(top_tweets, 1):
                # message += f"{i}. @{tweet.author_username}\n"
                # message += f"   {tweet.text[:100]}...\n"
                message += f"   Score: {tweet.score:.2f} | ❤️ {tweet.likes} | 🔄 {tweet.retweets}\n\n"
            
            await update.message.reply_text(message)
            
        except Exception as e:
            logger.error(f"Error getting top tweets: {e}")
            await update.message.reply_text("Sorry, couldn't retrieve top tweets at the moment.")
    
    async def _button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks for feedback."""
        if not self._is_user_allowed(update.effective_user.id):
            return
        
        query = update.callback_query
        await query.answer()
        
        try:
            # Parse callback data: "feedback:tweet_id:rating"
            data = query.data.split(':')
            if len(data) == 3 and data[0] == 'feedback':
                tweet_id = data[1]
                rating = int(data[2])  # Convert rating to integer (1-5)
                
                # Process feedback
                user_id = str(update.effective_user.id)
                success = self.feedback_processor.process_feedback(
                    tweet_id=tweet_id,
                    user_id=user_id,
                    feedback_type=f"rating_{rating}"  # Store as rating_1, rating_2, etc.
                )
                
                if success:
                    # Update button text to show rating
                    stars = "⭐" * rating
                    new_text = f"{stars} Rated {rating}/5 by you!"
                    await query.edit_message_text(
                        text=query.message.text + f"\n\n{new_text}",
                        reply_markup=None
                    )
                else:
                    await query.answer("Error processing feedback", show_alert=True)
            
        except Exception as e:
            logger.error(f"Error handling button callback: {e}")
            await query.answer("Error processing feedback", show_alert=True)
    
    def _is_user_allowed(self, user_id: int) -> bool:
        """Check if user is allowed to use the bot.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if user is allowed
        """
        if not self.allowed_users:
            return True  # Allow all users if no restrictions set
        return str(user_id) in self.allowed_users
    
    def _clean_html_text(self, text: str) -> str:
        """Clean HTML tags from text.
        
        Args:
            text: Text containing HTML tags
            
        Returns:
            Cleaned text without HTML tags
        """
        if not text:
            return ""
        
        import re
        
        # First, remove all HTML tags completely
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        # Remove any remaining HTML entities
        clean_text = re.sub(r'&[a-zA-Z0-9#]+;', '', clean_text)
        
        # Remove image alt text patterns that might have survived
        clean_text = re.sub(r'img alt="[^"]*"', '', clean_text)
        clean_text = re.sub(r'alt="[^"]*"', '', clean_text)
        
        # Remove common metadata patterns
        clean_text = re.sub(r'Source:\s*[^.]*\.', '', clean_text)
        clean_text = re.sub(r'Credit:\s*[^.]*\.', '', clean_text)
        clean_text = re.sub(r'Image:\s*[^.]*\.', '', clean_text)
        clean_text = re.sub(r'<img[^>]*>', '', clean_text)
        
        # Remove specific patterns that are still appearing
        clean_text = re.sub(r'<img[^>]*alt="[^"]*"[^>]*>', '', clean_text)
        clean_text = re.sub(r'<img[^>]*class="[^"]*"[^>]*>', '', clean_text)
        clean_text = re.sub(r'<img[^>]*src="[^"]*"[^>]*>', '', clean_text)
        clean_text = re.sub(r'<img[^>]*width="[^"]*"[^>]*>', '', clean_text)
        clean_text = re.sub(r'<img[^>]*height="[^"]*"[^>]*>', '', clean_text)
        
        # Remove any remaining HTML-like patterns
        clean_text = re.sub(r'<[^>]*>', '', clean_text)
        
        # Remove extra whitespace and newlines
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        # Remove special characters that might break Markdown
        clean_text = clean_text.replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace(']', '\\]')
        
        # Final cleanup - remove any remaining HTML-like patterns
        clean_text = re.sub(r'<[^>]*>', '', clean_text)
        
        return clean_text.strip()
    
    async def send_top_articles(self, articles: List[Article]):
        """Send top articles notification.
        
        Args:
            articles: List of top articles to send
        """
        if not self.application or not articles:
            return
        
        try:
            message = "🤖 *Robotics Radar Update*\n\n"
            message += f"Here are the top {len(articles)} robotics articles:\n\n"
            
            for i, article in enumerate(articles, 1):
                # Truncate text if too long
                text = article.text[:150] + "..." if len(article.text) > 150 else article.text
                
                message += f"{i}. *@{article.author_username}*\n"
                message += f"   {text}\n"
                message += f"   📝 *Summary:* {article.summary or 'No summary available'}\n"
                message += f"   Score: {article.score:.2f} | ❤️ {article.likes} | 🔄 {article.retweets}\n"
                message += f"   [Read Article]({article.url})\n\n"
            
            # Send to all allowed users
            for user_id in self.allowed_users:
                try:
                    # Create inline keyboard for feedback
                    keyboard = []
                    for article in articles:
                        row = []
                        for rating in range(1, 6):
                            stars = "⭐" * rating
                            row.append(InlineKeyboardButton(
                                f"{stars} {article.id[:8]}", 
                                callback_data=f"feedback:{article.id}:{rating}"
                            ))
                        keyboard.append(row)
                    
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await self.application.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode='Markdown',
                        disable_web_page_preview=True,
                        reply_markup=reply_markup
                    )
                    
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
            
            logger.info(f"Sent top articles notification to {len(self.allowed_users)} users")
            
        except Exception as e:
            logger.error(f"Error sending top articles notification: {e}")
    
    async def send_analytics_report(self, stats: Dict):
        """Send analytics report.
        
        Args:
            stats: Analytics statistics
        """
        if not self.application:
            return
        
        try:
            message = "📊 *Daily Robotics Radar Report*\n\n"
            message += f"📈 Total Articles: {stats.get('total_articles', 0):,}\n"
            message += f"👥 Total Authors: {stats.get('total_authors', 0):,}\n"
            message += f"⭐ Average Score: {stats.get('avg_score', 0):.2f}\n"
            message += f"🕐 Recent Articles (24h): {stats.get('recent_articles', 0):,}\n\n"
            
            # Add top authors
            top_authors = stats.get('top_authors', [])
            if top_authors:
                message += "🏆 *Top Authors:*\n"
                for i, author in enumerate(top_authors[:3], 1):
                    message += f"{i}. @{author['username']} ({author['followers_count']:,} followers)\n"
                message += "\n"
            
            # Add trending topics
            trending_topics = stats.get('trending_topics', [])
            if trending_topics:
                message += "🔥 *Trending Topics:*\n"
                for i, topic in enumerate(trending_topics[:5], 1):
                    message += f"{i}. {topic['name']} ({topic['frequency']} mentions)\n"
            
            # Send to all allowed users
            for user_id in self.allowed_users:
                try:
                    await self.application.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Error sending analytics to user {user_id}: {e}")
            
            logger.info(f"Sent analytics report to {len(self.allowed_users)} users")
            
        except Exception as e:
            logger.error(f"Error sending analytics report: {e}")
    
    def send_top_articles_sync(self, articles: List[Article]):
        """Synchronous wrapper for sending top articles."""
        if not articles:
            return
        
        try:
            # Use direct Bot API instead of Application to avoid event loop issues
            from telegram import Bot
            bot = Bot(token=self.bot_token)
            
            # Import ArticleReader for enhanced summaries
            from agent_integration.article_reader import ArticleReader
            article_reader = ArticleReader()
            
            message = "🤖 *Robotics Radar Update*\n\n"
            message += f"Here are the top {len(articles)} robotics articles:\n\n"
            
            for i, article in enumerate(articles, 1):
                # Clean up the text by removing HTML tags and truncating properly
                clean_text = self._clean_html_text(article.text)
                title = clean_text.split('\n')[0] if clean_text else "No title"
                title = title[:150] + "..." if len(title) > 150 else title
                
                # Use ArticleReader to enhance summary if available
                enhanced_summary = article.summary
                try:
                    if article.url and article.url.startswith('http'):
                        # Try to get enhanced summary from ArticleReader
                        article_content = article_reader.read_article(article.url)
                        if article_content and article_content.get('summary'):
                            enhanced_summary = article_content['summary']
                except Exception as e:
                    logger.debug(f"Could not enhance summary for {article.url}: {e}")
                
                # Clean up summary and make it longer
                clean_summary = self._clean_html_text(enhanced_summary or "No summary available")
                clean_summary = clean_summary[:300] + "..." if len(clean_summary) > 300 else clean_summary
                
                message += f"*{i}. {clean_summary}*\n"
                message += f"⭐ Score: {article.score:.1f}\n"
                message += f"🔗 [Read Article]({article.url})\n\n"
            
            # Create 1-5 star rating buttons
            keyboard = []
            for article in articles:
                row = []
                for rating in range(1, 6):
                    stars = "⭐" * rating
                    row.append(InlineKeyboardButton(
                        f"{stars} {article.id[:8]}", 
                        callback_data=f"feedback:{article.id}:{rating}"
                    ))
                keyboard.append(row)
            
            reply_markup = InlineKeyboardMarkup(keyboard)
                    
            # Send to all allowed users
            for user_id in self.allowed_users:
                try:
                    import asyncio
                    asyncio.run(bot.send_message(
                        chat_id=user_id, text=message, parse_mode='Markdown',
                        disable_web_page_preview=True, reply_markup=reply_markup
                    ))
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
            logger.info(f"Sent top articles notification to {len(self.allowed_users)} users")
            
        except Exception as e:
            logger.error(f"Error in sync send_top_articles: {e}")
    
    def send_analytics_report_sync(self, stats: Dict):
        """Synchronous wrapper for sending analytics report."""
        if not self.application:
            return
        
        try:
            asyncio.run(self.send_analytics_report(stats))
        except Exception as e:
            logger.error(f"Error in sync send_analytics_report: {e}")


def main():
    """Main function to run the Telegram bot."""
    try:
        notifier = TelegramNotifier()
        
        if not notifier.is_available():
            logger.error("Telegram bot token not configured")
            return
        
        # Run the bot
        asyncio.run(notifier.start_bot())
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    main() 