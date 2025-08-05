"""
Database operations for Robotics Radar.
Handles SQLite database initialization, schema, and CRUD operations.
"""

import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Article:
    """Data class for article information."""
    id: str
    text: str
    author_id: str
    author_username: str
    author_name: str
    author_followers: int
    likes: int
    retweets: int
    replies: int
    url: str
    created_at: datetime
    score: float = 0.0
    topics: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    summary: Optional[str] = None

@dataclass
class Author:
    """Data class for author information."""
    id: str
    username: str
    name: str
    followers_count: int
    verified: bool
    created_at: datetime

@dataclass
class Feedback:
    """Data class for user feedback."""
    id: int
    article_id: str
    user_id: str
    feedback_type: str  # 'like', 'dislike', 'rating_1', 'rating_2', etc.
    created_at: datetime

class DatabaseManager:
    """Manages SQLite database operations for Robotics Radar."""
    
    def __init__(self, db_path: str = "data/radar.db"):
        """Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with proper configuration.
        
        Returns:
            SQLite connection object
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def init_database(self) -> None:
        """Initialize database schema."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create articles table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS articles (
                        id TEXT PRIMARY KEY,
                        text TEXT NOT NULL,
                        author_id TEXT NOT NULL,
                        author_username TEXT NOT NULL,
                        author_name TEXT NOT NULL,
                        author_followers INTEGER NOT NULL,
                        likes INTEGER DEFAULT 0,
                        retweets INTEGER DEFAULT 0,
                        replies INTEGER DEFAULT 0,
                        url TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        score REAL DEFAULT 0.0,
                        topics TEXT,
                        categories TEXT,
                        summary TEXT,
                        created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create authors table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS authors (
                        id TEXT PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        followers_count INTEGER DEFAULT 0,
                        verified BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create feedback table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS feedback (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        article_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        feedback_type TEXT NOT NULL CHECK (feedback_type IN ('like', 'dislike', 'rating_1', 'rating_2', 'rating_3', 'rating_4', 'rating_5')),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (article_id) REFERENCES articles (id),
                        UNIQUE(article_id, user_id)
                    )
                """)
                
                # Create topics table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS topics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        frequency INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_score ON articles (score DESC)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_created_at ON articles (created_at DESC)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_author_id ON articles (author_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_article_id ON feedback (article_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_topics_frequency ON topics (frequency DESC)")
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def insert_article(self, article: Article) -> bool:
        """Insert a new article into the database.
        
        Args:
            article: Article object to insert
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Insert or update author
                cursor.execute("""
                    INSERT OR REPLACE INTO authors 
                    (id, username, name, followers_count, verified, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    article.author_id,
                    article.author_username,
                    article.author_name,
                    article.author_followers,
                    False,  # Default verified status
                    datetime.now()
                ))
                
                # Insert article
                cursor.execute("""
                    INSERT OR REPLACE INTO articles 
                    (id, text, author_id, author_username, author_name, author_followers,
                     likes, retweets, replies, url, created_at, score, topics, categories, summary)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    article.id,
                    article.text,
                    article.author_id,
                    article.author_username,
                    article.author_name,
                    article.author_followers,
                    article.likes,
                    article.retweets,
                    article.replies,
                    article.url,
                    article.created_at,
                    article.score,
                    json.dumps(article.topics) if article.topics else None,
                    json.dumps(article.categories) if article.categories else None,
                    article.summary
                ))
                
                conn.commit()
                logger.info(f"Article {article.id} inserted successfully")
                return True
                
        except Exception as e:
            logger.error(f"Error inserting article {article.id}: {e}")
            return False
    
    def get_top_articles(self, limit: int = 10) -> List[Article]:
        """Get top articles by score.
        
        Args:
            limit: Number of articles to return
            
        Returns:
            List of Article objects
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM articles 
                    ORDER BY score DESC 
                    LIMIT ?
                """, (limit,))
                
                articles = []
                for row in cursor.fetchall():
                    article = Article(
                        id=row['id'],
                        text=row['text'],
                        author_id=row['author_id'],
                        author_username=row['author_username'],
                        author_name=row['author_name'],
                        author_followers=row['author_followers'],
                        likes=row['likes'],
                        retweets=row['retweets'],
                        replies=row['replies'],
                        url=row['url'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        score=row['score'],
                        topics=json.loads(row['topics']) if row['topics'] else None,
                        categories=json.loads(row['categories']) if row['categories'] else None,
                        summary=row['summary']
                    )
                    articles.append(article)
                
                return articles
                
        except Exception as e:
            logger.error(f"Error getting top articles: {e}")
            return []
    
    def get_article_by_id(self, article_id: str) -> Optional[Article]:
        """Get a specific article by ID.
        
        Args:
            article_id: ID of the article to retrieve
            
        Returns:
            Article object if found, None otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM articles 
                    WHERE id = ?
                """, (article_id,))
                
                row = cursor.fetchone()
                if row:
                    return Article(
                        id=row['id'],
                        text=row['text'],
                        author_id=row['author_id'],
                        author_username=row['author_username'],
                        author_name=row['author_name'],
                        author_followers=row['author_followers'],
                        likes=row['likes'],
                        retweets=row['retweets'],
                        replies=row['replies'],
                        url=row['url'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        score=row['score'],
                        topics=json.loads(row['topics']) if row['topics'] else None,
                        categories=json.loads(row['categories']) if row['categories'] else None,
                        summary=row['summary']
                    )
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting article by ID {article_id}: {e}")
            return None
    
    def update_article_score(self, article_id: str, score: float) -> bool:
        """Update article score.
        
        Args:
            article_id: ID of the article
            score: New score value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE articles 
                    SET score = ? 
                    WHERE id = ?
                """, (score, article_id))
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error updating article score: {e}")
            return False
    
    def add_feedback(self, article_id: str, user_id: str, feedback_type: str) -> bool:
        """Add user feedback for an article.
        
        Args:
            article_id: ID of the article
            user_id: ID of the user
            feedback_type: Type of feedback ('like', 'dislike', 'rating_1', etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO feedback 
                    (article_id, user_id, feedback_type, created_at)
                    VALUES (?, ?, ?, ?)
                """, (article_id, user_id, feedback_type, datetime.now()))
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error adding feedback: {e}")
            return False
    
    def get_article_feedback(self, article_id: str) -> Dict[str, int]:
        """Get feedback statistics for an article.
        
        Args:
            article_id: ID of the article
            
        Returns:
            Dictionary with feedback counts
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT feedback_type, COUNT(*) as count 
                    FROM feedback 
                    WHERE article_id = ?
                    GROUP BY feedback_type
                """, (article_id,))
                
                feedback = {}
                for row in cursor.fetchall():
                    feedback[row['feedback_type']] = row['count']
                
                return feedback
                
        except Exception as e:
            logger.error(f"Error getting article feedback: {e}")
            return {}
    
    def get_top_authors(self, limit: int = 10) -> List[Dict]:
        """Get top authors by follower count.
        
        Args:
            limit: Number of authors to return
            
        Returns:
            List of author dictionaries
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT a.*, COUNT(ar.id) as tweet_count
                    FROM authors a
                    LEFT JOIN articles ar ON a.id = ar.author_id
                    GROUP BY a.id
                    ORDER BY a.followers_count DESC
                    LIMIT ?
                """, (limit,))
                
                authors = []
                for row in cursor.fetchall():
                    authors.append({
                        'id': row['id'],
                        'username': row['username'],
                        'name': row['name'],
                        'followers_count': row['followers_count'],
                        'verified': row['verified'],
                        'tweet_count': row['tweet_count']
                    })
                
                return authors
                
        except Exception as e:
            logger.error(f"Error getting top authors: {e}")
            return []
    
    def get_trending_topics(self, limit: int = 10) -> List[Dict]:
        """Get trending topics by frequency.
        
        Args:
            limit: Number of topics to return
            
        Returns:
            List of topic dictionaries
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM topics 
                    ORDER BY frequency DESC 
                    LIMIT ?
                """, (limit,))
                
                topics = []
                for row in cursor.fetchall():
                    topics.append({
                        'id': row['id'],
                        'name': row['name'],
                        'frequency': row['frequency'],
                        'created_at': row['created_at']
                    })
                
                return topics
                
        except Exception as e:
            logger.error(f"Error getting trending topics: {e}")
            return []
    
    def update_topic_frequency(self, topic_name: str) -> bool:
        """Update topic frequency count.
        
        Args:
            topic_name: Name of the topic
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO topics 
                    (name, frequency, updated_at)
                    VALUES (?, 
                        COALESCE((SELECT frequency FROM topics WHERE name = ?), 0) + 1,
                        ?)
                """, (topic_name, topic_name, datetime.now()))
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error updating topic frequency: {e}")
            return False
    
    def get_analytics_summary(self) -> Dict:
        """Get analytics summary for dashboard.
        
        Returns:
            Dictionary with analytics data
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get total articles
                cursor.execute("SELECT COUNT(*) as count FROM articles")
                total_articles = cursor.fetchone()['count']
                
                # Get total authors
                cursor.execute("SELECT COUNT(*) as count FROM authors")
                total_authors = cursor.fetchone()['count']
                
                # Get average score
                cursor.execute("SELECT AVG(score) as avg_score FROM articles")
                avg_score = cursor.fetchone()['avg_score'] or 0.0
                
                # Get recent articles (last 24 hours)
                cursor.execute("""
                    SELECT COUNT(*) as count FROM articles 
                    WHERE created_at >= datetime('now', '-1 day')
                """)
                recent_articles = cursor.fetchone()['count']
                
                # Get total feedback
                cursor.execute("SELECT COUNT(*) as count FROM feedback")
                total_feedback = cursor.fetchone()['count']
                
                # Get top authors
                top_authors = self.get_top_authors(limit=3)
                
                # Get trending topics
                trending_topics = self.get_trending_topics(limit=5)
                
                return {
                    'total_articles': total_articles,
                    'total_authors': total_authors,
                    'avg_score': avg_score,
                    'recent_articles': recent_articles,
                    'total_feedback': total_feedback,
                    'top_authors': top_authors,
                    'trending_topics': trending_topics
                }
                
        except Exception as e:
            logger.error(f"Error getting analytics summary: {e}")
            return {
                'total_articles': 0,
                'total_authors': 0,
                'avg_score': 0.0,
                'recent_articles': 0,
                'total_feedback': 0,
                'top_authors': [],
                'trending_topics': []
            }
    
    def get_feedback_stats(self) -> Dict:
        """Get feedback statistics for 1-5 star rating system.
        
        Returns:
            Dictionary with feedback statistics
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get rating counts for 1-5 stars
                rating_stats = {}
                for rating in range(1, 6):
                    cursor.execute("""
                        SELECT COUNT(*) as count FROM feedback 
                        WHERE feedback_type = ?
                    """, (f'rating_{rating}',))
                    rating_stats[f'rating_{rating}'] = cursor.fetchone()['count']
                
                # Also get legacy like/dislike counts for backward compatibility
                cursor.execute("""
                    SELECT COUNT(*) as count FROM feedback 
                    WHERE feedback_type = 'like'
                """)
                likes = cursor.fetchone()['count']
                
                cursor.execute("""
                    SELECT COUNT(*) as count FROM feedback 
                    WHERE feedback_type = 'dislike'
                """)
                dislikes = cursor.fetchone()['count']
                
                total_ratings = sum(rating_stats.values())
                total_feedback = total_ratings + likes + dislikes
                
                return {
                    **rating_stats,  # rating_1, rating_2, etc.
                    'likes': likes,
                    'dislikes': dislikes,
                    'total_ratings': total_ratings,
                    'total_feedback': total_feedback
                }
                
        except Exception as e:
            logger.error(f"Error getting feedback stats: {e}")
            return {
                'rating_1': 0, 'rating_2': 0, 'rating_3': 0, 'rating_4': 0, 'rating_5': 0,
                'likes': 0, 'dislikes': 0, 'total_ratings': 0, 'total_feedback': 0
            }
    
    def get_engagement_trends(self, days: int = 7) -> List[Dict]:
        """Get engagement trends over time.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            List of daily engagement data
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        DATE(created_at) as date,
                        COUNT(*) as article_count,
                        AVG(score) as avg_score,
                        SUM(likes + retweets + replies) as total_engagement
                    FROM articles 
                    WHERE created_at >= datetime('now', '-{} days')
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                """.format(days))
                
                trends = []
                for row in cursor.fetchall():
                    trends.append({
                        'date': row['date'],
                        'article_count': row['article_count'],
                        'avg_score': row['avg_score'],
                        'total_engagement': row['total_engagement']
                    })
                
                return trends
                
        except Exception as e:
            logger.error(f"Error getting engagement trends: {e}")
            return []
    
    def get_content_categories(self) -> List[Dict]:
        """Get content category distribution.
        
        Returns:
            List of category statistics
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        categories,
                        COUNT(*) as count,
                        AVG(score) as avg_score
                    FROM articles 
                    WHERE categories IS NOT NULL
                    GROUP BY categories
                    ORDER BY count DESC
                    LIMIT 10
                """)
                
                categories = []
                for row in cursor.fetchall():
                    if row['categories']:
                        try:
                            category_list = json.loads(row['categories'])
                            categories.append({
                                'categories': category_list,
                                'count': row['count'],
                                'avg_score': row['avg_score']
                            })
                        except json.JSONDecodeError:
                            continue
                
                return categories
                
        except Exception as e:
            logger.error(f"Error getting content categories: {e}")
            return []
    
    def url_exists(self, url: str) -> bool:
        """Check if URL already exists in database.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL exists, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM articles WHERE url = ?", (url,))
                return cursor.fetchone()['count'] > 0
                
        except Exception as e:
            logger.error(f"Error checking URL existence: {e}")
            return False
    
    def title_similarity_exists(self, title: str, similarity_threshold: float = 0.8) -> bool:
        """Check if a similar title already exists in the database.
        
        Args:
            title: Title to check
            similarity_threshold: Minimum similarity threshold (0.0 to 1.0)
            
        Returns:
            True if similar title exists, False otherwise
        """
        try:
            from difflib import SequenceMatcher
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT title FROM articles ORDER BY created_at DESC LIMIT 1000")
                existing_titles = [row['title'] for row in cursor.fetchall()]
                
                title_lower = title.lower()
                for existing_title in existing_titles:
                    existing_lower = existing_title.lower()
                    similarity = SequenceMatcher(None, title_lower, existing_lower).ratio()
                    if similarity >= similarity_threshold:
                        return True
                
                return False
        except Exception as e:
            logger.error(f"Error checking title similarity: {e}")
            return False
    
    def is_duplicate_content(self, title: str, url: str, content_preview: str = None) -> bool:
        """Check if content is duplicate based on URL and title similarity.
        
        Args:
            title: Article title
            url: Article URL
            content_preview: Preview of article content (optional)
            
        Returns:
            True if duplicate content detected, False otherwise
        """
        # Check URL first (exact match)
        if self.url_exists(url):
            return True
        
        # Check title similarity (fuzzy match)
        if self.title_similarity_exists(title):
            return True
        
        # Optional: Check content similarity if preview provided
        if content_preview:
            try:
                from difflib import SequenceMatcher
                
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT text FROM articles ORDER BY created_at DESC LIMIT 500")
                    existing_contents = [row['text'] for row in cursor.fetchall()]
                    
                    content_lower = content_preview.lower()
                    for existing_content in existing_contents:
                        existing_lower = existing_content.lower()
                        similarity = SequenceMatcher(None, content_lower, existing_lower).ratio()
                        if similarity >= 0.7:  # 70% content similarity threshold
                            return True
            except Exception as e:
                logger.error(f"Error checking content similarity: {e}")
        
        return False
    
    def delete_duplicate_urls(self) -> int:
        """Delete duplicate articles based on URL.
        
        Returns:
            Number of duplicates deleted
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Find and delete duplicates, keeping the one with highest score
                cursor.execute("""
                    DELETE FROM articles 
                    WHERE id NOT IN (
                        SELECT MIN(id) 
                        FROM articles 
                        GROUP BY url
                    )
                """)
                
                deleted_count = cursor.rowcount
                conn.commit()
                logger.info(f"Deleted {deleted_count} duplicate articles")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error deleting duplicate URLs: {e}")
            return 0
    
    def get_articles_with_review_status(self) -> List[Dict]:
        """Get articles with their review status from feedback.
        
        Returns:
            List of articles with review status
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get articles with review status from feedback table
                cursor.execute("""
                    SELECT 
                        a.id,
                        a.text,
                        a.author_name,
                        a.score,
                        a.created_at,
                        f.feedback_type as review_status,
                        f.created_at as review_date
                    FROM articles a
                    LEFT JOIN feedback f ON a.id = f.article_id
                    WHERE f.feedback_type IN ('approved', 'rejected', 'edited', 'skipped')
                    ORDER BY f.created_at DESC
                """)
                
                rows = cursor.fetchall()
                articles = []
                
                for row in rows:
                    articles.append({
                        'id': row['id'],
                        'text': row['text'],
                        'author_name': row['author_name'],
                        'score': row['score'],
                        'created_at': row['created_at'],
                        'review_status': row['review_status'],
                        'review_date': row['review_date']
                    })
                
                return articles
                
        except Exception as e:
            logger.error(f"Error getting articles with review status: {e}")
            return []
    
    def get_diverse_articles(self, limit: int = 10) -> List[Article]:
        """Get diverse articles mixing high-score and recent articles.
        
        Args:
            limit: Maximum number of articles to return
            
        Returns:
            List of diverse articles
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get half high-score articles and half recent articles
                half_limit = limit // 2
                
                # Get top articles by score
                cursor.execute("""
                    SELECT * FROM articles 
                    ORDER BY score DESC 
                    LIMIT ?
                """, (half_limit,))
                
                high_score_rows = cursor.fetchall()
                
                # Get recent articles
                cursor.execute("""
                    SELECT * FROM articles 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (half_limit,))
                
                recent_rows = cursor.fetchall()
                
                # Combine and deduplicate
                all_rows = high_score_rows + recent_rows
                seen_ids = set()
                unique_rows = []
                
                for row in all_rows:
                    if row['id'] not in seen_ids:
                        seen_ids.add(row['id'])
                        unique_rows.append(row)
                
                # Sort by score and take top limit
                unique_rows.sort(key=lambda x: x['score'], reverse=True)
                unique_rows = unique_rows[:limit]
                
                articles = []
                for row in unique_rows:
                    article = Article(
                        id=row['id'],
                        text=row['text'],
                        author_id=row['author_id'],
                        author_username=row['author_username'],
                        author_name=row['author_name'],
                        author_followers=row['author_followers'],
                        likes=row['likes'],
                        retweets=row['retweets'],
                        replies=row['replies'],
                        url=row['url'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        score=row['score'],
                        topics=json.loads(row['topics']) if row['topics'] else None,
                        categories=json.loads(row['categories']) if row['categories'] else None,
                        summary=row['summary']
                    )
                    articles.append(article)
                
                return articles
                
        except Exception as e:
            logger.error(f"Error getting diverse articles: {e}")
            return []
    
    def get_unpublished_articles(self, limit: int = 10) -> List[Article]:
        """Get articles that haven't been published yet.
        
        Args:
            limit: Maximum number of articles to return
            
        Returns:
            List of unpublished articles
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM articles 
                    WHERE published_at IS NULL
                    ORDER BY score DESC, created_at DESC
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                articles = []
                
                for row in rows:
                    article = Article(
                        id=row['id'],
                        text=row['text'],
                        author_id=row['author_id'],
                        author_username=row['author_username'],
                        author_name=row['author_name'],
                        author_followers=row['author_followers'],
                        likes=row['likes'],
                        retweets=row['retweets'],
                        replies=row['replies'],
                        url=row['url'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        score=row['score'],
                        topics=json.loads(row['topics']) if row['topics'] else None,
                        categories=json.loads(row['categories']) if row['categories'] else None,
                        summary=row['summary']
                    )
                    articles.append(article)
                
                return articles
                
        except Exception as e:
            logger.error(f"Error getting unpublished articles: {e}")
            return []
    
    def get_next_article_to_publish(self) -> Optional[Article]:
        """Get the next best article to publish.
        Prioritizes new articles, then unpublished articles by score.
        
        Returns:
            Next article to publish or None if no articles available
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # First, try to get a new article (created in last 2 hours)
                cursor.execute("""
                    SELECT * FROM articles 
                    WHERE published_at IS NULL 
                    AND created_at >= datetime('now', '-2 hours')
                    ORDER BY score DESC, created_at DESC
                    LIMIT 1
                """)
                
                row = cursor.fetchone()
                
                if row:
                    article = Article(
                        id=row['id'],
                        text=row['text'],
                        author_id=row['author_id'],
                        author_username=row['author_username'],
                        author_name=row['author_name'],
                        author_followers=row['author_followers'],
                        likes=row['likes'],
                        retweets=row['retweets'],
                        replies=row['replies'],
                        url=row['url'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        score=row['score'],
                        topics=json.loads(row['topics']) if row['topics'] else None,
                        categories=json.loads(row['categories']) if row['categories'] else None,
                        summary=row['summary']
                    )
                    return article
                
                # If no new articles, get the best unpublished article
                cursor.execute("""
                    SELECT * FROM articles 
                    WHERE published_at IS NULL
                    ORDER BY score DESC, created_at DESC
                    LIMIT 1
                """)
                
                row = cursor.fetchone()
                
                if row:
                    article = Article(
                        id=row['id'],
                        text=row['text'],
                        author_id=row['author_id'],
                        author_username=row['author_username'],
                        author_name=row['author_name'],
                        author_followers=row['author_followers'],
                        likes=row['likes'],
                        retweets=row['retweets'],
                        replies=row['replies'],
                        url=row['url'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        score=row['score'],
                        topics=json.loads(row['topics']) if row['topics'] else None,
                        categories=json.loads(row['categories']) if row['categories'] else None,
                        summary=row['summary']
                    )
                    return article
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting next article to publish: {e}")
            return None
    
    def mark_article_published(self, article_id: str) -> bool:
        """Mark an article as published with current timestamp.
        
        Args:
            article_id: ID of the article to mark as published
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE articles 
                    SET published_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (article_id,))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error marking article as published: {e}")
            return False
    
    def get_published_articles_count(self) -> int:
        """Get count of published articles.
        
        Returns:
            Number of published articles
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT COUNT(*) FROM articles 
                    WHERE published_at IS NOT NULL
                """)
                
                return cursor.fetchone()[0]
                
        except Exception as e:
            logger.error(f"Error getting published articles count: {e}")
            return 0
    
    def get_unpublished_articles_count(self) -> int:
        """Get count of unpublished articles.
        
        Returns:
            Number of unpublished articles
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT COUNT(*) FROM articles 
                    WHERE published_at IS NULL
                """)
                
                return cursor.fetchone()[0]
                
        except Exception as e:
            logger.error(f"Error getting unpublished articles count: {e}")
            return 0
    
    def clear_all_data(self) -> bool:
        """Clear all data from the database.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Clear all tables
                cursor.execute("DELETE FROM feedback")
                cursor.execute("DELETE FROM articles")
                cursor.execute("DELETE FROM authors")
                cursor.execute("DELETE FROM topics")
                
                conn.commit()
                logger.info("All data cleared from database")
                return True
                
        except Exception as e:
            logger.error(f"Error clearing database: {e}")
            return False 