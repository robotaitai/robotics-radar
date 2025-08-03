#!/usr/bin/env python3
"""
Test script for new dashboard features
"""

from storage.database import DatabaseManager
from analytics.dashboard import AnalyticsDashboard

def test_keywords_extraction():
    """Test keywords extraction functionality."""
    print("🔍 Testing Keywords Extraction")
    print("=" * 50)
    
    db = DatabaseManager()
    dashboard = AnalyticsDashboard()
    
    # Get some tweets
    tweets = db.get_top_tweets(limit=5)
    
    for i, tweet in enumerate(tweets, 1):
        print(f"\n{i}. {tweet.text[:60]}...")
        print(f"   Keywords: {tweet.topics[:5] if tweet.topics else 'No topics'}")
        
        # Test the dashboard's keyword extraction
        keywords = dashboard._extract_keywords_for_display(tweet)
        print(f"   Dashboard Keywords: {keywords}")

def test_article_limit():
    """Test configurable article limit."""
    print("\n\n📊 Testing Article Limit Configuration")
    print("=" * 50)
    
    db = DatabaseManager()
    
    # Test different limits
    for limit in [5, 10, 20, 50]:
        tweets = db.get_top_tweets(limit=limit)
        print(f"Requested {limit} articles, got {len(tweets)} articles")
        
        if tweets:
            print(f"   First article: {tweets[0].text[:50]}...")
            print(f"   Last article: {tweets[-1].text[:50]}...")

def main():
    print("🧪 Testing New Dashboard Features")
    print("=" * 60)
    
    test_keywords_extraction()
    test_article_limit()
    
    print("\n" + "=" * 60)
    print("✅ Testing complete!")
    print("🎯 New features:")
    print("   - Keywords column added to dashboard table")
    print("   - Configurable article limit (5-100 articles)")
    print("   - Keywords extracted from topics or generated from text")
    print("\n💡 Open http://localhost:8501 to see the updated dashboard!")

if __name__ == "__main__":
    main() 