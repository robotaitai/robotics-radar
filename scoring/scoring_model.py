"""
Scoring model for Robotics Radar.
Calculates tweet scores based on engagement metrics and user feedback.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
import yaml
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScoringWeights:
    """Configuration for scoring weights."""
    likes: float = 1.0
    retweets: float = 2.0
    replies: float = 1.5
    user_feedback: float = 3.0
    author_followers: float = 0.1
    content_length: float = 0.5
    category_weights: Dict[str, float] = None
    user_preferences: Dict[str, float] = None

class ScoringModel:
    """Scoring model for tweets based on engagement and content quality."""
    
    def __init__(self, config_path: str = "config/keywords.yaml"):
        """Initialize scoring model.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.weights = self._load_scoring_weights()
        self.min_thresholds = self._load_thresholds()
        
    def _load_scoring_weights(self) -> ScoringWeights:
        """Load scoring weights from configuration.
        
        Returns:
            ScoringWeights object
        """
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
                
            weights_config = config.get('scoring_weights', {})
            category_weights = config.get('category_weights', {})
            user_preferences = config.get('user_preferences', {})
            
            return ScoringWeights(
                likes=weights_config.get('likes', 1.0),
                retweets=weights_config.get('retweets', 2.0),
                replies=weights_config.get('replies', 1.5),
                user_feedback=weights_config.get('user_feedback', 3.0),
                author_followers=weights_config.get('author_followers', 0.1),
                content_length=weights_config.get('content_length', 0.5),
                category_weights=category_weights,
                user_preferences=user_preferences
            )
            
        except Exception as e:
            logger.warning(f"Error loading scoring weights, using defaults: {e}")
            return ScoringWeights()
    
    def _load_thresholds(self) -> Dict[str, int]:
        """Load minimum thresholds from configuration.
        
        Returns:
            Dictionary with threshold values
        """
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
                
            return {
                'min_likes': config.get('min_likes', 10),
                'min_retweets': config.get('min_retweets', 5),
                'min_author_followers': config.get('min_author_followers', 1000)
            }
            
        except Exception as e:
            logger.warning(f"Error loading thresholds, using defaults: {e}")
            return {
                'min_likes': 10,
                'min_retweets': 5,
                'min_author_followers': 1000
            }
    
    def calculate_base_score(self, tweet_data: Dict) -> float:
        """Calculate base score from engagement metrics.
        
        Args:
            tweet_data: Dictionary containing tweet metrics
            
        Returns:
            Base score value
        """
        try:
            likes = tweet_data.get('likes', 0)
            retweets = tweet_data.get('retweets', 0)
            replies = tweet_data.get('replies', 0)
            author_followers = tweet_data.get('author_followers', 0)
            content_length = len(tweet_data.get('text', ''))
            created_at = tweet_data.get('created_at')
            
            # Calculate recency bonus
            recency_bonus = self._calculate_recency_bonus(created_at)
            
            # For RSS articles (0 likes/retweets), give them a base score
            if likes == 0 and retweets == 0:
                # RSS articles get a base score based on content quality and author
                import math
                author_score = math.log10(max(author_followers, 1)) * self.weights.author_followers
                content_score = min(content_length / 280, 1.0) * self.weights.content_length
                base_score = 100.0 + author_score + content_score + recency_bonus  # Base 100 for RSS articles
            else:
                # Calculate engagement score for social media posts
                engagement_score = (
                    likes * self.weights.likes +
                    retweets * self.weights.retweets +
                    replies * self.weights.replies
                )
                
                # Calculate author influence score (logarithmic to prevent domination)
                import math
                author_score = math.log10(max(author_followers, 1)) * self.weights.author_followers
                
                # Calculate content quality score
                content_score = min(content_length / 280, 1.0) * self.weights.content_length
                
                base_score = engagement_score + author_score + content_score + recency_bonus
            
            logger.debug(f"Base score calculation: author={author_score:.2f}, "
                        f"content={content_score:.2f}, recency={recency_bonus:.2f}, total={base_score:.2f}")
            
            return base_score
            
        except Exception as e:
            logger.error(f"Error calculating base score: {e}")
            return 0.0
    
    def _calculate_recency_bonus(self, created_at) -> float:
        """Calculate recency bonus for recently published articles.
        
        Args:
            created_at: Article creation timestamp
            
        Returns:
            Recency bonus score
        """
        try:
            from datetime import datetime, timezone
            
            if not created_at:
                return 0.0
            
            # Convert to datetime if it's a string
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
            # Ensure created_at has timezone info
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            
            # Get current time
            now = datetime.now(timezone.utc)
            
            # Calculate hours since publication
            time_diff = now - created_at
            hours_ago = time_diff.total_seconds() / 3600
            
            # Recency bonus calculation:
            # - Articles published in last 1 hour: +50 points
            # - Articles published in last 6 hours: +30 points  
            # - Articles published in last 24 hours: +15 points
            # - Articles published in last 7 days: +5 points
            # - Older articles: no bonus
            
            if hours_ago <= 1:
                return 50.0
            elif hours_ago <= 6:
                return 30.0
            elif hours_ago <= 24:
                return 15.0
            elif hours_ago <= 168:  # 7 days
                return 5.0
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating recency bonus: {e}")
            return 0.0
    
    def apply_feedback_adjustment(self, base_score: float, feedback_data: Dict[str, int]) -> float:
        """Apply feedback-based adjustments to score.
        
        Args:
            base_score: Original base score
            feedback_data: Dictionary with 'like' and 'dislike' counts
            
        Returns:
            Adjusted score
        """
        try:
            likes = feedback_data.get('like', 0)
            dislikes = feedback_data.get('dislike', 0)
            
            if likes == 0 and dislikes == 0:
                return base_score
            
            # Calculate feedback ratio
            total_feedback = likes + dislikes
            if total_feedback == 0:
                return base_score
            
            feedback_ratio = likes / total_feedback
            
            # Apply feedback adjustment
            feedback_multiplier = 1.0 + (feedback_ratio - 0.5) * 2.0  # Range: 0.0 to 2.0
            adjusted_score = base_score * feedback_multiplier
            
            logger.debug(f"Feedback adjustment: likes={likes}, dislikes={dislikes}, "
                        f"ratio={feedback_ratio:.2f}, multiplier={feedback_multiplier:.2f}, "
                        f"adjusted_score={adjusted_score:.2f}")
            
            return adjusted_score
            
        except Exception as e:
            logger.error(f"Error applying feedback adjustment: {e}")
            return base_score
    
    def calculate_final_score(self, tweet_data: Dict, feedback_data: Optional[Dict[str, int]] = None) -> float:
        """Calculate final score for a tweet.
        
        Args:
            tweet_data: Dictionary containing tweet metrics
            feedback_data: Optional dictionary with feedback counts
            
        Returns:
            Final score value
        """
        try:
            # Check minimum thresholds
            if not self._meets_thresholds(tweet_data):
                return 0.0
            
            # Calculate base score
            base_score = self.calculate_base_score(tweet_data)
            
            # Apply feedback adjustment if available
            if feedback_data:
                final_score = self.apply_feedback_adjustment(base_score, feedback_data)
            else:
                final_score = base_score
            
            # Apply category-based scoring
            category_multiplier = self.calculate_category_score(tweet_data)
            final_score *= category_multiplier
            
            # Ensure non-negative score
            final_score = max(0.0, final_score)
            
            logger.info(f"Final score for tweet {tweet_data.get('id', 'unknown')}: {final_score:.2f}")
            
            return final_score
            
        except Exception as e:
            logger.error(f"Error calculating final score: {e}")
            return 0.0
    
    def calculate_category_score(self, tweet_data: Dict) -> float:
        """Calculate category-based score multiplier.
        
        Args:
            tweet_data: Dictionary containing tweet data with categories
            
        Returns:
            Category score multiplier
        """
        try:
            if not self.weights.category_weights:
                return 1.0  # No category weights configured
            
            categories = tweet_data.get('categories', [])
            if not categories:
                return 1.0  # No categories found
            
            # Calculate weighted category score
            category_scores = []
            for category in categories:
                weight = self.weights.category_weights.get(category, 1.0)
                category_scores.append(weight)
            
            # Use average of category weights
            if category_scores:
                return sum(category_scores) / len(category_scores)
            else:
                return 1.0
                
        except Exception as e:
            logger.error(f"Error calculating category score: {e}")
            return 1.0
    
    def update_user_preferences(self, category: str, rating: int) -> None:
        """Update user preferences based on feedback.
        
        Args:
            category: Category that received feedback
            rating: Rating value (1-5)
        """
        try:
            if not self.weights.user_preferences:
                return
            
            # Initialize user preferences if not exists
            if not hasattr(self.weights, 'user_preferences') or self.weights.user_preferences is None:
                self.weights.user_preferences = {}
            
            # Calculate preference adjustment
            learning_rate = self.weights.user_preferences.get('learning_rate', 0.1)
            current_pref = self.weights.user_preferences.get(category, 1.0)
            
            # Normalize rating to 0-1 scale
            normalized_rating = (rating - 1) / 4.0  # Convert 1-5 to 0-1
            
            # Update preference with learning rate
            new_pref = current_pref + learning_rate * (normalized_rating - current_pref)
            
            # Update category weight
            if self.weights.category_weights:
                self.weights.category_weights[category] = max(0.1, new_pref)
            
            # Store user preference
            self.weights.user_preferences[category] = new_pref
            
            logger.info(f"Updated user preference for {category}: {current_pref:.3f} -> {new_pref:.3f}")
            
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
    
    def _meets_thresholds(self, tweet_data: Dict) -> bool:
        """Check if tweet meets minimum thresholds.
        
        Args:
            tweet_data: Dictionary containing tweet metrics
            
        Returns:
            True if thresholds are met, False otherwise
        """
        try:
            likes = tweet_data.get('likes', 0)
            retweets = tweet_data.get('retweets', 0)
            author_followers = tweet_data.get('author_followers', 0)
            
            # For RSS articles (which have 0 likes/retweets), use different logic
            if likes == 0 and retweets == 0:
                # RSS articles should pass if they have reasonable author followers
                return author_followers >= 100  # Lower threshold for RSS
            else:
                # For social media posts, use original thresholds
                return (likes >= self.min_thresholds['min_likes'] and
                        retweets >= self.min_thresholds['min_retweets'] and
                        author_followers >= self.min_thresholds['min_author_followers'])
                    
        except Exception as e:
            logger.error(f"Error checking thresholds: {e}")
            return False
    
    def update_weights(self, new_weights: Dict[str, float]) -> None:
        """Update scoring weights dynamically.
        
        Args:
            new_weights: Dictionary with new weight values
        """
        try:
            if 'likes' in new_weights:
                self.weights.likes = new_weights['likes']
            if 'retweets' in new_weights:
                self.weights.retweets = new_weights['retweets']
            if 'replies' in new_weights:
                self.weights.replies = new_weights['replies']
            if 'user_feedback' in new_weights:
                self.weights.user_feedback = new_weights['user_feedback']
            if 'author_followers' in new_weights:
                self.weights.author_followers = new_weights['author_followers']
            if 'content_length' in new_weights:
                self.weights.content_length = new_weights['content_length']
                
            logger.info("Scoring weights updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating weights: {e}")
    
    def get_score_breakdown(self, tweet_data: Dict, feedback_data: Optional[Dict[str, int]] = None) -> Dict:
        """Get detailed breakdown of score calculation.
        
        Args:
            tweet_data: Dictionary containing tweet metrics
            feedback_data: Optional dictionary with feedback counts
            
        Returns:
            Dictionary with score breakdown
        """
        try:
            likes = tweet_data.get('likes', 0)
            retweets = tweet_data.get('retweets', 0)
            replies = tweet_data.get('replies', 0)
            author_followers = tweet_data.get('author_followers', 0)
            content_length = len(tweet_data.get('text', ''))
            
            # Calculate individual components
            likes_score = likes * self.weights.likes
            retweets_score = retweets * self.weights.retweets
            replies_score = replies * self.weights.replies
            
            import math
            author_score = math.log10(max(author_followers, 1)) * self.weights.author_followers
            content_score = min(content_length / 280, 1.0) * self.weights.content_length
            
            engagement_score = likes_score + retweets_score + replies_score
            base_score = engagement_score + author_score + content_score
            
            # Calculate feedback adjustment
            feedback_adjustment = 0.0
            feedback_multiplier = 1.0
            if feedback_data:
                likes_feedback = feedback_data.get('like', 0)
                dislikes_feedback = feedback_data.get('dislike', 0)
                total_feedback = likes_feedback + dislikes_feedback
                
                if total_feedback > 0:
                    feedback_ratio = likes_feedback / total_feedback
                    feedback_multiplier = 1.0 + (feedback_ratio - 0.5) * 2.0
                    feedback_adjustment = base_score * (feedback_multiplier - 1.0)
            
            final_score = base_score + feedback_adjustment
            
            return {
                'likes_score': round(likes_score, 2),
                'retweets_score': round(retweets_score, 2),
                'replies_score': round(replies_score, 2),
                'author_score': round(author_score, 2),
                'content_score': round(content_score, 2),
                'engagement_score': round(engagement_score, 2),
                'base_score': round(base_score, 2),
                'feedback_adjustment': round(feedback_adjustment, 2),
                'feedback_multiplier': round(feedback_multiplier, 2),
                'final_score': round(final_score, 2),
                'meets_thresholds': self._meets_thresholds(tweet_data)
            }
            
        except Exception as e:
            logger.error(f"Error getting score breakdown: {e}")
            return {
                'final_score': 0.0,
                'meets_thresholds': False,
                'error': str(e)
            } 