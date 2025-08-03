#!/usr/bin/env python3
"""
Script to update existing articles with improved keywords
"""

from storage.database import DatabaseManager
from nlp.keyword_extraction import KeywordExtractor
import json
import sqlite3

def update_article_keywords():
    """Update all articles in the database with improved keywords."""
    print("🔄 Updating article keywords...")
    
    db = DatabaseManager()
    extractor = KeywordExtractor()
    
    # Get all articles
    tweets = db.get_top_tweets(limit=1000)  # Get all articles
    print(f"📊 Found {len(tweets)} articles to update")
    
    # Update each article
    updated_count = 0
    for i, tweet in enumerate(tweets):
        try:
            # Extract new keywords
            new_topics = extractor.extract_topics(tweet.text)
            
            # Update the database
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE tweets SET topics = ? WHERE id = ?",
                    (json.dumps(new_topics), tweet.id)
                )
                conn.commit()
            
            updated_count += 1
            
            # Show progress
            if (i + 1) % 10 == 0:
                print(f"✅ Updated {i + 1}/{len(tweets)} articles")
                
        except Exception as e:
            print(f"❌ Error updating article {tweet.id}: {e}")
    
    print(f"🎉 Successfully updated {updated_count}/{len(tweets)} articles with new keywords!")
    
    # Show sample of updated articles
    print("\n📋 Sample of updated articles:")
    updated_tweets = db.get_top_tweets(limit=5)
    for i, tweet in enumerate(updated_tweets, 1):
        topics = json.loads(tweet.topics) if tweet.topics else []
        print(f"{i}. {tweet.text[:50]}... -> {topics}")

if __name__ == "__main__":
    update_article_keywords() 