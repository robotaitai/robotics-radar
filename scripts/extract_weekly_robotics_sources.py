#!/usr/bin/env python3
"""
Extract sources from Weekly Robotics issues to find high-quality robotics content sources.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from collections import Counter
import time
import yaml

def extract_weekly_robotics_sources():
    """Extract all sources from Weekly Robotics issues."""
    base_url = "https://www.weeklyrobotics.com/"
    issues = [f"weekly-robotics-{i}" for i in range(275, 325)]  # Last 50 issues
    domains_counter = Counter()
    
    print("🔍 Extracting sources from Weekly Robotics issues...")
    print(f"📅 Analyzing {len(issues)} issues (275-324)")
    
    for i, issue in enumerate(issues):
        try:
            print(f"  📖 Processing {issue}... ({i+1}/{len(issues)})")
            res = requests.get(base_url + issue, timeout=10)
            soup = BeautifulSoup(res.content, "html.parser")
            links = soup.find_all("a", href=True)
            
            for link in links:
                url = link["href"]
                parsed = urlparse(url)
                domain = parsed.netloc.replace('www.', '')
                
                if domain and 'weeklyrobotics.com' not in domain:
                    domains_counter[domain] += 1
            
            # Small delay to be respectful
            time.sleep(1)
            
        except Exception as e:
            print(f"    ❌ Error processing {issue}: {e}")
            continue
    
    print(f"\n📊 Found {len(domains_counter)} unique domains")
    print("🏆 Top 50 most frequent sources:")
    print("=" * 60)
    
    for domain, count in domains_counter.most_common(50):
        print(f"{domain}: {count}")
    
    return domains_counter

def identify_rss_feeds(domains_counter):
    """Identify which domains likely have RSS feeds."""
    print(f"\n🔍 Identifying RSS feed candidates...")
    print("=" * 60)
    
    rss_candidates = []
    
    # Common RSS feed patterns
    rss_patterns = [
        '/feed',
        '/rss',
        '/atom',
        '/xml',
        '/blog/feed',
        '/news/feed',
        '/articles/feed'
    ]
    
    for domain, count in domains_counter.most_common(30):  # Check top 30
        print(f"🔍 Checking {domain} (mentioned {count} times)...")
        
        # Try common RSS patterns
        for pattern in rss_patterns:
            try:
                test_url = f"https://{domain}{pattern}"
                res = requests.get(test_url, timeout=5)
                
                if res.status_code == 200 and ('xml' in res.headers.get('content-type', '') or 'rss' in res.headers.get('content-type', '')):
                    print(f"  ✅ Found RSS: {test_url}")
                    rss_candidates.append({
                        'domain': domain,
                        'url': test_url,
                        'frequency': count,
                        'pattern': pattern
                    })
                    break
                    
            except Exception as e:
                continue
        
        # Small delay
        time.sleep(0.5)
    
    return rss_candidates

def generate_feeds_config(rss_candidates):
    """Generate a feeds configuration from the found RSS feeds."""
    print(f"\n📝 Generating feeds configuration...")
    print("=" * 60)
    
    feeds = []
    
    for candidate in rss_candidates:
        feed_config = {
            'name': f"Weekly Robotics - {candidate['domain']}",
            'url': candidate['url'],
            'tags': ['weekly-robotics', 'robotics'],
            'enabled': True,
            'weight': min(candidate['frequency'], 10)  # Cap weight at 10
        }
        feeds.append(feed_config)
        print(f"  ✅ Added: {candidate['domain']} (weight: {feed_config['weight']})")
    
    return feeds

def main():
    """Main function to extract and analyze Weekly Robotics sources."""
    print("🤖 Weekly Robotics Source Extractor")
    print("=" * 60)
    
    # Extract sources
    domains_counter = extract_weekly_robotics_sources()
    
    # Identify RSS feeds
    rss_candidates = identify_rss_feeds(domains_counter)
    
    if rss_candidates:
        # Generate feeds configuration
        feeds = generate_feeds_config(rss_candidates)
        
        # Save to file
        config = {
            'name': 'Weekly Robotics Sources',
            'description': 'High-quality robotics sources extracted from Weekly Robotics issues',
            'feeds': feeds
        }
        
        with open('config/weekly_robotics_sources.yaml', 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        print(f"\n💾 Saved {len(feeds)} feeds to config/weekly_robotics_sources.yaml")
        print("🎉 You can now add these feeds to your main feeds.yaml configuration!")
        
    else:
        print("\n❌ No RSS feeds found. You may need to manually check the top domains.")
    
    # Show top domains for manual investigation
    print(f"\n🔍 Top 20 domains for manual RSS investigation:")
    print("=" * 60)
    for domain, count in domains_counter.most_common(20):
        print(f"  • {domain} ({count} mentions)")

if __name__ == "__main__":
    main() 