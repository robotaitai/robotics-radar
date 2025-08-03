"""
Email notification module for Robotics Radar.
Sends notifications via SMTP email.
"""

import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.database import Article

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailNotifier:
    """Email notifier for sending top articles via SMTP."""
    
    def __init__(self):
        """Initialize email notifier."""
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.recipients = self._get_recipients()
        
    def _get_recipients(self) -> List[str]:
        """Get list of email recipients from environment.
        
        Returns:
            List of email addresses
        """
        recipients_str = os.getenv('EMAIL_RECIPIENTS', '')
        if recipients_str:
            return [email.strip() for email in recipients_str.split(',')]
        return []
    
    def is_available(self) -> bool:
        """Check if email notifier is available.
        
        Returns:
            True if SMTP credentials are configured
        """
        return all([
            self.smtp_server,
            self.smtp_username,
            self.smtp_password,
            self.recipients
        ])
    
    def _create_message(self, subject: str, html_content: str, text_content: str) -> MIMEMultipart:
        """Create email message.
        
        Args:
            subject: Email subject
            html_content: HTML version of email content
            text_content: Plain text version of email content
            
        Returns:
            MIME message object
        """
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = self.smtp_username
        message['To'] = ', '.join(self.recipients)
        
        # Add plain text and HTML parts
        text_part = MIMEText(text_content, 'plain')
        html_part = MIMEText(html_content, 'html')
        
        message.attach(text_part)
        message.attach(html_part)
        
        return message
    
    def _send_email(self, message: MIMEMultipart) -> bool:
        """Send email via SMTP.
        
        Args:
            message: MIME message object
            
        Returns:
            True if email sent successfully
        """
        try:
            # Connect to SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            
            # Login
            server.login(self.smtp_username, self.smtp_password)
            
            # Send email
            server.send_message(message)
            server.quit()
            
            logger.info(f"Email sent successfully to {len(self.recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def send_top_articles(self, articles: List[Article]) -> bool:
        """Send top articles notification via email.
        
        Args:
            articles: List of top articles to send
            
        Returns:
            True if email sent successfully
        """
        if not self.is_available() or not articles:
            return False
        
        try:
            subject = f"🤖 Robotics Radar - Top {len(articles)} Articles"
            
            # Create HTML content
            html_content = self._create_html_content(articles)
            
            # Create plain text content
            text_content = self._create_text_content(articles)
            
            # Create and send message
            message = self._create_message(subject, html_content, text_content)
            return self._send_email(message)
            
        except Exception as e:
            logger.error(f"Error creating top articles email: {e}")
            return False
    
    def _create_html_content(self, articles: List[Article]) -> str:
        """Create HTML content for email.
        
        Args:
            articles: List of articles
            
        Returns:
            HTML content string
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #1da1f2; color: white; padding: 20px; text-align: center; }}
                .tweet {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 8px; }}
                .author {{ font-weight: bold; color: #1da1f2; }}
                .score {{ color: #666; font-size: 0.9em; }}
                .metrics {{ color: #666; font-size: 0.9em; }}
                .link {{ color: #1da1f2; text-decoration: none; }}
                .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 Robotics Radar</h1>
                <p>Top {len(articles)} Robotics Articles</p>
            </div>
            
            <div style="padding: 20px;">
        """
        
        for i, article in enumerate(articles, 1):
            # Truncate text if too long
            text = article.text[:300] + "..." if len(article.text) > 300 else article.text
            
            html += f"""
                <div class="tweet">
                    <div class="author">#{i} {article.author_username}</div>
                    <div style="margin: 10px 0;">{text}</div>
                    <div class="metrics">
                        ❤️ {article.likes:,} | 🔄 {article.retweets:,} | 💬 {article.replies:,}
                    </div>
                    <div class="score">Score: {article.score:.2f}</div>
                    <div style="margin-top: 10px;">
                        <a href="{article.url}" class="link">Read Article</a>
                    </div>
                </div>
            """
        
        html += f"""
            </div>
            
            <div class="footer">
                <p>Robotics Radar - Automated robotics content curation</p>
                <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _create_text_content(self, articles: List[Article]) -> str:
        """Create plain text content for email.
        
        Args:
            articles: List of articles
            
        Returns:
            Plain text content string
        """
        text = f"🤖 Robotics Radar - Top {len(articles)} Articles\n"
        text += "=" * 50 + "\n\n"
        
        for i, article in enumerate(articles, 1):
            # Truncate text if too long
            article_text = article.text[:200] + "..." if len(article.text) > 200 else article.text
            
            text += f"{i}. {article.author_username}\n"
            text += f"   {article_text}\n"
            text += f"   Score: {article.score:.2f} | ❤️ {article.likes:,} | 🔄 {article.retweets:,} | 💬 {article.replies:,}\n"
            text += f"   View: {article.url}\n\n"
        
        text += f"\nGenerated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return text
    
    def send_analytics_report(self, stats: Dict) -> bool:
        """Send analytics report via email.
        
        Args:
            stats: Analytics statistics
            
        Returns:
            True if email sent successfully
        """
        if not self.is_available():
            return False
        
        try:
            subject = "📊 Robotics Radar - Daily Analytics Report"
            
            # Create HTML content
            html_content = self._create_analytics_html(stats)
            
            # Create plain text content
            text_content = self._create_analytics_text(stats)
            
            # Create and send message
            message = self._create_message(subject, html_content, text_content)
            return self._send_email(message)
            
        except Exception as e:
            logger.error(f"Error creating analytics email: {e}")
            return False
    
    def _create_analytics_html(self, stats: Dict) -> str:
        """Create HTML content for analytics report.
        
        Args:
            stats: Analytics statistics
            
        Returns:
            HTML content string
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #1da1f2; color: white; padding: 20px; text-align: center; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat {{ text-align: center; padding: 15px; background-color: #f8f9fa; border-radius: 8px; }}
                .stat-number {{ font-size: 2em; font-weight: bold; color: #1da1f2; }}
                .stat-label {{ color: #666; }}
                .section {{ margin: 20px 0; }}
                .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Robotics Radar Analytics</h1>
                <p>Daily Report</p>
            </div>
            
            <div style="padding: 20px;">
                <div class="stats">
                    <div class="stat">
                        <div class="stat-number">{stats.get('total_articles', 0):,}</div>
                        <div class="stat-label">Total Articles</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">{stats.get('total_authors', 0):,}</div>
                        <div class="stat-label">Total Authors</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">{stats.get('avg_score', 0):.2f}</div>
                        <div class="stat-label">Avg Score</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">{stats.get('recent_articles', 0):,}</div>
                        <div class="stat-label">Recent (24h)</div>
                    </div>
                </div>
        """
        
        # Add top authors
        top_authors = stats.get('top_authors', [])
        if top_authors:
            html += """
                <div class="section">
                    <h2>🏆 Top Authors</h2>
            """
            for i, author in enumerate(top_authors[:5], 1):
                html += f"""
                    <div style="padding: 10px; border-bottom: 1px solid #eee;">
                        {i}. @{author['username']} - {author['followers_count']:,} followers
                    </div>
                """
            html += "</div>"
        
        # Add trending topics
        trending_topics = stats.get('trending_topics', [])
        if trending_topics:
            html += """
                <div class="section">
                    <h2>🔥 Trending Topics</h2>
            """
            for i, topic in enumerate(trending_topics[:5], 1):
                html += f"""
                    <div style="padding: 10px; border-bottom: 1px solid #eee;">
                        {i}. {topic['name']} - {topic['frequency']} mentions
                    </div>
                """
            html += "</div>"
        
        html += f"""
            </div>
            
            <div class="footer">
                <p>Robotics Radar - Automated robotics content curation</p>
                <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _create_analytics_text(self, stats: Dict) -> str:
        """Create plain text content for analytics report.
        
        Args:
            stats: Analytics statistics
            
        Returns:
            Plain text content string
        """
        text = "📊 Robotics Radar - Daily Analytics Report\n"
        text += "=" * 50 + "\n\n"
        
        text += f"📈 Total Articles: {stats.get('total_articles', 0):,}\n"
        text += f"👥 Total Authors: {stats.get('total_authors', 0):,}\n"
        text += f"⭐ Average Score: {stats.get('avg_score', 0):.2f}\n"
        text += f"🕐 Recent Articles (24h): {stats.get('recent_articles', 0):,}\n\n"
        
        # Add top authors
        top_authors = stats.get('top_authors', [])
        if top_authors:
            text += "🏆 Top Authors:\n"
            for i, author in enumerate(top_authors[:5], 1):
                text += f"{i}. @{author['username']} ({author['followers_count']:,} followers)\n"
            text += "\n"
        
        # Add trending topics
        trending_topics = stats.get('trending_topics', [])
        if trending_topics:
            text += "🔥 Trending Topics:\n"
            for i, topic in enumerate(trending_topics[:5], 1):
                text += f"{i}. {topic['name']} ({topic['frequency']} mentions)\n"
        
        text += f"\nGenerated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return text


def main():
    """Main function for testing email notifications."""
    try:
        notifier = EmailNotifier()
        
        if not notifier.is_available():
            logger.error("Email notifier not configured")
            return
        
        # Test email with sample data
        sample_tweets = [
            Tweet(
                id="123456789",
                text="This is a sample robotics tweet for testing email notifications.",
                author_id="123",
                author_username="test_user",
                author_name="Test User",
                author_followers=1000,
                likes=50,
                retweets=10,
                replies=5,
                url="https://twitter.com/test_user/status/123456789",
                created_at=datetime.now(),
                score=85.5
            )
        ]
        
        success = notifier.send_top_tweets(sample_tweets)
        if success:
            print("Test email sent successfully")
        else:
            print("Failed to send test email")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    main() 