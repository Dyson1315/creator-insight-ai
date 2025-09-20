"""
Analytics service for recommendation performance and user behavior analysis
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.models.database import RecommendationHistory, UserLike, Artwork
from app.models.schemas import RecommendationMetrics, UserBehaviorAnalytics

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
    
    async def get_recommendation_performance(
        self,
        start_date: datetime,
        end_date: datetime,
        algorithm_version: Optional[str] = None
    ) -> RecommendationMetrics:
        """
        Get recommendation system performance metrics
        """
        try:
            # Base query
            query = self.db.query(RecommendationHistory).filter(
                and_(
                    RecommendationHistory.createdAt >= start_date,
                    RecommendationHistory.createdAt <= end_date
                )
            )
            
            if algorithm_version:
                query = query.filter(RecommendationHistory.algorithmVersion == algorithm_version)
            
            # Total recommendations
            total_recommendations = query.count()
            
            # Click-through rate
            total_clicks = query.filter(RecommendationHistory.wasClicked == True).count()
            click_through_rate = total_clicks / total_recommendations if total_recommendations > 0 else 0
            
            # Conversion rate (likes after recommendations)
            conversions = self.db.query(UserLike).join(
                RecommendationHistory,
                and_(
                    UserLike.userId == RecommendationHistory.userId,
                    UserLike.artworkId == RecommendationHistory.artworkId,
                    UserLike.createdAt >= RecommendationHistory.createdAt
                )
            ).filter(
                and_(
                    RecommendationHistory.createdAt >= start_date,
                    RecommendationHistory.createdAt <= end_date,
                    UserLike.isLike == True
                )
            ).count()
            
            conversion_rate = conversions / total_recommendations if total_recommendations > 0 else 0
            
            # Average score
            avg_score_result = query.with_entities(func.avg(RecommendationHistory.score)).scalar()
            average_score = float(avg_score_result) if avg_score_result else 0.0
            
            # Top categories
            top_categories = self._get_top_recommended_categories(start_date, end_date, algorithm_version)
            
            # Algorithm performance comparison
            algorithm_performance = await self._get_algorithm_performance_comparison(start_date, end_date)
            
            return RecommendationMetrics(
                total_recommendations=total_recommendations,
                click_through_rate=click_through_rate,
                conversion_rate=conversion_rate,
                average_score=average_score,
                top_categories=top_categories,
                algorithm_performance=algorithm_performance
            )
            
        except Exception as e:
            logger.error(f"Error getting recommendation performance: {str(e)}")
            raise
    
    async def get_user_behavior(self, user_id: str) -> UserBehaviorAnalytics:
        """
        Get user behavior analytics
        """
        try:
            # Total interactions
            total_likes = self.db.query(UserLike).filter(UserLike.userId == user_id).count()
            total_recommendations = self.db.query(RecommendationHistory).filter(
                RecommendationHistory.userId == user_id
            ).count()
            total_interactions = total_likes + total_recommendations
            
            # Favorite categories and styles
            favorite_categories = self._get_user_favorite_categories(user_id)
            favorite_styles = self._get_user_favorite_styles(user_id)
            
            # Session duration analysis
            avg_session_duration = self._calculate_average_session_duration(user_id)
            
            # Engagement score
            engagement_score = self._calculate_engagement_score(user_id)
            
            # Preference vector
            preference_vector = await self._get_user_preference_vector(user_id)
            
            return UserBehaviorAnalytics(
                user_id=user_id,
                total_interactions=total_interactions,
                favorite_categories=favorite_categories,
                favorite_styles=favorite_styles,
                average_session_duration=avg_session_duration,
                engagement_score=engagement_score,
                preference_vector=preference_vector
            )
            
        except Exception as e:
            logger.error(f"Error getting user behavior: {str(e)}")
            raise
    
    def _get_top_recommended_categories(
        self,
        start_date: datetime,
        end_date: datetime,
        algorithm_version: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get top recommended categories in time period
        """
        try:
            # Join with artwork to get categories
            query = self.db.query(
                Artwork.category,
                func.count(RecommendationHistory.id).label('count'),
                func.avg(RecommendationHistory.score).label('avg_score')
            ).join(
                RecommendationHistory, Artwork.id == RecommendationHistory.artworkId
            ).filter(
                and_(
                    RecommendationHistory.createdAt >= start_date,
                    RecommendationHistory.createdAt <= end_date,
                    Artwork.category.isnot(None)
                )
            )
            
            if algorithm_version:
                query = query.filter(RecommendationHistory.algorithmVersion == algorithm_version)
            
            results = query.group_by(Artwork.category).order_by(
                func.count(RecommendationHistory.id).desc()
            ).limit(10).all()
            
            return [
                {
                    "category": result.category,
                    "count": result.count,
                    "average_score": float(result.avg_score) if result.avg_score else 0.0
                }
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting top categories: {str(e)}")
            return []
    
    async def _get_algorithm_performance_comparison(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, float]:
        """
        Compare performance across different algorithm versions
        """
        try:
            results = self.db.query(
                RecommendationHistory.algorithmVersion,
                func.count(RecommendationHistory.id).label('total'),
                func.sum(func.cast(RecommendationHistory.wasClicked, func.Integer())).label('clicks'),
                func.avg(RecommendationHistory.score).label('avg_score')
            ).filter(
                and_(
                    RecommendationHistory.createdAt >= start_date,
                    RecommendationHistory.createdAt <= end_date
                )
            ).group_by(RecommendationHistory.algorithmVersion).all()
            
            performance = {}
            for result in results:
                ctr = result.clicks / result.total if result.total > 0 else 0
                performance[result.algorithmVersion] = {
                    "click_through_rate": ctr,
                    "average_score": float(result.avg_score) if result.avg_score else 0.0,
                    "total_recommendations": result.total
                }
            
            return performance
            
        except Exception as e:
            logger.error(f"Error getting algorithm performance: {str(e)}")
            return {}
    
    def _get_user_favorite_categories(self, user_id: str) -> List[str]:
        """
        Get user's favorite categories based on likes
        """
        try:
            results = self.db.query(
                Artwork.category,
                func.count(UserLike.id).label('count')
            ).join(
                UserLike, Artwork.id == UserLike.artworkId
            ).filter(
                and_(
                    UserLike.userId == user_id,
                    UserLike.isLike == True,
                    Artwork.category.isnot(None)
                )
            ).group_by(Artwork.category).order_by(
                func.count(UserLike.id).desc()
            ).limit(5).all()
            
            return [result.category for result in results]
            
        except Exception as e:
            logger.error(f"Error getting favorite categories: {str(e)}")
            return []
    
    def _get_user_favorite_styles(self, user_id: str) -> List[str]:
        """
        Get user's favorite styles based on likes
        """
        try:
            results = self.db.query(
                Artwork.style,
                func.count(UserLike.id).label('count')
            ).join(
                UserLike, Artwork.id == UserLike.artworkId
            ).filter(
                and_(
                    UserLike.userId == user_id,
                    UserLike.isLike == True,
                    Artwork.style.isnot(None)
                )
            ).group_by(Artwork.style).order_by(
                func.count(UserLike.id).desc()
            ).limit(5).all()
            
            return [result.style for result in results]
            
        except Exception as e:
            logger.error(f"Error getting favorite styles: {str(e)}")
            return []
    
    def _calculate_average_session_duration(self, user_id: str) -> float:
        """
        Calculate average session duration for user
        """
        try:
            # TODO: Implement session tracking
            # For now, return placeholder
            return 300.0  # 5 minutes
            
        except Exception as e:
            logger.error(f"Error calculating session duration: {str(e)}")
            return 0.0
    
    def _calculate_engagement_score(self, user_id: str) -> float:
        """
        Calculate user engagement score
        """
        try:
            # Get user activity metrics
            total_likes = self.db.query(UserLike).filter(UserLike.userId == user_id).count()
            positive_likes = self.db.query(UserLike).filter(
                and_(UserLike.userId == user_id, UserLike.isLike == True)
            ).count()
            
            total_recommendations = self.db.query(RecommendationHistory).filter(
                RecommendationHistory.userId == user_id
            ).count()
            total_clicks = self.db.query(RecommendationHistory).filter(
                and_(
                    RecommendationHistory.userId == user_id,
                    RecommendationHistory.wasClicked == True
                )
            ).count()
            
            # Calculate engagement components
            like_ratio = positive_likes / total_likes if total_likes > 0 else 0
            click_ratio = total_clicks / total_recommendations if total_recommendations > 0 else 0
            activity_level = min((total_likes + total_clicks) / 50, 1.0)  # Normalize to 0-1
            
            # Weighted engagement score
            engagement_score = (like_ratio * 0.4 + click_ratio * 0.4 + activity_level * 0.2)
            
            return engagement_score
            
        except Exception as e:
            logger.error(f"Error calculating engagement score: {str(e)}")
            return 0.0
    
    async def _get_user_preference_vector(self, user_id: str) -> List[float]:
        """
        Get user preference vector for ML models
        """
        try:
            # TODO: Implement preference vector calculation
            # For now, return dummy vector
            import numpy as np
            return np.random.rand(50).tolist()  # 50-dimensional preference vector
            
        except Exception as e:
            logger.error(f"Error getting preference vector: {str(e)}")
            return [0.0] * 50