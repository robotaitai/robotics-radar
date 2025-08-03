#!/usr/bin/env python3
"""
Simple script to check dashboard data
"""

from storage.database import DatabaseManager
import pandas as pd

def main():
    print("🔍 Checking Dashboard Data")
    print("=" * 50)
    
    # Initialize database
    db = DatabaseManager()
    
    # Get top tweets
    tweets = db.get_top_tweets(limit=50)
    print(f"📊 Total articles in database: {len(tweets)}")
    
    # Deduplicate by URL
    seen_urls = set()
    unique_tweets = []
    for tweet in tweets:
        if tweet.url not in seen_urls:
            seen_urls.add(tweet.url)
            unique_tweets.append(tweet)
    
    print(f"✅ Unique articles after deduplication: {len(unique_tweets)}")
    print()
    
    # Display articles
    print("📋 Articles that should appear in dashboard:")
    print("-" * 50)
    
    for i, tweet in enumerate(unique_tweets[:20], 1):
        # Clean title
        title = tweet.text.split('\n')[0][:60] + "..." if len(tweet.text.split('\n')[0]) > 60 else tweet.text.split('\n')[0]
        print(f"{i:2d}. {title}")
        print(f"    👤 {tweet.author_name}")
        print(f"    ⭐ Score: {tweet.score:.1f}")
        print(f"    🔗 {tweet.url}")
        print()
    
    print("=" * 50)
    print("✅ If you see 20 articles above, the dashboard should show them too!")
    print("💡 Try refreshing your browser (Ctrl+F5) if you only see 4 articles.")

if __name__ == "__main__":
    main() 