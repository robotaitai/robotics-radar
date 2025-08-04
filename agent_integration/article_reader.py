"""
Enhanced Offline Article Reader Agent for Robotics Radar.
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
    """Enhanced offline agent for reading and summarizing articles."""
    
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
        """Read and analyze an article from a URL."""
        try:
            logger.info(f"Reading article: {url}")
            
            # Fetch the article
            response = self.session.get(url, timeout=15)
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
                'source': self._extract_source(url),
                'meta_description': article_data.get('meta_description', '')
            }
            
        except Exception as e:
            logger.error(f"Error reading article {url}: {e}")
            return None
    
    def _extract_article_content(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """Extract article content with multiple fallback methods."""
        try:
            # Method 1: Try specialized extraction patterns
            content = self._extract_with_patterns(soup)
            
            # Method 2: Try meta description as fallback
            if not content or len(content) < 200:
                meta_desc = self._extract_meta_description(soup)
                if meta_desc and len(meta_desc) > 50:
                    logger.info(f"Using meta description as fallback for {url}")
                    content = meta_desc
            
            # Method 3: Try newspaper3k-style extraction
            if not content or len(content) < 200:
                content = self._extract_newspaper_style(soup)
            
            # Extract title
            title = self._extract_title(soup)
            
            # Extract meta description
            meta_description = self._extract_meta_description(soup)
            
            # Clean and validate content
            if content and len(content) > 100:
                clean_content = self._clean_text_enhanced(content)
                return {
                    'title': title,
                    'content': clean_content,
                    'meta_description': meta_description,
                    'topics': self._extract_topics(clean_content)
                }
            
            logger.warning(f"Content extraction failed for {url}")
            return None
            
        except Exception as e:
            logger.error(f"Error in content extraction: {e}")
            return None
    
    def _extract_with_patterns(self, soup: BeautifulSoup) -> str:
        """Extract content using common article patterns."""
        content_parts = []
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form', 'button']):
            element.decompose()
        
        # Remove elements with unwanted classes/IDs
        unwanted_patterns = [
            'comment', 'related', 'sidebar', 'advertisement', 'social', 'share',
            'menu', 'navigation', 'footer', 'header', 'cookie', 'popup'
        ]
        
        for pattern in unwanted_patterns:
            for element in soup.find_all(attrs={'class': re.compile(pattern, re.I)}):
                element.decompose()
            for element in soup.find_all(attrs={'id': re.compile(pattern, re.I)}):
                element.decompose()
        
        # Try article-specific selectors
        selectors = [
            'article',
            '[class*="article"]',
            '[class*="content"]',
            '[class*="post"]',
            '[class*="entry"]',
            'main',
            '.post-content',
            '.entry-content',
            '.article-content',
            '.story-content'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(separator=' ', strip=True)
                if len(text) > 200:
                    content_parts.append(text)
        
        # If no article-specific content found, try body content
        if not content_parts:
            body = soup.find('body')
            if body:
                # Get all text elements
                for tag in body.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote']):
                    text = tag.get_text(strip=True)
                    if len(text) > 20 and not self._is_metadata_text(text):
                        content_parts.append(text)
        
        return ' '.join(content_parts)
    
    def _extract_newspaper_style(self, soup: BeautifulSoup) -> str:
        """Extract content using newspaper3k-style heuristics."""
        content_parts = []
        
        # Score paragraphs by various heuristics
        paragraphs = soup.find_all(['p', 'div'])
        scored_paragraphs = []
        
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) < 50:
                continue
                
            score = 0
            
            # Length bonus
            score += min(len(text) / 10, 10)
            
            # Link density penalty
            links = p.find_all('a')
            if links:
                link_density = len(links) / len(text.split())
                score -= link_density * 50
            
            # Class/ID bonuses
            if p.get('class'):
                class_text = ' '.join(p.get('class')).lower()
                if any(word in class_text for word in ['content', 'article', 'post', 'text']):
                    score += 20
            
            # Position bonus (earlier = higher)
            score += max(0, 10 - len(scored_paragraphs))
            
            scored_paragraphs.append((text, score))
        
        # Sort by score and take top paragraphs
        scored_paragraphs.sort(key=lambda x: x[1], reverse=True)
        
        for text, score in scored_paragraphs[:10]:
            if score > 5:
                content_parts.append(text)
        
        return ' '.join(content_parts)
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title."""
        # Try multiple title sources
        title_selectors = [
            'h1',
            'title',
            '[class*="title"]',
            '[class*="headline"]',
            'meta[property="og:title"]',
            'meta[name="twitter:title"]'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True) if element.name != 'meta' else element.get('content', '')
                if title and len(title) > 10:
                    return title
        
        return ""
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description."""
        meta_selectors = [
            'meta[name="description"]',
            'meta[property="og:description"]',
            'meta[name="twitter:description"]'
        ]
        
        for selector in meta_selectors:
            element = soup.select_one(selector)
            if element:
                desc = element.get('content', '')
                if desc and len(desc) > 20:
                    return desc
        
        return ""
    
    def _is_metadata_text(self, text: str) -> bool:
        """Check if text is metadata rather than content."""
        metadata_patterns = [
            r'^Source:', r'^Credit:', r'^Image:', r'^Photo:', r'^Picture:',
            r'^A computer-generated', r'^AI-generated', r'^This image shows',
            r'^The image depicts', r'^Click here', r'^Read more',
            r'^Share this', r'^Follow us', r'^Subscribe', r'^Newsletter'
        ]
        
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in metadata_patterns)
    
    def _clean_text_enhanced(self, text: str) -> str:
        """Enhanced text cleaning that preserves important punctuation."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common metadata patterns
        text = re.sub(r'Source:\s*[^.]*\.', '', text)
        text = re.sub(r'Credit:\s*[^.]*\.', '', text)
        text = re.sub(r'Image:\s*[^.]*\.', '', text)
        
        # Preserve Unicode characters and punctuation
        text = text.strip()
        
        return text
    
    def _generate_intelligent_summary(self, article_data: Dict) -> str:
        """Generate intelligent summary using advanced techniques."""
        try:
            content = article_data.get('content', '')
            title = article_data.get('title', '')
            meta_description = article_data.get('meta_description', '')
            
            if not content:
                return f"📰 {title[:150]}..."
            
            # Split content into sentences
            sentences = re.split(r'[.!?]+', content)
            sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]
            
            if len(sentences) < 3:
                return f"📰 {title[:150]}..."
            
            # Score sentences based on relevance
            scored_sentences = []
            for sentence in sentences[:10]:  # Look at first 10 sentences
                score = 0
                
                # Score based on robotics keywords
                robotics_keywords = ['robot', 'robotics', 'ai', 'artificial intelligence', 'automation', 
                                   'machine learning', 'computer vision', 'autonomous', 'sensor', 'algorithm']
                for keyword in robotics_keywords:
                    if keyword.lower() in sentence.lower():
                        score += 2
                
                # Score based on technical terms
                tech_terms = ['system', 'technology', 'development', 'research', 'study', 'experiment']
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
                
                # Truncate if too long
                if len(summary) > 200:
                    summary = summary[:200] + "..."
                
                # Add emoji based on content
                summary = self._add_content_emoji(summary, title)
                
                return summary
            else:
                # Fallback to meta description
                if meta_description and len(meta_description) > 50:
                    return f"📰 {meta_description[:200]}..."
                else:
                    return f"📰 {title[:150]}..."
                    
        except Exception as e:
            logger.error(f"Error generating intelligent summary: {e}")
            return f"📰 {title[:150]}..."
    
    def _add_content_emoji(self, summary: str, title: str) -> str:
        """Add appropriate emoji based on content."""
        text_lower = (summary + ' ' + title).lower()
        
        if any(word in text_lower for word in ['breakthrough', 'novel', 'revolutionary', 'first']):
            return f"🚀 {summary}"
        elif any(word in text_lower for word in ['research', 'study', 'experiment', 'paper']):
            return f"🔬 {summary}"
        elif any(word in text_lower for word in ['announcement', 'launch', 'release']):
            return f"📢 {summary}"
        elif any(word in text_lower for word in ['improvement', 'better', 'faster', 'enhanced']):
            return f"⚡ {summary}"
        else:
            return f"📰 {summary}"
    
    def _extract_key_insights(self, article_data: Dict) -> List[str]:
        """Extract key insights from article content."""
        insights = []
        content = article_data.get('content', '')
        
        if not content:
            return insights
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]
        
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
    
    def _extract_topics(self, content: str) -> List[str]:
        """Extract topics from content."""
        try:
            return self.keyword_extractor.extract_topics(content)
        except Exception as e:
            logger.error(f"Error extracting topics: {e}")
            return []
    
    def _extract_source(self, url: str) -> str:
        """Extract source domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '')
            return domain
        except Exception:
            return "unknown"
    
    def enhance_tweet_summary(self, tweet) -> str:
        """Legacy method for backward compatibility."""
        try:
            # Extract URL from tweet
            url = getattr(tweet, 'url', None)
            if not url:
                return getattr(tweet, 'text', '')[:150] + "..."
            
            # Read article and generate enhanced summary
            article_data = self.read_article(url)
            if article_data:
                return article_data['summary']
            else:
                return getattr(tweet, 'text', '')[:150] + "..."
                
        except Exception as e:
            logger.error(f"Error enhancing tweet summary: {e}")
            return getattr(tweet, 'text', '')[:150] + "..."
    
    def batch_enhance_summaries(self, tweets: List) -> List:
        """Legacy method for batch processing."""
        enhanced_tweets = []
        
        for tweet in tweets:
            try:
                enhanced_summary = self.enhance_tweet_summary(tweet)
                tweet.enhanced_summary = enhanced_summary
                enhanced_tweets.append(tweet)
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error enhancing tweet {getattr(tweet, 'id', 'unknown')}: {e}")
                enhanced_tweets.append(tweet)
        
        return enhanced_tweets 