#!/usr/bin/env python3
"""
Test script to verify Telegram message fixes:
1. No duplicates
2. Better HTML cleaning
3. Enhanced summaries with ArticleReader
"""

from storage.database import DatabaseManager
from notifier.telegram_bot import TelegramNotifier
from agent_integration.article_reader import ArticleReader
import re

def test_html_cleaning():
    """Test the improved HTML cleaning."""
    print("🧪 Testing HTML Cleaning")
    print("=" * 50)
    
    notifier = TelegramNotifier()
    
    # Test cases with HTML jibrish
    test_cases = [
        "Beyond the assembly line — swarm robotics emerge <img alt=\"A computer-generated image of futuristic aerospace assembly with swarm robotics\" class=\"size-full wp-image-584800\" height=\"400\" src=\"https://www.therobotreport.com/wp-content/uploads/2025/07/swarm-robotics-aerospace.jpg\" width=\"600\">",
        "Swarm robotics could spell the end of the assembly line <div class=\"wp-caption aligncenter\" id=\"attachment_583769\" style=\"width: 600px\">",
        "Top 10 robotics developments of July 2025 <p>July 2025 brought fresh funding rounds, new milestones in robotics, and exciting new deployments. In addition, The Robot Report team has been busy covering the latest developments in the robotics industry.</p>"
    ]
    
    for i, test_text in enumerate(test_cases, 1):
        cleaned = notifier._clean_html_text(test_text)
        print(f"{i}. Original: {test_text[:80]}...")
        print(f"   Cleaned:  {cleaned[:80]}...")
        print()

def test_enhanced_summaries():
    """Test enhanced summaries with ArticleReader."""
    print("🧪 Testing Enhanced Summaries")
    print("=" * 50)
    
    db = DatabaseManager()
    article_reader = ArticleReader()
    
    # Get a few articles from database
    tweets = db.get_top_tweets(limit=3)
    
    for i, tweet in enumerate(tweets, 1):
        print(f"{i}. Article: {tweet.text[:60]}...")
        print(f"   Original Summary: {tweet.summary[:100]}...")
        
        # Try to enhance with ArticleReader
        try:
            if tweet.url and tweet.url.startswith('http'):
                article_content = article_reader.read_article(tweet.url)
                if article_content and article_content.get('summary'):
                    enhanced_summary = article_content['summary']
                    print(f"   Enhanced Summary: {enhanced_summary[:150]}...")
                else:
                    print(f"   Enhanced Summary: No enhancement available")
            else:
                print(f"   Enhanced Summary: No URL available")
        except Exception as e:
            print(f"   Enhanced Summary: Error - {e}")
        print()

def test_no_duplicates():
    """Test that we get unique articles from database."""
    print("🧪 Testing No Duplicates")
    print("=" * 50)
    
    db = DatabaseManager()
    
    # Get top 10 articles
    tweets = db.get_top_tweets(limit=10)
    
    print(f"Retrieved {len(tweets)} articles from database")
    
    # Check for duplicates by URL
    urls = []
    duplicates = []
    
    for tweet in tweets:
        if tweet.url in urls:
            duplicates.append(tweet.url)
        else:
            urls.append(tweet.url)
    
    if duplicates:
        print(f"❌ Found {len(duplicates)} duplicate URLs:")
        for url in duplicates:
            print(f"   - {url}")
    else:
        print("✅ No duplicate URLs found!")
    
    # Check for duplicate titles
    titles = []
    duplicate_titles = []
    
    for tweet in tweets:
        clean_title = tweet.text.split('\n')[0] if tweet.text else ""
        if clean_title in titles:
            duplicate_titles.append(clean_title)
        else:
            titles.append(clean_title)
    
    if duplicate_titles:
        print(f"❌ Found {len(duplicate_titles)} duplicate titles:")
        for title in duplicate_titles:
            print(f"   - {title}")
    else:
        print("✅ No duplicate titles found!")
    
    print()

def test_telegram_message_format():
    """Test the complete Telegram message format."""
    print("🧪 Testing Telegram Message Format")
    print("=" * 50)
    
    db = DatabaseManager()
    notifier = TelegramNotifier()
    
    # Get top 3 articles
    tweets = db.get_top_tweets(limit=3)
    
    # Simulate the message building process
    message = "🤖 *Robotics Radar Update*\n\n"
    message += f"Here are the top {len(tweets)} robotics articles:\n\n"
    
    for i, tweet in enumerate(tweets, 1):
        # Clean up the text by removing HTML tags and truncating properly
        clean_text = notifier._clean_html_text(tweet.text)
        title = clean_text.split('\n')[0] if clean_text else "No title"
        title = title[:80] + "..." if len(title) > 80 else title
        
        # Use ArticleReader to enhance summary if available
        enhanced_summary = tweet.summary
        try:
            from agent_integration.article_reader import ArticleReader
            article_reader = ArticleReader()
            if tweet.url and tweet.url.startswith('http'):
                # Try to get enhanced summary from ArticleReader
                article_content = article_reader.read_article(tweet.url)
                if article_content and article_content.get('summary'):
                    enhanced_summary = article_content['summary']
        except Exception as e:
            pass
        
        # Clean up summary and make it longer
        clean_summary = notifier._clean_html_text(enhanced_summary or "No summary available")
        clean_summary = clean_summary[:300] + "..." if len(clean_summary) > 300 else clean_summary
        
        message += f"*{i}. {title}*\n"
        message += f"👤 {tweet.author_name}\n"
        message += f"📝 {clean_summary}\n"
        message += f"⭐ Score: {tweet.score:.1f}\n"
        message += f"🔗 [Read Article]({tweet.url})\n\n"
    
    print("Generated Telegram message preview:")
    print("-" * 50)
    print(message)
    print("-" * 50)
    
    # Check for HTML tags in the message
    html_tags = re.findall(r'<[^>]+>', message)
    if html_tags:
        print(f"❌ Found {len(html_tags)} HTML tags in message:")
        for tag in html_tags[:5]:  # Show first 5
            print(f"   - {tag}")
    else:
        print("✅ No HTML tags found in message!")
    
    # Check message length
    print(f"📏 Message length: {len(message)} characters")
    if len(message) > 4000:
        print("⚠️  Message might be too long for Telegram")
    else:
        print("✅ Message length is acceptable")

def main():
    """Run all tests."""
    print("🚀 Testing Telegram Message Fixes")
    print("=" * 60)
    print()
    
    test_html_cleaning()
    test_enhanced_summaries()
    test_no_duplicates()
    test_telegram_message_format()
    
    print("🎉 All tests completed!")

if __name__ == "__main__":
    main() 