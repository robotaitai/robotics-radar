"""
NLP module for Robotics Radar.
Handles keyword extraction and topic analysis using spaCy.
"""

import logging
import spacy
from typing import List, Dict, Set, Optional
import re
from collections import Counter
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KeywordExtractor:
    """Extract keywords and topics from tweet content using NLP."""
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """Initialize keyword extractor.
        
        Args:
            model_name: spaCy model to use
        """
        try:
            self.nlp = spacy.load(model_name)
            logger.info(f"Loaded spaCy model: {model_name}")
        except OSError:
            logger.warning(f"Model {model_name} not found. Please install with: python -m spacy download {model_name}")
            # Fallback to basic processing
            self.nlp = None
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text using NLP.
        
        Args:
            text: Input text to analyze
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of extracted keywords
        """
        if not self.nlp:
            return self._basic_keyword_extraction(text, max_keywords)
        
        try:
            # Process text with spaCy
            doc = self.nlp(text.lower())
            
            # Extract relevant tokens
            keywords = []
            for token in doc:
                # Filter for nouns, proper nouns, and technical terms
                if (token.pos_ in ['NOUN', 'PROPN'] and 
                    not token.is_stop and 
                    not token.is_punct and
                    len(token.text) > 2 and
                    not token.text.startswith('@') and
                    not token.text.startswith('#')):
                    
                    # Lemmatize the token
                    keyword = token.lemma_.lower()
                    if keyword not in keywords:
                        keywords.append(keyword)
            
            # Limit to max_keywords
            return keywords[:max_keywords]
            
        except Exception as e:
            logger.error(f"Error extracting keywords with spaCy: {e}")
            return self._basic_keyword_extraction(text, max_keywords)
    
    def _basic_keyword_extraction(self, text: str, max_keywords: int = 10) -> List[str]:
        """Basic keyword extraction without spaCy.
        
        Args:
            text: Input text to analyze
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of extracted keywords
        """
        try:
            # Remove URLs, mentions, and hashtags
            text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
            text = re.sub(r'@\w+', '', text)
            text = re.sub(r'#\w+', '', text)
            
            # Split into words and filter
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
            
            # Remove common stop words
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
                'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
                'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
            }
            
            keywords = [word for word in words if word not in stop_words]
            
            # Count frequency and return most common
            word_counts = Counter(keywords)
            return [word for word, count in word_counts.most_common(max_keywords)]
            
        except Exception as e:
            logger.error(f"Error in basic keyword extraction: {e}")
            return []
    
    def extract_topics(self, text: str) -> List[str]:
        """Extract broader topics from text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of extracted topics
        """
        try:
            # Extract specific keywords first
            keywords = self.extract_keywords(text, max_keywords=15)
            
            # Get content-specific topics
            content_topics = self._extract_content_specific_topics(text, keywords)
            
            # Also check for robotics-specific topics but with more specific matching
            robotics_topics = self._extract_robotics_topics(text, keywords)
            
            # Combine and deduplicate
            all_topics = content_topics + robotics_topics
            unique_topics = []
            for topic in all_topics:
                if topic not in unique_topics:
                    unique_topics.append(topic)
            
            # If no specific topics found, add general robotics topics based on content
            if not unique_topics:
                unique_topics = self._extract_general_topics(text, keywords)
            
            # Return top 5 most relevant topics
            return unique_topics[:5]
            
        except Exception as e:
            logger.error(f"Error extracting topics: {e}")
            return ['robotics_general']
    
    def extract_categories(self, text: str) -> List[str]:
        """Extract specific robotics categories from text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of identified categories
        """
        try:
            # Convert to lowercase for matching
            text_lower = text.lower()
            
            # Extract keywords first
            keywords = self.extract_keywords(text, max_keywords=20)
            
            # Define category patterns
            category_patterns = {
                'industrial_automation': [
                    'industrial', 'automation', 'manufacturing', 'factory', 'assembly',
                    'production', 'warehouse', 'logistics', 'supply chain', 'industry 4.0'
                ],
                'educational_robotics': [
                    'education', 'learning', 'teaching', 'student', 'school', 'university',
                    'academic', 'curriculum', 'robotics education', 'stem education'
                ],
                'robotics_ethics': [
                    'ethics', 'ethical', 'responsible', 'safety', 'regulation', 'policy',
                    'governance', 'bias', 'fairness', 'transparency', 'accountability'
                ],
                'agricultural_robotics': [
                    'agriculture', 'farming', 'crop', 'harvest', 'irrigation', 'precision',
                    'agtech', 'agri', 'farm', 'food production', 'horticulture'
                ],
                'medical_robotics': [
                    'medical', 'healthcare', 'surgery', 'hospital', 'patient', 'diagnosis',
                    'treatment', 'rehabilitation', 'prosthetics', 'telemedicine'
                ],
                'autonomous_vehicles': [
                    'autonomous', 'self-driving', 'vehicle', 'car', 'transportation',
                    'mobility', 'av', 'autonomous vehicle', 'driverless'
                ],
                'humanoid_robotics': [
                    'humanoid', 'human-like', 'bipedal', 'anthropomorphic', 'humanoid robot',
                    'android', 'humanoid robotics'
                ],
                'swarm_robotics': [
                    'swarm', 'collective', 'multi-robot', 'distributed', 'coordination',
                    'swarm robotics', 'collective behavior'
                ],
                'soft_robotics': [
                    'soft', 'flexible', 'compliant', 'deformable', 'soft robotics',
                    'soft robot', 'flexible robot'
                ],
                'research_robotics': [
                    'research', 'study', 'experiment', 'investigation', 'analysis',
                    'scientific', 'academic research', 'robotics research'
                ],
                'consumer_robotics': [
                    'consumer', 'home', 'domestic', 'personal', 'household', 'entertainment',
                    'consumer robot', 'home robot'
                ],
                'military_robotics': [
                    'military', 'defense', 'security', 'weapon', 'combat', 'surveillance',
                    'defense robotics', 'military robot'
                ],
                'space_robotics': [
                    'space', 'satellite', 'rover', 'mars', 'nasa', 'spacecraft',
                    'space robotics', 'space robot'
                ],
                'underwater_robotics': [
                    'underwater', 'marine', 'ocean', 'submarine', 'aquatic', 'underwater robot',
                    'marine robotics', 'ocean robotics'
                ],
                'aerial_robotics': [
                    'aerial', 'drone', 'uav', 'quadcopter', 'flying', 'airborne',
                    'aerial robotics', 'drone robotics'
                ],
                'collaborative_robotics': [
                    'collaborative', 'cobot', 'human-robot', 'collaboration', 'cooperation',
                    'collaborative robot', 'cobot'
                ],
                'mobile_robotics': [
                    'mobile', 'navigation', 'localization', 'mapping', 'path planning',
                    'mobile robot', 'autonomous navigation'
                ],
                'robotics_software': [
                    'software', 'algorithm', 'programming', 'code', 'framework', 'library',
                    'robotics software', 'robot software'
                ],
                'robotics_hardware': [
                    'hardware', 'sensor', 'actuator', 'motor', 'controller', 'mechanical',
                    'robotics hardware', 'robot hardware'
                ],
                'ai_robotics': [
                    'ai', 'artificial intelligence', 'machine learning', 'deep learning',
                    'neural network', 'ai robotics', 'intelligent robot'
                ]
            }
            
            # Match categories
            categories = []
            for category, patterns in category_patterns.items():
                for pattern in patterns:
                    if pattern in text_lower:
                        categories.append(category)
                        break  # Found one pattern for this category, move to next
            
            # If no specific categories found, add general
            if not categories:
                categories.append('robotics_general')
            
            return categories[:3]  # Limit to top 3 categories
            
        except Exception as e:
            logger.error(f"Error extracting categories: {e}")
            return ['robotics_general']
    
    def _extract_content_specific_topics(self, text: str, keywords: List[str]) -> List[str]:
        """Extract content-specific topics based on the actual text content.
        
        Args:
            text: Input text
            keywords: Extracted keywords
            
        Returns:
            List of content-specific topics
        """
        text_lower = text.lower()
        topics = []
        
        # Company/Product specific topics
        if any(word in text_lower for word in ['nvidia', 'gpu', 'ai chip']):
            topics.append('ai_hardware')
        if any(word in text_lower for word in ['tesla', 'self-driving', 'autonomous vehicle']):
            topics.append('autonomous_vehicles')
        if any(word in text_lower for word in ['boston dynamics', 'atlas', 'spot']):
            topics.append('humanoid_robots')
        if any(word in text_lower for word in ['spacex', 'nasa', 'space', 'satellite']):
            topics.append('space_robotics')
        if any(word in text_lower for word in ['amazon', 'warehouse', 'logistics']):
            topics.append('logistics_automation')
        
        # Technology specific topics
        if any(word in text_lower for word in ['swarm', 'collective', 'multi-robot']):
            topics.append('swarm_robotics')
        if any(word in text_lower for word in ['soft robot', 'flexible', 'biomimetic']):
            topics.append('soft_robotics')
        if any(word in text_lower for word in ['medical', 'surgical', 'healthcare']):
            topics.append('medical_robotics')
        if any(word in text_lower for word in ['agriculture', 'farming', 'crop']):
            topics.append('agricultural_robotics')
        if any(word in text_lower for word in ['drone', 'uav', 'flying']):
            topics.append('aerial_robotics')
        if any(word in text_lower for word in ['underwater', 'marine', 'ocean']):
            topics.append('marine_robotics')
        
        # Application specific topics
        if any(word in text_lower for word in ['manufacturing', 'factory', 'production']):
            topics.append('industrial_automation')
        if any(word in text_lower for word in ['education', 'learning', 'teaching']):
            topics.append('educational_robotics')
        if any(word in text_lower for word in ['research', 'paper', 'study']):
            topics.append('research_publication')
        if any(word in text_lower for word in ['funding', 'investment', 'startup']):
            topics.append('business_development')
        if any(word in text_lower for word in ['safety', 'regulation', 'ethics']):
            topics.append('robotics_ethics')
        
        # AI/ML specific topics
        if any(word in text_lower for word in ['deep learning', 'neural network', 'transformer']):
            topics.append('deep_learning')
        if any(word in text_lower for word in ['reinforcement learning', 'rl', 'q-learning']):
            topics.append('reinforcement_learning')
        if any(word in text_lower for word in ['computer vision', 'image recognition']):
            topics.append('computer_vision')
        if any(word in text_lower for word in ['natural language', 'nlp', 'language model']):
            topics.append('natural_language_processing')
        
        return topics
    
    def _extract_robotics_topics(self, text: str, keywords: List[str]) -> List[str]:
        """Extract robotics-specific topics with more precise matching.
        
        Args:
            text: Input text
            keywords: Extracted keywords
            
        Returns:
            List of robotics topics
        """
        topics = self._load_robotics_topics()
        text_lower = text.lower()
        matched_topics = []
        
        # More precise matching - require multiple keyword matches
        for topic, keywords_list in topics.items():
            matches = 0
            for keyword in keywords_list:
                if keyword.lower() in text_lower:
                    matches += 1
                    if matches >= 2:  # Require at least 2 keyword matches
                        matched_topics.append(topic)
                        break
        
        return matched_topics
    
    def _extract_general_topics(self, text: str, keywords: List[str]) -> List[str]:
        """Extract general topics when no specific topics are found.
        
        Args:
            text: Input text
            keywords: Extracted keywords
            
        Returns:
            List of general topics
        """
        text_lower = text.lower()
        topics = []
        
        # Basic robotics categorization
        if any(word in text_lower for word in ['robot', 'robotics', 'automation']):
            topics.append('robotics_general')
        
        if any(word in text_lower for word in ['ai', 'artificial intelligence', 'machine learning']):
            topics.append('artificial_intelligence')
        
        if any(word in text_lower for word in ['research', 'study', 'paper', 'development']):
            topics.append('research_development')
        
        if any(word in text_lower for word in ['industry', 'manufacturing', 'production']):
            topics.append('industrial_applications')
        
        if any(word in text_lower for word in ['technology', 'innovation', 'breakthrough']):
            topics.append('technology_innovation')
        
        # Ensure we return at least one topic
        if not topics:
            topics.append('robotics_general')
        
        return topics
    
    def _load_robotics_topics(self) -> Dict[str, List[str]]:
        """Load robotics-specific topic keywords.
        
        Returns:
            Dictionary mapping topics to keyword lists
        """
        return {
            'robotics_research': [
                'research', 'paper', 'study', 'experiment', 'algorithm', 'methodology',
                'innovation', 'breakthrough', 'discovery', 'analysis'
            ],
            'autonomous_systems': [
                'autonomous', 'self-driving', 'autonomous vehicle', 'autonomous robot',
                'autonomous system', 'autonomous navigation', 'autonomous control'
            ],
            'computer_vision': [
                'computer vision', 'image processing', 'object detection', 'recognition',
                'vision system', 'camera', 'sensor', 'perception'
            ],
            'machine_learning': [
                'machine learning', 'deep learning', 'neural network', 'AI', 'artificial intelligence',
                'training', 'model', 'algorithm', 'reinforcement learning'
            ],
            'industrial_robotics': [
                'industrial', 'manufacturing', 'factory', 'automation', 'production',
                'assembly', 'welding', 'painting', 'material handling'
            ],
            'service_robots': [
                'service robot', 'domestic robot', 'household robot', 'cleaning robot',
                'assistance robot', 'care robot', 'companion robot'
            ],
            'medical_robotics': [
                'medical robot', 'surgical robot', 'healthcare robot', 'rehabilitation',
                'prosthetics', 'medical device', 'surgery', 'therapy'
            ],
            'mobile_robotics': [
                'mobile robot', 'wheeled robot', 'legged robot', 'flying robot', 'drone',
                'UAV', 'UGV', 'locomotion', 'navigation'
            ],
            'human_robot_interaction': [
                'human robot interaction', 'HRI', 'collaborative robot', 'cobot',
                'human robot collaboration', 'interface', 'interaction'
            ],
            'soft_robotics': [
                'soft robot', 'soft robotics', 'flexible robot', 'compliant robot',
                'biomimetic', 'bio-inspired', 'elastic', 'deformable'
            ]
        }
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Basic sentiment analysis.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with sentiment scores
        """
        try:
            # Simple keyword-based sentiment analysis
            positive_words = {
                'amazing', 'awesome', 'great', 'excellent', 'outstanding', 'brilliant',
                'innovative', 'breakthrough', 'exciting', 'promising', 'successful',
                'improved', 'better', 'faster', 'stronger', 'efficient', 'effective'
            }
            
            negative_words = {
                'terrible', 'awful', 'bad', 'poor', 'disappointing', 'failed',
                'broken', 'problem', 'issue', 'difficult', 'challenging', 'expensive',
                'slow', 'weak', 'inefficient', 'unreliable'
            }
            
            words = text.lower().split()
            positive_count = sum(1 for word in words if word in positive_words)
            negative_count = sum(1 for word in words if word in negative_words)
            
            total_words = len(words)
            if total_words == 0:
                return {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0}
            
            positive_score = positive_count / total_words
            negative_score = negative_count / total_words
            neutral_score = 1.0 - positive_score - negative_score
            
            return {
                'positive': round(positive_score, 3),
                'negative': round(negative_score, 3),
                'neutral': round(neutral_score, 3)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0}
    
    def extract_entities(self, text: str) -> List[Dict]:
        """Extract named entities from text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of entity dictionaries
        """
        if not self.nlp:
            return []
        
        try:
            doc = self.nlp(text)
            entities = []
            
            for ent in doc.ents:
                entities.append({
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char
                })
            
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return []
    
    def is_robotics_related(self, text: str, config_path: str = "config/keywords.yaml") -> bool:
        """Check if text is robotics-related based on keywords.
        
        Args:
            text: Input text to check
            config_path: Path to keywords configuration file
            
        Returns:
            True if robotics-related, False otherwise
        """
        try:
            # Load configuration
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
            
            keywords = config.get('keywords', [])
            exclude_keywords = config.get('exclude_keywords', [])
            
            text_lower = text.lower()
            
            # Check for exclusion keywords first
            for exclude_keyword in exclude_keywords:
                if exclude_keyword.lower() in text_lower:
                    return False
            
            # Check for inclusion keywords
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return True
            
            # Additional check with extracted topics
            topics = self.extract_topics(text)
            return len(topics) > 0
            
        except Exception as e:
            logger.error(f"Error checking robotics relevance: {e}")
            return False
    
    def get_content_summary(self, text: str) -> Dict:
        """Get comprehensive content analysis summary.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with analysis results
        """
        try:
            return {
                'keywords': self.extract_keywords(text),
                'topics': self.extract_topics(text),
                'sentiment': self.analyze_sentiment(text),
                'entities': self.extract_entities(text),
                'is_robotics_related': self.is_robotics_related(text),
                'word_count': len(text.split()),
                'character_count': len(text)
            }
            
        except Exception as e:
            logger.error(f"Error getting content summary: {e}")
            return {
                'keywords': [],
                'topics': [],
                'sentiment': {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0},
                'entities': [],
                'is_robotics_related': False,
                'word_count': 0,
                'character_count': 0
            } 