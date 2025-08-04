"""
Telegram bot notification module for Robotics Radar.
Sends notifications and handles user feedback via Telegram bot.
"""

import logging
import os
from typing import List, Dict, Optional
import sys
from datetime import datetime
import time # Added for time.sleep in send_top_articles_sync

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
            top_articles = self.db.get_top_articles(limit=5)
            
            if not top_articles:
                await update.message.reply_text("No articles available at the moment.")
                return
            
            message = "🤖 *Top Robotics Articles:*\n\n"
            
            for i, article in enumerate(top_articles, 1):
                # Generate enhanced summary
                enhanced_summary = self._generate_enhanced_summary(article)
                clean_summary = enhanced_summary.replace('\n\n', '\n').strip()
                
                message += f"**{i}.** {clean_summary}\n"
                message += f"   📊 Score: {article.score:.1f} | 👍 {article.likes} | 🔄 {article.retweets}\n"
                message += f"   🔗 [Read Article]({article.url})\n\n"
            
            await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)
            
        except Exception as e:
            logger.error(f"Error getting top articles: {e}")
            await update.message.reply_text("Sorry, couldn't retrieve top articles at the moment.")
    
    async def _button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks."""
        query = update.callback_query
        await query.answer()
        
        try:
            data = query.data
            
            # Handle approval/rejection workflow
            if data.startswith('approve_'):
                await self._handle_approve_article(query, data)
            elif data.startswith('reject_'):
                await self._handle_reject_article(query, data)
            elif data.startswith('edit_'):
                await self._handle_edit_article(query, data)
            elif data.startswith('skip_'):
                await self._handle_skip_article(query, data)
            # Handle legacy feedback system
            elif data.startswith('feedback:'):
                await self._handle_feedback(query, data)
            else:
                await query.edit_message_text("Unknown action")
                
        except Exception as e:
            logger.error(f"Error handling button callback: {e}")
            await query.edit_message_text("Error processing action")
    
    async def _handle_approve_article(self, query, data):
        """Handle article approval."""
        try:
            article_id = data.replace('approve_', '')
            
            # Get article from database
            article = self.db.get_article_by_id(article_id)
            if not article:
                await query.edit_message_text("❌ Article not found in database")
                return
            
            # Format approved message for main channel
            approved_message = self._format_approved_message(article)
            
            # Update the review message
            await query.edit_message_text(
                f"✅ **APPROVED**\n\n{approved_message}",
                parse_mode='Markdown'
            )
            
            # TODO: Send to main channel (you can implement this based on your channel setup)
            logger.info(f"Article {article_id} approved for publishing")
            
            # Store approval in database
            self.db.add_feedback(article_id, "approved", 5, "human_approval")
            
        except Exception as e:
            logger.error(f"Error approving article: {e}")
            await query.edit_message_text("❌ Error approving article")
    
    async def _handle_reject_article(self, query, data):
        """Handle article rejection."""
        try:
            article_id = data.replace('reject_', '')
            
            # Update the review message
            await query.edit_message_text(
                "❌ **REJECTED**\n\nArticle has been rejected and will not be published.",
                parse_mode='Markdown'
            )
            
            # Store rejection in database
            self.db.add_feedback(article_id, "rejected", 1, "human_rejection")
            
            logger.info(f"Article {article_id} rejected")
            
        except Exception as e:
            logger.error(f"Error rejecting article: {e}")
            await query.edit_message_text("❌ Error rejecting article")
    
    async def _handle_edit_article(self, query, data):
        """Handle article edit request."""
        try:
            article_id = data.replace('edit_', '')
            
            # For now, just mark as needing edit
            await query.edit_message_text(
                "✏️ **EDIT MODE**\n\nPlease edit the message above and then approve manually.",
                parse_mode='Markdown'
            )
            
            logger.info(f"Article {article_id} marked for editing")
            
        except Exception as e:
            logger.error(f"Error handling edit request: {e}")
            await query.edit_message_text("❌ Error handling edit request")
    
    async def _handle_skip_article(self, query, data):
        """Handle article skip."""
        try:
            article_id = data.replace('skip_', '')
            
            # Update the review message
            await query.edit_message_text(
                "⏭️ **SKIPPED**\n\nArticle has been skipped for now.",
                parse_mode='Markdown'
            )
            
            logger.info(f"Article {article_id} skipped")
            
        except Exception as e:
            logger.error(f"Error skipping article: {e}")
            await query.edit_message_text("❌ Error skipping article")
    
    def _format_approved_message(self, article: Article) -> str:
        """Format message for approved article (ready for main channel)."""
        try:
            # Generate enhanced summary
            enhanced_summary = self._generate_enhanced_summary(article)
            
            # Format for main channel
            message_parts = [
                enhanced_summary,
                "",
                f"🔗 [Read Full Article]({article.url})",
                "",
                f"📊 Score: {article.score:.1f} | 👍 {article.likes} | 📅 {article.created_at.strftime('%Y-%m-%d')}"
            ]
            
            return "\n".join(message_parts)
            
        except Exception as e:
            logger.error(f"Error formatting approved message: {e}")
            return f"📰 {article.text[:200]}...\n\n🔗 [Read Full Article]({article.url})"
    
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
        """Send top articles notification with enhanced summaries.
        
        Args:
            articles: List of top articles to send
        """
        if not self.application or not articles:
            return
        
        try:
            message = "🤖 *Robotics Radar - Enhanced Summary*\n\n"
            
            for i, article in enumerate(articles, 1):
                # Generate enhanced summary
                enhanced_summary = self._generate_enhanced_summary(article)
                
                # Clean up the summary for display
                clean_summary = enhanced_summary.replace('\n\n', '\n').strip()
                
                message += f"**{i}.** {clean_summary}\n"
                message += f"   📊 Score: {article.score:.1f} | 👍 {article.likes} | 🔄 {article.retweets}\n"
                message += f"   🔗 [Read Article]({article.url})\n\n"
            
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
    
    def send_top_articles_sync(self, articles: List[Article], max_articles: int = 10) -> bool:
        """Send top articles to Telegram with human-in-the-loop review.
        
        Args:
            articles: List of Article objects
            max_articles: Maximum number of articles to send
            
        Returns:
            True if sent successfully
        """
        if not articles:
            logger.warning("No articles to send")
            return False
        
        try:
            # Initialize bot for synchronous operations
            from telegram import Bot
            import asyncio
            
            async def send_messages():
                bot = Bot(token=self.bot_token)
                
                # Get top articles
                top_articles = articles[:max_articles]
                
                logger.info(f"Sending {len(top_articles)} articles for review")
                
                for i, article in enumerate(top_articles, 1):
                    # Generate enhanced summary with insights
                    enhanced_summary = self._generate_enhanced_summary(article)
                    
                    # Create review message with approval buttons
                    message_text = self._format_review_message(i, article, enhanced_summary)
                    
                    # Create inline keyboard for approval/rejection
                    keyboard = [
                        [
                            InlineKeyboardButton("✅ Approve & Publish", callback_data=f"approve_{article.id}"),
                            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{article.id}")
                        ],
                        [
                            InlineKeyboardButton("✏️ Edit & Approve", callback_data=f"edit_{article.id}"),
                            InlineKeyboardButton("⏭️ Skip", callback_data=f"skip_{article.id}")
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    # Send to review channel/chat
                    for user_id in self.allowed_users:
                        try:
                            await bot.send_message(
                                chat_id=user_id,
                                text=message_text,
                                parse_mode='Markdown',
                                reply_markup=reply_markup,
                                disable_web_page_preview=False
                            )
                            logger.info(f"Sent review message for article {article.id} to user {user_id}")
                            
                            # Small delay between messages
                            await asyncio.sleep(1)
                            
                        except Exception as e:
                            logger.error(f"Error sending review message to user {user_id}: {e}")
                            continue
            
            # Run the async function
            asyncio.run(send_messages())
            return True
            
        except Exception as e:
            logger.error(f"Error in send_top_articles_sync: {e}")
            return False
    
    def _generate_enhanced_summary(self, article: Article) -> str:
        """Generate enhanced summary using the enhanced ArticleReader.
        
        Args:
            article: Article object
            
        Returns:
            Enhanced summary text
        """
        try:
            # Use the enhanced ArticleReader for intelligent analysis
            from agent_integration.article_reader import ArticleReader
            article_reader = ArticleReader()
            
            # Try to get enhanced summary from ArticleReader
            if article.url and article.url.startswith('http'):
                try:
                    article_data = article_reader.read_article(article.url)
                    if article_data and article_data.get('summary'):
                        # Use the enhanced summary from ArticleReader
                        enhanced_summary = article_data['summary']
                        
                        # Add insights if available
                        insights = article_data.get('insights', [])
                        if insights:
                            enhanced_summary += "\n\n**Key Insights:**"
                            for insight in insights[:2]:  # Limit to 2 insights
                                enhanced_summary += f"\n• {insight[:100]}..."
                        
                        # Add source information
                        enhanced_summary += f"\n\n*Source: {article.author_name}*"
                        
                        return enhanced_summary
                        
                except Exception as e:
                    logger.debug(f"Could not use enhanced ArticleReader for {article.url}: {e}")
            
            # Fallback to enhanced basic summary
            return self._generate_enhanced_basic_summary(article)
            
        except Exception as e:
            logger.error(f"Error generating enhanced summary: {e}")
            return self._generate_enhanced_basic_summary(article)
    
    def _generate_enhanced_basic_summary(self, article: Article) -> str:
        """Generate enhanced basic summary with more detail and explanation."""
        try:
            # Clean title
            clean_title = self._clean_html_text(article.text)
            title = clean_title.split('\n')[0] if clean_title else article.text
            
            # Determine category and emoji
            category_info = self._determine_category(title, article.author_name)
            
            # Generate detailed summary
            summary_parts = []
            
            # Add category header
            summary_parts.append(f"{category_info['emoji']} **{category_info['category']}**")
            
            # Add title
            summary_parts.append(f"**{title[:120]}{'...' if len(title) > 120 else ''}**")
            
            # Add detailed explanation based on category
            explanation = self._generate_detailed_explanation(title, category_info['type'])
            if explanation:
                summary_parts.append(f"\n{explanation}")
            
            # Add technical context
            technical_context = self._extract_technical_context(title)
            if technical_context:
                summary_parts.append(f"\n**Technical Context:** {technical_context}")
            
            # Add impact assessment
            impact = self._assess_impact(article.score, article.likes)
            if impact:
                summary_parts.append(f"\n**Impact Assessment:** {impact}")
            
            # Add source with credibility
            source_info = self._format_source_info(article.author_name)
            summary_parts.append(f"\n{source_info}")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error generating enhanced basic summary: {e}")
            return f"📰 **Robotics News**\n**{article.text[:100]}...**\n*Source: {article.author_name}*"
    
    def _determine_category(self, title: str, author: str) -> dict:
        """Determine the category and type of the article."""
        title_lower = title.lower()
        author_lower = author.lower()
        
        # Research and academic content
        if any(word in title_lower for word in ['research', 'study', 'paper', 'thesis', 'dissertation']):
            return {
                'emoji': '🔬',
                'category': 'Research Publication',
                'type': 'research'
            }
        elif any(word in title_lower for word in ['arxiv', 'conference', 'journal', 'proceedings']):
            return {
                'emoji': '📚',
                'category': 'Academic Research',
                'type': 'academic'
            }
        
        # Breakthrough and innovation
        elif any(word in title_lower for word in ['breakthrough', 'revolutionary', 'groundbreaking', 'novel', 'first']):
            return {
                'emoji': '🚀',
                'category': 'Breakthrough Innovation',
                'type': 'breakthrough'
            }
        
        # Product launches and announcements
        elif any(word in title_lower for word in ['launch', 'announcement', 'release', 'unveil', 'introduce']):
            return {
                'emoji': '📢',
                'category': 'Product Launch',
                'type': 'launch'
            }
        
        # Funding and business
        elif any(word in title_lower for word in ['funding', 'investment', 'raise', 'series', 'venture', 'startup']):
            return {
                'emoji': '💰',
                'category': 'Business & Funding',
                'type': 'business'
            }
        
        # Performance improvements
        elif any(word in title_lower for word in ['improve', 'better', 'faster', 'enhance', 'optimize', 'upgrade']):
            return {
                'emoji': '⚡',
                'category': 'Performance Enhancement',
                'type': 'improvement'
            }
        
        # Industry applications
        elif any(word in title_lower for word in ['industrial', 'manufacturing', 'production', 'deployment', 'commercial']):
            return {
                'emoji': '🏭',
                'category': 'Industrial Application',
                'type': 'industrial'
            }
        
        # Open source and tools
        elif any(word in title_lower for word in ['open source', 'github', 'library', 'framework', 'toolkit']):
            return {
                'emoji': '🔧',
                'category': 'Open Source Tool',
                'type': 'opensource'
            }
        
        # Default
        else:
            return {
                'emoji': '📰',
                'category': 'Robotics News',
                'type': 'general'
            }
    
    def _generate_detailed_explanation(self, title: str, category_type: str) -> str:
        """Generate detailed explanation based on category type."""
        title_lower = title.lower()
        
        if category_type == 'research':
            return "This research publication presents new findings in robotics and AI, contributing to the scientific understanding of autonomous systems and machine learning applications."
        
        elif category_type == 'academic':
            return "This academic work advances the theoretical foundations of robotics, providing new insights into algorithms, methodologies, or computational approaches."
        
        elif category_type == 'breakthrough':
            return "This breakthrough represents a significant advancement in robotics technology, potentially transforming how we approach automation and intelligent systems."
        
        elif category_type == 'launch':
            return "This product launch introduces new robotics technology to the market, offering practical solutions for real-world automation challenges."
        
        elif category_type == 'business':
            return "This business development reflects growing investment in robotics technology, indicating strong market confidence in the future of automation."
        
        elif category_type == 'improvement':
            return "This enhancement improves existing robotics capabilities, making systems more efficient, accurate, or reliable for practical applications."
        
        elif category_type == 'industrial':
            return "This industrial application demonstrates how robotics technology is being deployed in manufacturing and production environments."
        
        elif category_type == 'opensource':
            return "This open-source contribution provides valuable tools and frameworks for the robotics community, enabling faster development and innovation."
        
        else:
            # Generate context based on keywords
            if 'robot' in title_lower:
                return "This robotics development advances the field of autonomous systems and automation technology."
            elif 'ai' in title_lower or 'artificial intelligence' in title_lower:
                return "This AI advancement contributes to the development of intelligent systems and machine learning applications."
            elif 'autonomous' in title_lower:
                return "This autonomous system development pushes the boundaries of self-driving and independent operation capabilities."
            else:
                return "This development contributes to the advancement of robotics and automation technology."
    
    def _extract_technical_context(self, title: str) -> str:
        """Extract technical context from the title."""
        title_lower = title.lower()
        
        contexts = []
        
        if any(word in title_lower for word in ['machine learning', 'ml', 'neural network', 'deep learning']):
            contexts.append("Machine Learning")
        
        if any(word in title_lower for word in ['computer vision', 'vision', 'image processing']):
            contexts.append("Computer Vision")
        
        if any(word in title_lower for word in ['autonomous', 'self-driving', 'navigation']):
            contexts.append("Autonomous Navigation")
        
        if any(word in title_lower for word in ['manipulation', 'grasping', 'control']):
            contexts.append("Robotic Manipulation")
        
        if any(word in title_lower for word in ['sensor', 'perception', 'detection']):
            contexts.append("Sensor Technology")
        
        if any(word in title_lower for word in ['simulation', 'virtual', 'digital twin']):
            contexts.append("Simulation & Digital Twins")
        
        if contexts:
            return ", ".join(contexts[:3])  # Limit to 3 contexts
        
        return "Robotics & Automation"
    
    def _assess_impact(self, score: float, likes: int) -> str:
        """Assess the potential impact of the article."""
        if score > 800:
            return "🔥 **High Impact** - This represents a significant advancement with broad implications for the robotics industry."
        elif score > 500:
            return "⭐ **Notable Impact** - This development shows promising potential for practical applications."
        elif score > 200:
            return "📈 **Emerging Impact** - This contributes to the growing field of robotics technology."
        else:
            return "📊 **Developing Impact** - This adds to the expanding robotics ecosystem."
    
    def _format_source_info(self, author: str) -> str:
        """Format source information with credibility assessment."""
        author_lower = author.lower()
        
        if any(word in author_lower for word in ['university', 'institute', 'research', 'lab']):
            return f"*Source: {author}* (Academic/Research Institution)"
        elif any(word in author_lower for word in ['company', 'corp', 'inc', 'ltd', 'tech']):
            return f"*Source: {author}* (Industry Leader)"
        elif any(word in author_lower for word in ['report', 'news', 'media']):
            return f"*Source: {author}* (Industry Publication)"
        else:
            return f"*Source: {author}*"
    
    def _extract_key_insights(self, article: Article) -> List[str]:
        """Extract key insights from article content.
        
        Args:
            article: Article object
            
        Returns:
            List of key insights
        """
        insights = []
        
        try:
            content = article.text.lower()
            
            # Look for breakthrough indicators
            if any(word in content for word in ['breakthrough', 'novel', 'first', 'revolutionary']):
                insights.append("Presents a breakthrough or novel approach")
            
            # Look for performance indicators
            if any(word in content for word in ['improved', 'better', 'faster', 'more accurate']):
                insights.append("Shows significant performance improvements")
            
            # Look for application indicators
            if any(word in content for word in ['industrial', 'commercial', 'real-world', 'deployment']):
                insights.append("Has real-world applications")
            
            # Look for research indicators
            if any(word in content for word in ['research', 'study', 'experiment', 'validation']):
                insights.append("Includes research validation")
            
            # Look for technology indicators
            if any(word in content for word in ['ai', 'machine learning', 'computer vision', 'autonomous']):
                insights.append("Involves advanced AI/ML technology")
            
            # Add engagement context
            if article.likes > 1000:
                insights.append("High community engagement")
            elif article.likes > 100:
                insights.append("Good community interest")
            
        except Exception as e:
            logger.error(f"Error extracting insights: {e}")
        
        return insights
    
    def _format_review_message(self, index: int, article: Article, enhanced_summary: str) -> str:
        """Format message for human review.
        
        Args:
            index: Article index
            article: Article object
            enhanced_summary: Enhanced summary text
            
        Returns:
            Formatted message text
        """
        message_parts = [
            f"🤖 **Article #{index} - Review Required**",
            "",
            enhanced_summary,
            "",
            f"🔗 [Read Full Article]({article.url})",
            "",
            f"📊 Score: {article.score:.1f} | 👍 {article.likes} | 📅 {article.created_at.strftime('%Y-%m-%d')}",
            "",
            "**Please review and choose an action:**"
        ]
        
        return "\n".join(message_parts)
    
    async def _handle_feedback(self, query, data):
        """Handle legacy feedback system."""
        try:
            # Parse callback data: "feedback:tweet_id:rating"
            parts = data.split(':')
            if len(parts) == 3 and parts[0] == 'feedback':
                tweet_id = parts[1]
                rating = int(parts[2])  # Convert rating to integer (1-5)
                
                # Process feedback
                user_id = str(query.from_user.id)
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
            else:
                await query.answer("Invalid feedback format", show_alert=True)
                
        except Exception as e:
            logger.error(f"Error handling feedback: {e}")
            await query.answer("Error processing feedback", show_alert=True)
    
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