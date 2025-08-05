#!/usr/bin/env python3
"""
Migration script to add published_at column to articles table.
This tracks when articles have been published to Telegram.
"""

import sqlite3
import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.database import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_published_at_column():
    """Add published_at column to articles table."""
    try:
        db = DatabaseManager()
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if column already exists
            cursor.execute("PRAGMA table_info(articles)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'published_at' not in columns:
                logger.info("Adding published_at column to articles table...")
                cursor.execute("ALTER TABLE articles ADD COLUMN published_at TIMESTAMP NULL")
                conn.commit()
                logger.info("✅ published_at column added successfully")
            else:
                logger.info("✅ published_at column already exists")
                
            # Create index for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles (published_at)")
            conn.commit()
            logger.info("✅ Index created for published_at column")
            
    except Exception as e:
        logger.error(f"Error adding published_at column: {e}")
        return False
    
    return True

def main():
    """Main function."""
    print("🔄 Adding published_at column to articles table...")
    
    if add_published_at_column():
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 