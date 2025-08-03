#!/usr/bin/env python3
"""
RSS Feed Validation Script
Validates all configured RSS feeds to ensure they're working and contain content.
"""

import requests
import feedparser
import yaml
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FeedValidator:
    """Validates RSS feeds for accessibility and content."""
    
    def __init__(self, config_path: str = "config/feeds.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def _load_config(self) -> Dict:
        """Load feeds configuration."""
        try:
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def validate_feed(self, feed_config: Dict) -> Dict:
        """Validate a single RSS feed.
        
        Args:
            feed_config: Feed configuration dictionary
            
        Returns:
            Validation results dictionary
        """
        url = feed_config.get('url', '')
        name = feed_config.get('name', 'Unknown')
        enabled = feed_config.get('enabled', True)
        
        if not enabled:
            return {
                'name': name,
                'url': url,
                'status': 'disabled',
                'accessible': False,
                'has_content': False,
                'item_count': 0,
                'last_updated': None,
                'error': 'Feed is disabled'
            }
        
        logger.info(f"Validating feed: {name} ({url})")
        
        try:
            # Check HTTP accessibility
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse RSS content
            feed = feedparser.parse(response.content)
            
            # Check for parsing errors
            if feed.bozo:
                return {
                    'name': name,
                    'url': url,
                    'status': 'malformed',
                    'accessible': True,
                    'has_content': False,
                    'item_count': 0,
                    'last_updated': None,
                    'error': f'Malformed RSS: {feed.bozo_exception}'
                }
            
            # Count items
            items = feed.entries
            item_count = len(items)
            
            # Check for recent content (within last 30 days)
            recent_items = 0
            latest_date = None
            
            for item in items:
                try:
                    # Try different date fields
                    pub_date = item.get('published_parsed') or item.get('updated_parsed')
                    if pub_date:
                        item_date = datetime(*pub_date[:6])
                        if item_date > datetime.now() - timedelta(days=30):
                            recent_items += 1
                        if not latest_date or item_date > latest_date:
                            latest_date = item_date
                except Exception:
                    continue
            
            # Determine status
            if item_count == 0:
                status = 'no_content'
            elif recent_items == 0:
                status = 'stale'
            else:
                status = 'healthy'
            
            return {
                'name': name,
                'url': url,
                'status': status,
                'accessible': True,
                'has_content': item_count > 0,
                'item_count': item_count,
                'recent_items': recent_items,
                'last_updated': latest_date,
                'error': None
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'name': name,
                'url': url,
                'status': 'inaccessible',
                'accessible': False,
                'has_content': False,
                'item_count': 0,
                'last_updated': None,
                'error': f'HTTP Error: {e}'
            }
        except Exception as e:
            return {
                'name': name,
                'url': url,
                'status': 'error',
                'accessible': False,
                'has_content': False,
                'item_count': 0,
                'last_updated': None,
                'error': f'Unexpected error: {e}'
            }
    
    def validate_all_feeds(self) -> List[Dict]:
        """Validate all configured feeds.
        
        Returns:
            List of validation results
        """
        feeds = self.config.get('feeds', [])
        results = []
        
        logger.info(f"Validating {len(feeds)} feeds...")
        
        for i, feed_config in enumerate(feeds):
            result = self.validate_feed(feed_config)
            results.append(result)
            
            # Progress update
            if (i + 1) % 10 == 0:
                logger.info(f"Validated {i + 1}/{len(feeds)} feeds...")
            
            # Rate limiting
            time.sleep(1)
        
        return results
    
    def generate_report(self, results: List[Dict]) -> str:
        """Generate a human-readable validation report.
        
        Args:
            results: List of validation results
            
        Returns:
            Formatted report string
        """
        total_feeds = len(results)
        healthy_feeds = len([r for r in results if r['status'] == 'healthy'])
        problematic_feeds = total_feeds - healthy_feeds
        
        report = f"""
🤖 RSS Feed Validation Report
{'=' * 50}

📊 Summary:
- Total feeds: {total_feeds}
- Healthy feeds: {healthy_feeds} ✅
- Problematic feeds: {problematic_feeds} ⚠️
- Success rate: {(healthy_feeds/total_feeds)*100:.1f}%

"""
        
        # Group by status
        status_groups = {}
        for result in results:
            status = result['status']
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(result)
        
        # Report by status
        for status, feeds in status_groups.items():
            status_emoji = {
                'healthy': '✅',
                'stale': '⚠️',
                'no_content': '❌',
                'inaccessible': '🚫',
                'malformed': '🔧',
                'disabled': '⏸️',
                'error': '💥'
            }.get(status, '❓')
            
            report += f"\n{status_emoji} {status.upper()} ({len(feeds)} feeds):\n"
            
            for feed in feeds:
                report += f"  • {feed['name']}\n"
                if feed['error']:
                    report += f"    Error: {feed['error']}\n"
                elif feed['status'] == 'healthy':
                    report += f"    Items: {feed['item_count']} (recent: {feed['recent_items']})\n"
                elif feed['status'] == 'stale':
                    report += f"    Items: {feed['item_count']} (last updated: {feed['last_updated']})\n"
        
        # Recommendations
        report += f"\n💡 Recommendations:\n"
        
        if problematic_feeds > 0:
            report += f"- Review and fix {problematic_feeds} problematic feeds\n"
            report += "- Consider removing permanently broken feeds\n"
            report += "- Update stale feeds or reduce polling frequency\n"
        else:
            report += "- All feeds are healthy! 🎉\n"
        
        report += f"- Run this validation weekly to maintain feed health\n"
        
        return report
    
    def save_results(self, results: List[Dict], output_file: str = "feed_validation_results.yaml"):
        """Save validation results to file.
        
        Args:
            results: List of validation results
            output_file: Output file path
        """
        try:
            # Convert datetime objects to strings for YAML serialization
            serializable_results = []
            for result in results:
                serializable_result = result.copy()
                if serializable_result['last_updated']:
                    serializable_result['last_updated'] = serializable_result['last_updated'].isoformat()
                serializable_results.append(serializable_result)
            
            with open(output_file, 'w') as file:
                yaml.dump(serializable_results, file, default_flow_style=False, indent=2)
            
            logger.info(f"Results saved to {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")

def main():
    """Main validation function."""
    print("🔍 RSS Feed Validator")
    print("=" * 50)
    
    validator = FeedValidator()
    results = validator.validate_all_feeds()
    
    # Generate and print report
    report = validator.generate_report(results)
    print(report)
    
    # Save results
    validator.save_results(results)
    
    # Exit with error code if there are problematic feeds
    problematic_count = len([r for r in results if r['status'] != 'healthy'])
    if problematic_count > 0:
        print(f"\n⚠️  Found {problematic_count} problematic feeds. Please review and fix.")
        exit(1)
    else:
        print("\n✅ All feeds are healthy!")
        exit(0)

if __name__ == "__main__":
    main() 