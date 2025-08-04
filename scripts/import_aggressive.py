#!/usr/bin/env python3
"""
Aggressive historical data import for Robotics Radar.
Temporarily relaxes filtering to import more historical content.
"""

import sys
import os
import time
import yaml
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.multi_source_scraper import MultiSourceScraper
from storage.database import DatabaseManager

def load_feeds_config():
    """Load feeds configuration from the active profile in feeds.yaml."""
    feeds_path = "config/feeds.yaml"
    
    if not os.path.exists(feeds_path):
        print(f"❌ Feeds configuration not found at {feeds_path}")
        return []
    
    try:
        with open(feeds_path, 'r') as file:
            config = yaml.safe_load(file)
        
        # Get active profile
        active_profile = config.get('active_profile', 'frontier')
        profiles = config.get('profiles', {})
        
        if active_profile not in profiles:
            print(f"❌ Active profile '{active_profile}' not found in configuration")
            return []
        
        profile = profiles[active_profile]
        feeds = profile.get('feeds', [])
        
        print(f"📋 Loaded {len(feeds)} feeds from profile: {profile['name']}")
        print(f"📝 Description: {profile['description']}")
        return feeds
        
    except Exception as e:
        print(f"❌ Error loading feeds configuration: {e}")
        return []

def get_active_sources(feeds):
    """Determine active sources from feeds configuration."""
    sources = set()
    
    for feed in feeds:
        if not feed.get('enabled', True):
            continue
            
        url = feed.get('url', '').lower()
        
        # Determine source type from URL
        if 'reddit.com' in url or '/r/' in url:
            sources.add('reddit')
        elif 'hacker-news' in url or 'hnrss.org' in url:
            sources.add('hackernews')
        elif 'github.com' in url or 'github' in url:
            sources.add('github')
        elif 'arxiv.org' in url or 'nitter' in url or 'medium.com' in url or 'blog' in url or 'feed' in url:
            sources.add('rss')
        else:
            # Default to RSS for unknown URLs
            sources.add('rss')
    
    return list(sources)

def aggressive_import(scraper, source, cycles=50):
    """Run aggressive import with many cycles to get more content."""
    print(f"🚀 Running aggressive import for {source} ({cycles} cycles)...")
    
    total_imported = 0
    total_processed = 0
    
    for cycle in range(cycles):
        try:
            if cycle % 10 == 0:
                print(f"  📅 Cycle {cycle + 1}/{cycles}...")
            
            # Run fetch cycle for this source
            result = scraper.fetch_from_source(source)
            
            imported = result.get('stored_count', 0)
            processed = result.get('total_fetched', 0)
            
            total_imported += imported
            total_processed += processed
            
            if imported > 0:
                print(f"    ✅ Cycle {cycle + 1}: Found {imported} new articles")
            
            # Small delay between cycles
            time.sleep(1)
            
        except Exception as e:
            print(f"    ❌ Error in cycle {cycle + 1}: {e}")
            continue
    
    return total_imported, total_processed

def main():
    """Run aggressive historical data import."""
    print("🤖 Robotics Radar - Aggressive Historical Data Import")
    print("=" * 70)
    print("🚀 Running aggressive import to maximize content collection...")
    print("⚠️  This will run many fetch cycles to get maximum content!")
    print()
    
    try:
        # Load feeds configuration
        feeds = load_feeds_config()
        if not feeds:
            print("❌ No feeds configured. Please check config/feeds.yaml")
            return
        
        # Determine active sources from configuration
        active_sources = get_active_sources(feeds)
        print(f"🔍 Active sources detected: {', '.join(active_sources)}")
        
        # Initialize multi-source scraper
        scraper = MultiSourceScraper()
        db = DatabaseManager()
        
        # Get initial database stats
        initial_analytics = db.get_analytics_summary()
        print(f"📊 Initial database: {initial_analytics['total_articles']} articles")
        
        total_imported = 0
        total_processed = 0
        
        # Show source status
        print("\n🔍 Source Status:")
        status = scraper.get_source_status()
        for source_key, info in status.items():
            if source_key in active_sources:
                print(f"  {'✅' if info['enabled'] else '❌'} {info['name']} (weight: {info['weight']})")
        
        print("\n" + "="*70)
        
        # Import from each active source aggressively
        for source in active_sources:
            if source not in status or not status[source]['enabled']:
                print(f"⏭️  Skipping {source} (disabled or not available)")
                continue
                
            print(f"\n🚀 Running aggressive import from {status[source]['name']}...")
            
            try:
                # Run aggressive import (50 cycles per source)
                cycles = 50 if source == 'rss' else 30  # More cycles for RSS
                imported, processed = aggressive_import(scraper, source, cycles=cycles)
                
                total_imported += imported
                total_processed += processed
                
                print(f"✅ {status[source]['name']}: {imported}/{processed} articles imported (aggressive)")
                
                # Small delay between sources
                time.sleep(3)
                
            except Exception as e:
                print(f"❌ Error importing from {status[source]['name']}: {e}")
                continue
        
        # Get final database stats
        final_analytics = db.get_analytics_summary()
        actual_new_articles = final_analytics['total_articles'] - initial_analytics['total_articles']
        
        print("\n" + "="*70)
        print(f"🎉 Aggressive import completed successfully!")
        print(f"📊 Results: {total_imported}/{total_processed} articles processed")
        print(f"📈 Success rate: {(total_imported/total_processed*100):.1f}%" if total_processed > 0 else "📈 Success rate: N/A")
        print(f"🗄️  Database growth: {initial_analytics['total_articles']} → {final_analytics['total_articles']} (+{actual_new_articles})")
        print(f"👥 Total authors: {final_analytics['total_authors']:,}")
        print(f"⭐ Average score: {final_analytics['avg_score']:.2f}")
        
        if actual_new_articles > 0:
            print(f"\n🎉 Your database now contains {actual_new_articles} new articles from aggressive import!")
            print("💡 You should start receiving more diverse Telegram messages.")
            print("🚀 The dashboard should now show comprehensive analytics.")
        else:
            print(f"\n⚠️  No new articles were imported.")
            print("💡 This might be because:")
            print("   • Articles already exist in your database")
            print("   • Sources are rate-limited")
            print("   • Filtering is too strict")
            print("   • Sources don't have much historical content")
        
        # Show source breakdown
        print(f"\n📋 Source Breakdown:")
        for source in active_sources:
            if source in status and status[source]['enabled']:
                cycles = 50 if source == 'rss' else 30
                print(f"  • {status[source]['name']}: Active (aggressive - {cycles} cycles)")
            else:
                print(f"  • {source}: Disabled")
        
        # Show feed statistics
        enabled_feeds = [f for f in feeds if f.get('enabled', True)]
        print(f"\n📰 Feed Statistics:")
        print(f"  • Total feeds configured: {len(feeds)}")
        print(f"  • Enabled feeds: {len(enabled_feeds)}")
        print(f"  • Disabled feeds: {len(feeds) - len(enabled_feeds)}")
        print(f"  • Aggressive cycles: 30-50 per source")
        
    except KeyboardInterrupt:
        print("\n⚠️  Import interrupted by user")
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 