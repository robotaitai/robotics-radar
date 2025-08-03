#!/usr/bin/env python3
"""
Multi-source historical data import for Robotics Radar.
Imports historical data from RSS, Reddit, Hacker News, and GitHub sources.
"""

import sys
import os
import time
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.multi_source_scraper import MultiSourceScraper
from storage.database import DatabaseManager

def main():
    """Import historical data from all sources."""
    print("🤖 Robotics Radar - Multi-Source Historical Data Import")
    print("=" * 70)
    print("📅 Importing data from all sources (RSS, Reddit, HN, GitHub)...")
    print("📊 This will add comprehensive content to your database!")
    print()
    
    try:
        # Initialize multi-source scraper
        scraper = MultiSourceScraper()
        db = DatabaseManager()
        
        total_imported = 0
        total_processed = 0
        
        # Show source status
        print("🔍 Available Sources:")
        status = scraper.get_source_status()
        for source_key, info in status.items():
            print(f"  {'✅' if info['enabled'] else '❌'} {info['name']} (weight: {info['weight']})")
        
        print("\n" + "="*70)
        
        # Import from each source
        sources = ['rss', 'reddit', 'hackernews', 'github']
        
        for source in sources:
            if not status[source]['enabled']:
                print(f"⏭️  Skipping {status[source]['name']} (disabled)")
                continue
                
            print(f"\n🔄 Importing from {status[source]['name']}...")
            
            try:
                # Run fetch cycle for this source
                result = scraper.fetch_from_source(source)
                
                imported = result.get('stored_count', 0)
                processed = result.get('total_fetched', 0)
                
                total_imported += imported
                total_processed += processed
                
                print(f"✅ {status[source]['name']}: {imported}/{processed} articles imported")
                
                # Small delay between sources
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error importing from {status[source]['name']}: {e}")
                continue
        
        # Get final database stats
        analytics = db.get_analytics_summary()
        
        print("\n" + "="*70)
        print(f"🎉 Multi-source import completed successfully!")
        print(f"📊 Results: {total_imported}/{total_processed} articles imported")
        print(f"📈 Success rate: {(total_imported/total_processed*100):.1f}%" if total_processed > 0 else "📈 Success rate: N/A")
        print(f"🗄️  Total articles in database: {analytics['total_articles']:,}")
        print(f"👥 Total authors: {analytics['total_authors']:,}")
        print(f"⭐ Average score: {analytics['avg_score']:.2f}")
        
        if total_imported > 0:
            print(f"\n🎉 Your database now contains {total_imported} new articles from all sources!")
            print("💡 You should start receiving more diverse Telegram messages.")
            print("🚀 The dashboard should now show comprehensive analytics.")
        else:
            print(f"\n⚠️  No new articles were imported.")
            print("💡 This might be because the articles already exist in your database.")
        
        # Show source breakdown
        print(f"\n📋 Source Breakdown:")
        for source in sources:
            if status[source]['enabled']:
                print(f"  • {status[source]['name']}: Active")
            else:
                print(f"  • {status[source]['name']}: Disabled")
        
    except KeyboardInterrupt:
        print("\n⚠️  Import interrupted by user")
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 