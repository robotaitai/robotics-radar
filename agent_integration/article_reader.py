"""
Offline Article Reader Agent for Robotics Radar.
Reads article content from URLs and generates intelligent summaries.
"""

import requests
import logging
import re
from typing import Optional, Dict, List
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlp.keyword_extraction import KeywordExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArticleReader:
    """Offline agent for reading and summarizing articles."""
    
    def __init__(self):
        """Initialize the article reader."""
        self.keyword_extractor = KeywordExtractor()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def read_article(self, url: str) -> Optional[Dict]:
        """Read and analyze an article from a URL.
        
        Args:
            url: Article URL to read
            
        Returns:
            Dictionary with article content and analysis, or None if failed
        """
        try:
            logger.info(f"Reading article: {url}")
            
            # Fetch the article
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract article content
            article_data = self._extract_article_content(soup, url)
            
            if not article_data:
                logger.warning(f"Could not extract content from {url}")
                return None
            
            # Generate intelligent summary
            summary = self._generate_intelligent_summary(article_data)
            
            # Extract key insights
            insights = self._extract_key_insights(article_data)
            
            return {
                'url': url,
                'title': article_data.get('title', ''),
                'content': article_data.get('content', ''),
                'summary': summary,
                'insights': insights,
                'word_count': len(article_data.get('content', '').split()),
                'topics': article_data.get('topics', []),
                'source': self._extract_source(url)
            }
            
        except Exception as e:
            logger.error(f"Error reading article {url}: {e}")
            return None
    
    def _extract_article_content(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """Extract article content from HTML.
        
        Args:
            soup: BeautifulSoup object
            url: Article URL for context
            
        Returns:
            Dictionary with extracted content
        """
        try:
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
            
            # Extract title
            title = ""
            title_selectors = [
                'h1',
                'title',
                '[class*="title"]',
                '[class*="headline"]',
                'h1[class*="title"]',
                'h1[class*="headline"]'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text().strip()
                    break
            
            # Extract main content
            content = ""
            content_selectors = [
                'article',
                '[class*="content"]',
                '[class*="article"]',
                '[class*="post"]',
                '[class*="entry"]',
                'main',
                '.post-content',
                '.article-content',
                '.entry-content'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Get paragraphs
                    paragraphs = content_elem.find_all(['p', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    content = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                    break
            
            # If no specific content area found, try body
            if not content:
                body = soup.find('body')
                if body:
                    paragraphs = body.find_all('p')
                    content = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            
            # Clean up content
            content = self._clean_text(content)
            
            if not content or len(content) < 100:
                return None
            
            # Extract topics
            topics = self.keyword_extractor.extract_topics(f"{title} {content}")
            
            return {
                'title': title,
                'content': content,
                'topics': topics
            }
            
        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might cause issues
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)
        
        return text.strip()
    
    def _generate_intelligent_summary(self, article_data: Dict) -> str:
        """Generate an intelligent summary of the article.
        
        Args:
            article_data: Article content and metadata
            
        Returns:
            Generated summary
        """
        try:
            title = article_data.get('title', '')
            content = article_data.get('content', '')
            topics = article_data.get('topics', [])
            
            # Clean content first
            clean_content = self._clean_text(content)
            
            # Split content into sentences
            sentences = re.split(r'[.!?]+', clean_content)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            # Score sentences based on relevance and filter out metadata
            scored_sentences = []
            for sentence in sentences[:20]:  # Limit to first 20 sentences
                # Skip metadata sentences
                if self._is_metadata_sentence(sentence):
                    continue
                
                # Skip very short sentences
                if len(sentence) < 20:
                    continue
                
                score = 0
                
                # Score based on topic keywords
                for topic in topics:
                    if topic.lower() in sentence.lower():
                        score += 2
                
                # Score based on technical terms
                tech_terms = ['robot', 'robotics', 'AI', 'artificial intelligence', 'automation', 
                            'machine learning', 'computer vision', 'autonomous', 'sensor', 'algorithm']
                for term in tech_terms:
                    if term.lower() in sentence.lower():
                        score += 1
                
                # Score based on sentence position (earlier = higher)
                position_score = max(0, 10 - len(scored_sentences))
                score += position_score
                
                scored_sentences.append((sentence, score))
            
            # Sort by score and take top 2 sentences
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            top_sentences = [s[0] for s in scored_sentences[:2]]
            
            # Generate summary
            if top_sentences:
                summary = '. '.join(top_sentences) + '.'
                summary = summary[:180] + "..." if len(summary) > 180 else summary
                
                # Add context based on title
                if "breakthrough" in title.lower() or "new" in title.lower():
                    summary = f"🚀 {summary}"
                elif "research" in title.lower() or "study" in title.lower():
                    summary = f"🔬 {summary}"
                elif "announcement" in title.lower() or "launch" in title.lower():
                    summary = f"📢 {summary}"
                else:
                    summary = f"📰 {summary}"
                
                return summary
            else:
                return f"📰 {title[:150]}..."
                
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"📰 {title[:150]}..."
    
    def _is_metadata_sentence(self, sentence: str) -> bool:
        """Check if a sentence is metadata rather than content.
        
        Args:
            sentence: Sentence to check
            
        Returns:
            True if it's metadata
        """
        metadata_patterns = [
            r'^Source:',
            r'^Credit:',
            r'^Image:',
            r'^<img',
            r'^A computer-generated',
            r'^AI-generated',
            r'^This image shows',
            r'^The image depicts',
            r'^Photo:',
            r'^Picture:',
            r'^Source\s*:',
            r'^Credit\s*:',
            r'^Image\s*:',
            r'^Photo\s*:',
            r'^Picture\s*:'
        ]
        
        sentence_lower = sentence.lower()
        
        for pattern in metadata_patterns:
            if re.search(pattern, sentence_lower):
                return True
        
        return False
    
    def _extract_key_insights(self, article_data: Dict) -> List[str]:
        """Extract key insights from the article.
        
        Args:
            article_data: Article content and metadata
            
        Returns:
            List of key insights
        """
        try:
            content = article_data.get('content', '')
            insights = []
            
            # Look for key phrases that indicate insights
            insight_patterns = [
                r'([^.]*?(?:breakthrough|innovation|discovery|advancement|milestone)[^.]*)',
                r'([^.]*?(?:enables|allows|improves|enhances|reduces)[^.]*)',
                r'([^.]*?(?:first time|never before|revolutionary|game-changing)[^.]*)',
                r'([^.]*?(?:cost|efficiency|accuracy|speed|performance)[^.]*)'
            ]
            
            for pattern in insight_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches[:2]:  # Limit to 2 matches per pattern
                    clean_match = match.strip()
                    if len(clean_match) > 20 and len(clean_match) < 200:
                        insights.append(clean_match)
            
            return insights[:5]  # Return top 5 insights
            
        except Exception as e:
            logger.error(f"Error extracting insights: {e}")
            return []
    
    def _extract_source(self, url: str) -> str:
        """Extract source name from URL.
        
        Args:
            url: Article URL
            
        Returns:
            Source name
        """
        try:
            domain = urlparse(url).netloc
            source = domain.replace('www.', '').split('.')[0]
            return source.title()
        except:
            return "Unknown"
    
    def enhance_tweet_summary(self, tweet) -> str:
        """Enhance a tweet's summary by reading the actual article.
        
        Args:
            tweet: Tweet object with URL
            
        Returns:
            Enhanced summary
        """
        try:
            # Read the article
            article_data = self.read_article(tweet.url)
            
            if article_data and article_data.get('summary'):
                return article_data['summary']
            else:
                # Fallback to original summary
                return tweet.summary or "No summary available"
                
        except Exception as e:
            # Don't log errors for blocked requests - this is expected
            if "403" not in str(e) and "429" not in str(e):
                logger.debug(f"Error enhancing summary for {tweet.url}: {e}")
            return tweet.summary or "No summary available"
    
    def batch_enhance_summaries(self, tweets: List) -> List:
        """Enhance summaries for a batch of tweets.
        
        Args:
            tweets: List of tweet objects
            
        Returns:
            List of tweets with enhanced summaries
        """
        enhanced_tweets = []
        
        for tweet in tweets:
            try:
                # Add small delay to be respectful to servers
                time.sleep(1)
                
                enhanced_summary = self.enhance_tweet_summary(tweet)
                tweet.summary = enhanced_summary
                enhanced_tweets.append(tweet)
                
            except Exception as e:
                logger.error(f"Error enhancing tweet {tweet.id}: {e}")
                enhanced_tweets.append(tweet)
        
        return enhanced_tweets


def main():
    """Test the article reader."""
    reader = ArticleReader()
    
    # Test with a sample URL
    test_url = "https://www.therobotreport.com/beyond-assembly-line-swarm-robotics-emerge/"
    
    print(f"Testing article reader with: {test_url}")
    result = reader.read_article(test_url)
    
    if result:
        print(f"✅ Successfully read article")
        print(f"Title: {result['title']}")
        print(f"Summary: {result['summary']}")
        print(f"Word count: {result['word_count']}")
        print(f"Topics: {result['topics']}")
        print(f"Insights: {result['insights'][:2]}")
    else:
        print("❌ Failed to read article")


if __name__ == "__main__":
    main() 