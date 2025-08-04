#!/usr/bin/env python3
"""
Update all article scores with new recency bonus.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.database import DatabaseManager
from scoring.scoring_model import ScoringModel

def main():
    """Update all article scores."""
    print("🔄 Updating all article scores with recency bonus...")
    
    try:
        db = DatabaseManager()
        scoring_model = ScoringModel()
        
        # Get all articles
        articles = db.get_top_articles(limit=1000)  # Get all articles
        
        if not articles:
            print("❌ No articles found in database")
            return
        
        print(f"📊 Found {len(articles)} articles to update")
        
        updated_count = 0
        
        for article in articles:
            try:
                # Convert article to dict format for scoring
                article_data = {
                    'id': article.id,
                    'text': article.text,
                    'author_id': article.author_id,
                    'author_username': article.author_username,
                    'author_name': article.author_name,
                    'author_followers': article.author_followers,
                    'likes': article.likes,
                    'retweets': article.retweets,
                    'replies': article.replies,
                    'url': article.url,
                    'created_at': article.created_at,
                    'score': article.score,
                    'topics': article.topics,
                    'categories': article.categories,
                    'summary': article.summary
                }
                
                # Calculate new score with recency bonus
                new_score = scoring_model.calculate_final_score(article_data)
                
                # Update score in database
                if abs(new_score - article.score) > 0.1:  # Only update if score changed significantly
                    db.update_article_score(article.id, new_score)
                    updated_count += 1
                    
                    print(f"  📈 Updated {article.id[:8]}...: {article.score:.1f} → {new_score:.1f}")
                
            except Exception as e:
                print(f"  ❌ Error updating article {article.id[:8]}...: {e}")
                continue
        
        print(f"\n✅ Score update completed!")
        print(f"📊 Updated {updated_count} articles out of {len(articles)}")
        
        # Show some examples of updated scores
        print(f"\n📋 Recent articles with recency bonus:")
        recent_articles = db.get_top_articles(limit=5)
        for i, article in enumerate(recent_articles, 1):
            print(f"  {i}. {article.text[:60]}... (Score: {article.score:.1f})")
        
    except Exception as e:
        print(f"❌ Error updating scores: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 