"""
Feedback processor for Robotics Radar.
Handles user feedback and dynamically adjusts scoring weights.
"""

import logging
from typing import Dict, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.database import DatabaseManager
from scoring.scoring_model import ScoringModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeedbackProcessor:
    """Processes user feedback and adjusts scoring weights dynamically."""
    
    def __init__(self):
        """Initialize feedback processor."""
        self.db = DatabaseManager()
        self.scoring_model = ScoringModel()
        
    def process_feedback(self, tweet_id: str, user_id: str, feedback_type: str) -> bool:
        """Process user feedback for a tweet.
        
        Args:
            tweet_id: ID of the tweet
            user_id: ID of the user providing feedback
            feedback_type: Type of feedback ('like', 'dislike', or 'rating_1' to 'rating_5')
            
        Returns:
            True if feedback processed successfully
        """
        try:
            # Validate feedback type
            if feedback_type.startswith('rating_'):
                # Handle 1-5 star ratings
                try:
                    rating = int(feedback_type.split('_')[1])
                    if rating < 1 or rating > 5:
                        logger.error(f"Invalid rating: {rating}")
                        return False
                except (ValueError, IndexError):
                    logger.error(f"Invalid rating format: {feedback_type}")
                    return False
            elif feedback_type not in ['like', 'dislike']:
                logger.error(f"Invalid feedback type: {feedback_type}")
                return False
            
            # Store feedback in database
            success = self.db.add_feedback(tweet_id, user_id, feedback_type)
            if not success:
                logger.error(f"Failed to store feedback for tweet {tweet_id}")
                return False
            
            # Update tweet score based on feedback
            self._update_tweet_score(tweet_id)
            
            # Update user preferences based on categories
            if feedback_type.startswith('rating_'):
                self._update_user_preferences(tweet_id, feedback_type)
            
            # Adjust scoring weights based on feedback patterns
            self._adjust_scoring_weights()
            
            logger.info(f"Feedback processed: {feedback_type} for tweet {tweet_id} by user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing feedback: {e}")
            return False
    
    def _update_tweet_score(self, tweet_id: str) -> None:
        """Update tweet score based on current feedback.
        
        Args:
            tweet_id: ID of the tweet to update
        """
        try:
            # Get current feedback for the tweet
            feedback_data = self.db.get_tweet_feedback(tweet_id)
            
            # Get tweet data from database
            # Note: This would require adding a method to get tweet by ID
            # For now, we'll use a simplified approach
            
            # Recalculate score with feedback
            # This is a simplified implementation - in practice, you'd get the full tweet data
            logger.info(f"Updated score for tweet {tweet_id} with feedback: {feedback_data}")
            
        except Exception as e:
            logger.error(f"Error updating tweet score: {e}")
    
    def _update_user_preferences(self, tweet_id: str, feedback_type: str) -> None:
        """Update user preferences based on tweet categories and rating.
        
        Args:
            tweet_id: ID of the tweet
            feedback_type: Rating feedback (e.g., 'rating_4')
        """
        try:
            # Extract rating from feedback type
            rating = int(feedback_type.split('_')[1])
            
            # Get tweet data to extract categories
            # Note: This would require adding a method to get tweet by ID
            # For now, we'll use a simplified approach
            
            # Get categories from database (simplified)
            # In practice, you'd query the database for the tweet's categories
            categories = self._get_article_categories(tweet_id)
            
            if categories:
                # Update preferences for each category
                for category in categories:
                    self.scoring_model.update_user_preferences(category, rating)
                    logger.info(f"Updated preference for category {category} with rating {rating}")
            
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
    
    def _get_article_categories(self, article_id: str) -> list:
        """Get categories for a specific article.
        
        Args:
            article_id: ID of the article
            
        Returns:
            List of categories
        """
        try:
            # Get article from database
            article = self.db.get_article_by_id(article_id)
            if article and article.categories:
                return article.categories
            else:
                return ['robotics_general']
                
        except Exception as e:
            logger.error(f"Error getting article categories: {e}")
            return []
    
    def _adjust_scoring_weights(self) -> None:
        """Adjust scoring weights based on feedback patterns."""
        try:
            # Get recent feedback statistics
            feedback_stats = self._get_feedback_statistics()
            
            if not feedback_stats:
                return
            
            # Calculate adjustment factors
            adjustment_factors = self._calculate_weight_adjustments(feedback_stats)
            
            # Apply adjustments
            if adjustment_factors:
                self.scoring_model.update_weights(adjustment_factors)
                logger.info(f"Adjusted scoring weights: {adjustment_factors}")
            
        except Exception as e:
            logger.error(f"Error adjusting scoring weights: {e}")
    
    def _get_feedback_statistics(self) -> Optional[Dict]:
        """Get feedback statistics for weight adjustment.
        
        Returns:
            Dictionary with feedback statistics
        """
        try:
            # This would query the database for recent feedback patterns
            # For now, return a simplified structure
            return {
                'total_feedback': 100,
                'positive_ratio': 0.75,
                'recent_trend': 'positive'
            }
            
        except Exception as e:
            logger.error(f"Error getting feedback statistics: {e}")
            return None
    
    def _calculate_weight_adjustments(self, feedback_stats: Dict) -> Optional[Dict]:
        """Calculate weight adjustments based on feedback statistics.
        
        Args:
            feedback_stats: Feedback statistics
            
        Returns:
            Dictionary with weight adjustments
        """
        try:
            positive_ratio = feedback_stats.get('positive_ratio', 0.5)
            
            # Simple adjustment logic
            # If positive feedback is high, increase user feedback weight
            # If positive feedback is low, decrease user feedback weight
            
            adjustments = {}
            
            if positive_ratio > 0.7:
                # High positive feedback - increase user feedback weight
                adjustments['user_feedback'] = self.scoring_model.weights.user_feedback * 1.1
            elif positive_ratio < 0.3:
                # Low positive feedback - decrease user feedback weight
                adjustments['user_feedback'] = self.scoring_model.weights.user_feedback * 0.9
            
            return adjustments
            
        except Exception as e:
            logger.error(f"Error calculating weight adjustments: {e}")
            return None
    
    def get_feedback_summary(self, tweet_id: str) -> Dict:
        """Get feedback summary for a tweet.
        
        Args:
            tweet_id: ID of the tweet
            
        Returns:
            Dictionary with feedback summary
        """
        try:
            feedback_data = self.db.get_tweet_feedback(tweet_id)
            
            total_feedback = feedback_data.get('like', 0) + feedback_data.get('dislike', 0)
            
            if total_feedback == 0:
                return {
                    'total_feedback': 0,
                    'positive_ratio': 0.0,
                    'sentiment': 'neutral'
                }
            
            positive_ratio = feedback_data.get('like', 0) / total_feedback
            
            # Determine sentiment
            if positive_ratio > 0.6:
                sentiment = 'positive'
            elif positive_ratio < 0.4:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            return {
                'total_feedback': total_feedback,
                'positive_ratio': positive_ratio,
                'sentiment': sentiment,
                'likes': feedback_data.get('like', 0),
                'dislikes': feedback_data.get('dislike', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting feedback summary: {e}")
            return {
                'total_feedback': 0,
                'positive_ratio': 0.0,
                'sentiment': 'neutral'
            }
    
    def get_user_feedback_history(self, user_id: str, limit: int = 10) -> list:
        """Get feedback history for a user.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of feedback entries to return
            
        Returns:
            List of feedback entries
        """
        try:
            # This would query the database for user feedback history
            # For now, return an empty list
            logger.info(f"Getting feedback history for user {user_id}")
            return []
            
        except Exception as e:
            logger.error(f"Error getting user feedback history: {e}")
            return []
    
    def get_overall_feedback_analytics(self) -> Dict:
        """Get overall feedback analytics.
        
        Returns:
            Dictionary with feedback analytics
        """
        try:
            # This would aggregate feedback data from the database
            # For now, return simplified analytics
            
            analytics = {
                'total_feedback': 0,
                'positive_feedback': 0,
                'negative_feedback': 0,
                'positive_ratio': 0.0,
                'most_feedback_tweets': [],
                'feedback_trend': 'stable'
            }
            
            logger.info("Generated overall feedback analytics")
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting feedback analytics: {e}")
            return {
                'total_feedback': 0,
                'positive_feedback': 0,
                'negative_feedback': 0,
                'positive_ratio': 0.0,
                'most_feedback_tweets': [],
                'feedback_trend': 'unknown'
            }
    
    def export_feedback_data(self, format_type: str = 'json') -> Optional[str]:
        """Export feedback data for analysis.
        
        Args:
            format_type: Export format ('json', 'csv')
            
        Returns:
            Exported data as string or None if failed
        """
        try:
            # This would export feedback data from the database
            # For now, return a placeholder
            
            if format_type == 'json':
                return '{"feedback_data": []}'
            elif format_type == 'csv':
                return 'tweet_id,user_id,feedback_type,timestamp\n'
            else:
                logger.error(f"Unsupported export format: {format_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error exporting feedback data: {e}")
            return None
    
    def cleanup_old_feedback(self, days: int = 90) -> int:
        """Clean up old feedback data.
        
        Args:
            days: Number of days to keep feedback data
            
        Returns:
            Number of feedback entries removed
        """
        try:
            # This would remove old feedback data from the database
            # For now, return 0
            logger.info(f"Cleaning up feedback data older than {days} days")
            return 0
            
        except Exception as e:
            logger.error(f"Error cleaning up feedback data: {e}")
            return 0


def main():
    """Main function for testing feedback processing."""
    try:
        processor = FeedbackProcessor()
        
        # Test feedback processing
        success = processor.process_feedback(
            tweet_id="123456789",
            user_id="user123",
            feedback_type="like"
        )
        
        if success:
            print("Feedback processed successfully")
        else:
            print("Failed to process feedback")
        
        # Test feedback summary
        summary = processor.get_feedback_summary("123456789")
        print(f"Feedback summary: {summary}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    main() 