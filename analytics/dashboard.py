"""
Analytics dashboard for Robotics Radar.
Streamlit-based dashboard for visualizing data and insights.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.database import DatabaseManager
from scoring.scoring_model import ScoringModel
from nlp.keyword_extraction import KeywordExtractor

# Configure page
st.set_page_config(
    page_title="Robotics Radar Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

class AnalyticsDashboard:
    """Streamlit dashboard for Robotics Radar analytics."""
    
    def __init__(self):
        """Initialize dashboard."""
        self.db = DatabaseManager()
        self.scoring_model = ScoringModel()
        self.keyword_extractor = KeywordExtractor()
        
    def run(self):
        """Run the dashboard."""
        # Header
        st.title("🤖 Robotics Radar Dashboard")
        st.markdown("Real-time analytics and insights for robotics content curation")
        
        # Sidebar
        self._create_sidebar()
        
        # Main content
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self._show_overview_metrics()
            self._show_trending_topics()
            self._show_top_tweets()
        
        with col2:
            self._show_top_authors()
            self._show_feedback_analytics()
        
        # Bottom section
        col3, col4 = st.columns(2)
        
        with col3:
            self._show_engagement_metrics()
        
        with col4:
            self._show_content_analysis()
        
        # Category and keyword analytics sections
        self._show_category_analytics()
        self._show_keyword_analytics()
    
    def _create_sidebar(self):
        """Create sidebar with filters and controls."""
        st.sidebar.header("Dashboard Controls")
        
        # Time range filter
        st.sidebar.subheader("Time Range")
        time_range = st.sidebar.selectbox(
            "Select time range:",
            ["Last 24 hours", "Last 7 days", "Last 30 days", "All Time"],
            index=3
        )
        
        # Number of articles to display
        st.sidebar.subheader("Display Settings")
        num_articles = st.sidebar.slider(
            "Number of articles to display:",
            min_value=5,
            max_value=100,
            value=20,
            step=5
        )
        
        # Score threshold filter
        st.sidebar.subheader("Score Threshold")
        min_score = st.sidebar.slider(
            "Minimum score:",
            min_value=0.0,
            max_value=100.0,
            value=10.0,
            step=5.0
        )
        
        # Topic filter
        st.sidebar.subheader("Topic Filter")
        topics = self._get_available_topics()
        selected_topics = st.sidebar.multiselect(
            "Select topics:",
            topics,
            default=topics[:3] if topics else []
        )
        
        # Refresh button
        if st.sidebar.button("🔄 Refresh Data"):
            st.rerun()
        
        # Store filters in session state
        st.session_state.time_range = time_range
        st.session_state.min_score = min_score
        st.session_state.selected_topics = selected_topics
        st.session_state.num_articles = num_articles
    
    def _show_overview_metrics(self):
        """Show overview metrics."""
        st.header("📈 Overview Metrics")
        
        try:
            analytics = self.db.get_analytics_summary()
            
            # Create metrics cards
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="Total Articles",
                    value=f"{analytics['total_articles']:,}",
                    delta=f"+{analytics['recent_articles']} (24h)"
                )
            
            with col2:
                st.metric(
                    label="Total Authors",
                    value=f"{analytics['total_authors']:,}",
                    delta="+0"
                )
            
            with col3:
                st.metric(
                    label="Average Score",
                    value=f"{analytics['avg_score']:.2f}",
                    delta="+0.0"
                )
            
            with col4:
                st.metric(
                    label="Total Feedback",
                    value=f"{analytics['total_feedback']:,}",
                    delta="+0"
                )
            
        except Exception as e:
            st.error(f"Error loading overview metrics: {e}")
    
    def _show_trending_topics(self):
        """Show trending topics visualization."""
        st.header("🔥 Trending Topics")
        
        try:
            topics = self.db.get_trending_topics(limit=10)
            
            if topics:
                # Create DataFrame
                df = pd.DataFrame(topics)
                df['updated_at'] = pd.to_datetime(df['updated_at'])
                
                # Create bar chart
                fig = px.bar(
                    df.head(8),
                    x='name',
                    y='frequency',
                    title="Most Mentioned Topics",
                    labels={'name': 'Topic', 'frequency': 'Mentions'},
                    color='frequency',
                    color_continuous_scale='viridis'
                )
                
                fig.update_layout(
                    xaxis_tickangle=-45,
                    height=400,
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show topic details
                with st.expander("📋 Topic Details"):
                    for i, topic in enumerate(topics[:10], 1):
                        st.write(f"{i}. **{topic['name']}** - {topic['frequency']} mentions")
            else:
                st.info("No trending topics available")
                
        except Exception as e:
            st.error(f"Error loading trending topics: {e}")
    
    def _show_top_tweets(self):
        """Show top tweets table."""
        st.header("🏆 Top Articles")
        
        try:
            # Get number of articles from session state or default to 20
            num_articles = getattr(st.session_state, 'num_articles', 20)
            tweets = self.db.get_top_articles(limit=num_articles)
            
            if tweets:
                # Create DataFrame with deduplication
                data = []
                seen_urls = set()
                
                for tweet in tweets:
                    # Skip if we've already seen this URL (deduplicate)
                    if tweet.url in seen_urls:
                        continue
                    seen_urls.add(tweet.url)
                    
                    # Clean the text for display
                    clean_text = self._clean_text_for_display(tweet.text)
                    
                    # Extract keywords from topics or generate them
                    keywords = self._extract_keywords_for_display(tweet)
                    
                    data.append({
                        'Author': f"@{tweet.author_username}",
                        'Title': clean_text[:80] + "..." if len(clean_text) > 80 else clean_text,
                        'Summary': tweet.summary[:120] + "..." if len(tweet.summary) > 120 else tweet.summary if tweet.summary else "No summary",
                        'Keywords': keywords,
                        'Score': f"{tweet.score:.2f}",
                        'Likes': tweet.likes,
                        'Retweets': tweet.retweets,
                        'Replies': tweet.replies,
                        'Created': tweet.created_at.strftime('%Y-%m-%d %H:%M'),
                        'URL': tweet.url
                    })
                
                df = pd.DataFrame(data)
                
                # Display table
                st.dataframe(
                    df,
                    column_config={
                        "URL": st.column_config.LinkColumn("Link"),
                        "Score": st.column_config.NumberColumn("Score", format="%.2f"),
                        "Likes": st.column_config.NumberColumn("Likes", format="%d"),
                        "Retweets": st.column_config.NumberColumn("Retweets", format="%d"),
                        "Replies": st.column_config.NumberColumn("Replies", format="%d"),
                        "Summary": st.column_config.TextColumn("Summary", width="medium"),
                        "Keywords": st.column_config.TextColumn("Keywords", width="medium")
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("No articles available")
                
        except Exception as e:
            st.error(f"Error loading top articles: {e}")
    
    def _clean_text_for_display(self, text: str) -> str:
        """Clean text for display in the dashboard.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        import re
        
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        # Remove image descriptions and metadata
        clean_text = re.sub(r'<img[^>]*alt="[^"]*"[^>]*>', '', clean_text)
        clean_text = re.sub(r'Source:\s*[^.]*\.', '', clean_text)
        clean_text = re.sub(r'Credit:\s*[^.]*\.', '', clean_text)
        clean_text = re.sub(r'Image:\s*[^.]*\.', '', clean_text)
        clean_text = re.sub(r'A computer-generated[^.]*\.', '', clean_text)
        clean_text = re.sub(r'AI-generated[^.]*\.', '', clean_text)
        
        # Remove extra whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        return clean_text.strip()
    
    def _extract_keywords_for_display(self, tweet) -> str:
        """Extract keywords for display in the dashboard.
        
        Args:
            tweet: Tweet object
            
        Returns:
            Formatted keywords string
        """
        try:
            # Always extract fresh keywords from the text content
            from nlp.keyword_extraction import KeywordExtractor
            extractor = KeywordExtractor()
            
            # Clean the text first to remove HTML artifacts
            clean_text = self._clean_text_for_display(tweet.text)
            content_text = clean_text
            
            if tweet.summary:
                clean_summary = self._clean_text_for_display(tweet.summary)
                content_text += f" {clean_summary}"
            
            keywords = extractor.extract_keywords(content_text, max_keywords=8)
            
            if keywords:
                # Filter out HTML artifacts and short words
                filtered_keywords = []
                for keyword in keywords:
                    # Skip HTML artifacts and very short words
                    if (len(keyword) > 2 and 
                        not keyword.startswith('class=') and 
                        not keyword.startswith('wp-') and
                        not keyword.startswith('align') and
                        not keyword.startswith('caption')):
                        filtered_keywords.append(keyword)
                
                # Format keywords nicely
                formatted_keywords = ", ".join(filtered_keywords[:6])  # Show top 6 keywords
                return formatted_keywords if formatted_keywords else "No keywords"
            else:
                return "No keywords"
            
        except Exception as e:
            return "No keywords"
    
    def _show_top_authors(self):
        """Show top authors visualization."""
        st.header("👥 Top Authors")
        
        try:
            authors = self.db.get_top_authors(limit=10)
            
            if authors:
                # Create DataFrame
                df = pd.DataFrame(authors)
                
                # Create bar chart
                fig = px.bar(
                    df.head(8),
                    x='username',
                    y='followers_count',
                    title="Top Authors by Followers",
                    labels={'username': 'Author', 'followers_count': 'Followers'},
                    color='tweet_count',
                    color_continuous_scale='plasma'
                )
                
                fig.update_layout(
                    xaxis_tickangle=-45,
                    height=300,
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show author details
                with st.expander("📋 Author Details"):
                    for i, author in enumerate(authors[:5], 1):
                        st.write(f"{i}. **@{author['username']}** - {author['followers_count']:,} followers")
            else:
                st.info("No authors available")
                
        except Exception as e:
            st.error(f"Error loading top authors: {e}")
    
    def _show_feedback_analytics(self):
        """Show feedback analytics with 1-5 star rating system."""
        st.header("💬 Feedback Analytics")
        
        try:
            # Get real feedback data from database
            feedback_stats = self.db.get_feedback_stats()
            
            if feedback_stats:
                # Extract 1-5 star ratings
                ratings = {
                    '1 Star': feedback_stats.get('rating_1', 0),
                    '2 Stars': feedback_stats.get('rating_2', 0),
                    '3 Stars': feedback_stats.get('rating_3', 0),
                    '4 Stars': feedback_stats.get('rating_4', 0),
                    '5 Stars': feedback_stats.get('rating_5', 0)
                }
                
                total_ratings = sum(ratings.values())
                
                if total_ratings > 0:
                    # Create pie chart for rating distribution
                    fig = go.Figure(data=[go.Pie(
                        labels=list(ratings.keys()),
                        values=list(ratings.values()),
                        hole=0.3,
                        marker_colors=['#ff6b6b', '#ffa726', '#ffeb3b', '#66bb6a', '#42a5f5']
                    )])
                    
                    fig.update_layout(
                        title="Rating Distribution (1-5 Stars)",
                        height=300,
                        showlegend=True
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Calculate average rating
                    weighted_sum = sum(i * ratings[f'{i} Star{"s" if i > 1 else ""}'] for i in range(1, 6))
                    avg_rating = weighted_sum / total_ratings if total_ratings > 0 else 0
                    
                    # Show feedback stats
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Ratings", f"{total_ratings}")
                    with col2:
                        st.metric("Average Rating", f"{avg_rating:.1f} ⭐")
                    with col3:
                        st.metric("5-Star Ratings", f"{ratings['5 Stars']}")
                    
                    # Show detailed rating breakdown
                    st.subheader("Rating Breakdown")
                    rating_df = pd.DataFrame([
                        {"Rating": k, "Count": v, "Percentage": f"{(v/total_ratings)*100:.1f}%"}
                        for k, v in ratings.items() if v > 0
                    ])
                    st.dataframe(rating_df, use_container_width=True)
                    
                else:
                    st.info("No ratings available yet. Rate some articles to see analytics!")
            else:
                st.info("No feedback data available yet")
                
        except Exception as e:
            st.error(f"Error loading feedback analytics: {e}")
    
    def _show_engagement_metrics(self):
        """Show engagement metrics."""
        st.header("📊 Content Metrics")
        
        try:
            # Get real engagement data from database
            engagement_data = self.db.get_engagement_trends(days=7)
            
            if engagement_data and len(engagement_data) > 1:
                # Create line chart
                fig = go.Figure()
                
                dates = [item['date'] for item in engagement_data]
                scores = [item['avg_score'] for item in engagement_data]
                counts = [item['article_count'] for item in engagement_data]
                
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=scores,
                    mode='lines+markers',
                    name='Average Score',
                    line=dict(color='#1da1f2')
                ))
                
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=counts,
                    mode='lines+markers',
                    name='Article Count',
                    line=dict(color='#17bf63'),
                    yaxis='y2'
                ))
                
                fig.update_layout(
                    title="Content Trends (Last 7 Days)",
                    height=400,
                    xaxis_title="Date",
                    yaxis_title="Average Score",
                    yaxis2=dict(
                        title="Article Count",
                        overlaying='y',
                        side='right'
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No engagement data available yet")
            
        except Exception as e:
            st.error(f"Error loading engagement metrics: {e}")
    
    def _show_content_analysis(self):
        """Show content analysis."""
        st.header("📝 Content Analysis")
        
        try:
            # Get real content analysis data from database
            content_data = self.db.get_content_categories()
            
            if content_data:
                # Create horizontal bar chart
                fig = px.bar(
                    x=[item['count'] for item in content_data],
                    y=[', '.join(item['categories']) if isinstance(item['categories'], list) else str(item['categories']) for item in content_data],
                    orientation='h',
                    title="Content Categories",
                    labels={'x': 'Count', 'y': 'Category'},
                    color=[item['count'] for item in content_data],
                    color_continuous_scale='viridis'
                )
                
                fig.update_layout(
                    height=400,
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show content insights
                with st.expander("💡 Content Insights"):
                    for item in content_data[:3]:
                        category_name = ', '.join(item['categories']) if isinstance(item['categories'], list) else str(item['categories'])
                        st.write(f"• **{category_name}** posts: {item['count']} articles")
                    if content_data:
                        top_category = content_data[0]
                        category_name = ', '.join(top_category['categories']) if isinstance(top_category['categories'], list) else str(top_category['categories'])
                        st.write(f"• **{category_name}** is the most popular category")
                
            else:
                st.info("No content analysis data available yet")
                
        except Exception as e:
            st.error(f"Error loading content analysis: {e}")
    
    def _show_category_analytics(self):
        """Show category-based analytics."""
        st.header("🏷️ Category Analytics")
        
        try:
            # Get articles with categories
            tweets = self.db.get_top_articles(limit=100)
            
            if tweets:
                # Extract category data
                category_data = {}
                for tweet in tweets:
                    if tweet.categories:
                        for category in tweet.categories:
                            if category not in category_data:
                                category_data[category] = {
                                    'count': 0,
                                    'total_score': 0.0,
                                    'avg_score': 0.0
                                }
                            category_data[category]['count'] += 1
                            category_data[category]['total_score'] += tweet.score
                
                # Calculate average scores
                for category in category_data:
                    if category_data[category]['count'] > 0:
                        category_data[category]['avg_score'] = (
                            category_data[category]['total_score'] / 
                            category_data[category]['count']
                        )
                
                if category_data:
                    # Create category distribution chart
                    categories = list(category_data.keys())
                    counts = [category_data[cat]['count'] for cat in categories]
                    avg_scores = [category_data[cat]['avg_score'] for cat in categories]
                    
                    # Create bar chart
                    fig = go.Figure()
                    
                    fig.add_trace(go.Bar(
                        x=categories,
                        y=counts,
                        name='Article Count',
                        marker_color='#1da1f2'
                    ))
                    
                    fig.update_layout(
                        title="Articles by Category",
                        xaxis_title="Category",
                        yaxis_title="Number of Articles",
                        height=400,
                        showlegend=True
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show category details
                    st.subheader("Category Performance")
                    category_df = pd.DataFrame([
                        {
                            "Category": cat,
                            "Articles": data['count'],
                            "Avg Score": f"{data['avg_score']:.2f}",
                            "Total Score": f"{data['total_score']:.2f}"
                        }
                        for cat, data in category_data.items()
                    ])
                    
                    st.dataframe(category_df, use_container_width=True)
                    
                    # Show user preferences if available
                    st.subheader("Your Category Preferences")
                    try:
                        # Get category weights from scoring model
                        category_weights = self.scoring_model.weights.category_weights
                        if category_weights:
                            preference_df = pd.DataFrame([
                                {
                                    "Category": cat,
                                    "Weight": f"{weight:.2f}",
                                    "Preference": "⭐" * int(weight * 5) if weight > 0 else "Not rated"
                                }
                                for cat, weight in category_weights.items()
                                if weight != 1.0  # Show only adjusted preferences
                            ])
                            
                            if not preference_df.empty:
                                st.dataframe(preference_df, use_container_width=True)
                            else:
                                st.info("Rate some articles to see your category preferences!")
                        else:
                            st.info("No category preferences available yet")
                    except Exception as e:
                        st.info("Category preferences will appear as you rate articles")
                else:
                    st.info("No category data available yet")
            else:
                st.info("No articles available for category analysis")
                
        except Exception as e:
            st.error(f"Error loading category analytics: {e}")
    
    def _show_keyword_analytics(self):
        """Show keyword-based analytics."""
        st.header("🔍 Keyword Analytics")
        
        try:
            # Get articles for keyword analysis
            tweets = self.db.get_top_articles(limit=50)
            
            if tweets:
                # Extract keywords from all articles
                from nlp.keyword_extraction import KeywordExtractor
                extractor = KeywordExtractor()
                
                all_keywords = []
                for tweet in tweets:
                    # Clean the text first to remove HTML artifacts
                    clean_text = self._clean_text_for_display(tweet.text)
                    content_text = clean_text
                    
                    if tweet.summary:
                        clean_summary = self._clean_text_for_display(tweet.summary)
                        content_text += f" {clean_summary}"
                    
                    keywords = extractor.extract_keywords(content_text, max_keywords=5)
                    
                    # Filter out HTML artifacts and short words
                    filtered_keywords = []
                    for keyword in keywords:
                        if (len(keyword) > 2 and 
                            not keyword.startswith('class=') and 
                            not keyword.startswith('wp-') and
                            not keyword.startswith('align') and
                            not keyword.startswith('caption')):
                            filtered_keywords.append(keyword)
                    
                    all_keywords.extend(filtered_keywords)
                
                # Count keyword frequency
                from collections import Counter
                keyword_counts = Counter(all_keywords)
                
                if keyword_counts:
                    # Get top 15 keywords
                    top_keywords = keyword_counts.most_common(15)
                    
                    # Create bar chart
                    keywords, counts = zip(*top_keywords)
                    
                    fig = go.Figure(data=[go.Bar(
                        x=keywords,
                        y=counts,
                        marker_color='#ff6b6b'
                    )])
                    
                    fig.update_layout(
                        title="Most Common Keywords",
                        xaxis_title="Keywords",
                        yaxis_title="Frequency",
                        height=400,
                        xaxis_tickangle=-45
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show keyword details
                    st.subheader("Keyword Frequency")
                    keyword_df = pd.DataFrame([
                        {
                            "Keyword": keyword,
                            "Frequency": count,
                            "Percentage": f"{(count/len(all_keywords)*100):.1f}%"
                        }
                        for keyword, count in top_keywords
                    ])
                    
                    st.dataframe(keyword_df, use_container_width=True)
                else:
                    st.info("No keywords found in articles")
            else:
                st.info("No articles available for keyword analysis")
                
        except Exception as e:
            st.error(f"Error loading keyword analytics: {e}")
    
    def _get_available_topics(self) -> List[str]:
        """Get available topics for filtering.
        
        Returns:
            List of available topics
        """
        try:
            topics = self.db.get_trending_topics(limit=20)
            return [topic['name'] for topic in topics]
        except Exception as e:
            st.error(f"Error getting available topics: {e}")
            return []


def main():
    """Main function to run the dashboard."""
    try:
        dashboard = AnalyticsDashboard()
        dashboard.run()
        
    except Exception as e:
        st.error(f"Error running dashboard: {e}")
        st.exception(e)


if __name__ == "__main__":
    main() 