#!/usr/bin/env python3
"""
Migration script to update the database for the new 1-5 star rating system.
"""

import sys
import os
import sqlite3
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.database import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_rating_system():
    """Migrate the database to support 1-5 star ratings."""
    print("🔄 Migrating Database for 1-5 Star Rating System")
    print("=" * 50)
    
    try:
        db = DatabaseManager()
        
        # Get database connection
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if feedback table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='feedback'")
            if not cursor.fetchone():
                print("❌ Feedback table doesn't exist. Creating new database...")
                db.init_database()
                print("✅ Database created with new rating system support")
                return True
            
            # Check current constraint
            cursor.execute("PRAGMA table_info(feedback)")
            columns = cursor.fetchall()
            
            # Find the feedback_type column
            feedback_type_col = None
            for col in columns:
                if col[1] == 'feedback_type':
                    feedback_type_col = col
                    break
            
            if not feedback_type_col:
                print("❌ feedback_type column not found")
                return False
            
            print(f"📊 Current feedback_type constraint: {feedback_type_col[4]}")
            
            # Create new table with updated constraint
            print("🔄 Creating new feedback table with rating support...")
            
            # Create temporary table
            cursor.execute("""
                CREATE TABLE feedback_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tweet_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    feedback_type TEXT NOT NULL CHECK (feedback_type IN ('like', 'dislike', 'rating_1', 'rating_2', 'rating_3', 'rating_4', 'rating_5')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (tweet_id) REFERENCES tweets (id),
                    UNIQUE(tweet_id, user_id)
                )
            """)
            
            # Copy existing data (only like/dislike entries)
            cursor.execute("""
                INSERT INTO feedback_new (tweet_id, user_id, feedback_type, created_at)
                SELECT tweet_id, user_id, feedback_type, created_at
                FROM feedback
                WHERE feedback_type IN ('like', 'dislike')
            """)
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE feedback")
            cursor.execute("ALTER TABLE feedback_new RENAME TO feedback")
            
            # Recreate indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_tweet_id ON feedback (tweet_id)")
            
            conn.commit()
            
            print("✅ Database migrated successfully!")
            print("📊 New rating system supports: like, dislike, rating_1, rating_2, rating_3, rating_4, rating_5")
            
            return True
            
    except Exception as e:
        logger.error(f"Error migrating database: {e}")
        print(f"❌ Migration failed: {e}")
        return False

def test_migration():
    """Test the migration by trying to add a rating."""
    print("\n🧪 Testing Migration")
    print("=" * 30)
    
    try:
        db = DatabaseManager()
        
        # Test adding a rating
        success = db.add_feedback("test_migration_123", "test_user_456", "rating_4")
        
        if success:
            print("✅ Migration test successful - can add rating_4")
            
            # Clean up test data
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM feedback WHERE tweet_id = 'test_migration_123'")
                conn.commit()
            
            return True
        else:
            print("❌ Migration test failed - cannot add rating")
            return False
            
    except Exception as e:
        logger.error(f"Error testing migration: {e}")
        print(f"❌ Migration test failed: {e}")
        return False

def main():
    """Run the migration."""
    print("🚀 Database Migration for 1-5 Star Rating System")
    print("=" * 60)
    print()
    
    # Run migration
    migration_ok = migrate_rating_system()
    
    if migration_ok:
        # Test migration
        test_ok = test_migration()
        
        print("\n📊 Migration Results")
        print("=" * 30)
        print(f"Migration: {'✅ Success' if migration_ok else '❌ Failed'}")
        print(f"Test: {'✅ Success' if test_ok else '❌ Failed'}")
        
        if migration_ok and test_ok:
            print("\n🎉 Database successfully migrated to support 1-5 star ratings!")
            print("💡 You can now use the new rating system in Telegram messages")
        else:
            print("\n⚠️  Migration completed but test failed")
    else:
        print("\n❌ Migration failed")

if __name__ == "__main__":
    main() 