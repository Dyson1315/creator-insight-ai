"""
Recommendation service for artwork and artist suggestions
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import json
import uuid

from app.core.database import get_db
from app.models.database import Artwork, UserLike, RecommendationHistory
from app.models.schemas import RecommendationResponse, ArtworkResponse
from app.ml.recommendation_engine import RecommendationEngine

logger = logging.getLogger(__name__)

class RecommendationService:
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
        self.recommendation_engine = RecommendationEngine()
    
    async def get_artwork_recommendations(
        self,
        user_id: str,
        limit: int = 10,
        category: Optional[str] = None,
        style: Optional[str] = None
    ) -> List[RecommendationResponse]:
        """
        Get personalized artwork recommendations for a user
        """
        try:
            # Generate recommendation batch ID
            recommendation_id = str(uuid.uuid4())
            
            # Get user preference profile
            user_profile = await self._get_user_profile(user_id)
            
            # Query candidate artworks
            query = self.db.query(Artwork).filter(Artwork.isPublic == True)
            
            if category:
                query = query.filter(Artwork.category == category)
            if style:
                query = query.filter(Artwork.style == style)
                
            # Exclude already seen artworks
            seen_artwork_ids = self._get_seen_artworks(user_id)
            if seen_artwork_ids:
                query = query.filter(~Artwork.id.in_(seen_artwork_ids))
            
            candidate_artworks = query.limit(limit * 3).all()  # Get more candidates for filtering
            
            # Run recommendation algorithm
            recommendations = await self.recommendation_engine.recommend_artworks(
                user_profile=user_profile,
                candidate_artworks=candidate_artworks,
                limit=limit
            )
            
            # Record recommendation history
            await self._record_recommendations(
                user_id, recommendations, recommendation_id
            )
            
            # Convert to response format
            response = []
            for i, (artwork, score) in enumerate(recommendations):
                artwork_response = ArtworkResponse.from_orm(artwork)
                recommendation_response = RecommendationResponse(
                    artwork=artwork_response,
                    score=score,
                    recommendation_id=recommendation_id,
                    position=i + 1,
                    reason=self._generate_recommendation_reason(artwork, user_profile)
                )
                response.append(recommendation_response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating artwork recommendations: {str(e)}")
            raise
    
    async def get_artist_recommendations(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[RecommendationResponse]:
        """
        Get personalized artist recommendations for a user
        """
        try:
            # Get user preference profile
            user_profile = await self._get_user_profile(user_id)
            
            # Get artists based on liked artworks styles
            artist_recommendations = await self.recommendation_engine.recommend_artists(
                user_profile=user_profile,
                limit=limit
            )
            
            # Convert to response format (using representative artwork)
            response = []
            for i, (artist_id, score, representative_artwork) in enumerate(artist_recommendations):
                if representative_artwork:
                    artwork_response = ArtworkResponse.from_orm(representative_artwork)
                    recommendation_response = RecommendationResponse(
                        artwork=artwork_response,
                        score=score,
                        recommendation_id=str(uuid.uuid4()),
                        position=i + 1,
                        reason=f"Recommended artist based on your preferences"
                    )
                    response.append(recommendation_response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating artist recommendations: {str(e)}")
            raise
    
    async def record_feedback(
        self,
        user_id: str,
        artwork_id: str,
        feedback_type: str
    ):
        """
        Record user feedback for recommendation improvements
        """
        try:
            if feedback_type in ["like", "dislike"]:
                # Record or update like
                existing_like = self.db.query(UserLike).filter(
                    UserLike.userId == user_id,
                    UserLike.artworkId == artwork_id
                ).first()
                
                if existing_like:
                    existing_like.isLike = (feedback_type == "like")
                    existing_like.updatedAt = datetime.utcnow()
                else:
                    new_like = UserLike(
                        userId=user_id,
                        artworkId=artwork_id,
                        isLike=(feedback_type == "like"),
                        context={"source": "recommendation"}
                    )
                    self.db.add(new_like)
            
            elif feedback_type == "click":
                # Update recommendation history
                rec_history = self.db.query(RecommendationHistory).filter(
                    RecommendationHistory.userId == user_id,
                    RecommendationHistory.artworkId == artwork_id
                ).first()
                
                if rec_history:
                    rec_history.wasClicked = True
                    rec_history.clickedAt = datetime.utcnow()
            
            elif feedback_type == "view":
                # Update recommendation history
                rec_history = self.db.query(RecommendationHistory).filter(
                    RecommendationHistory.userId == user_id,
                    RecommendationHistory.artworkId == artwork_id
                ).first()
                
                if rec_history:
                    rec_history.wasViewed = True
                    rec_history.viewedAt = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"Recorded {feedback_type} feedback for user {user_id} on artwork {artwork_id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error recording feedback: {str(e)}")
            raise
    
    async def _get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Get user preference profile based on interaction history
        """
        # Get user likes
        likes = self.db.query(UserLike).filter(
            UserLike.userId == user_id,
            UserLike.isLike == True
        ).all()
        
        # Analyze preferences
        categories = {}
        styles = {}
        
        for like in likes:
            artwork = like.artwork
            if artwork.category:
                categories[artwork.category] = categories.get(artwork.category, 0) + 1
            if artwork.style:
                styles[artwork.style] = styles.get(artwork.style, 0) + 1
        
        return {
            "user_id": user_id,
            "preferred_categories": categories,
            "preferred_styles": styles,
            "total_likes": len(likes),
            "profile_strength": min(len(likes) / 10, 1.0)  # 0-1 score
        }
    
    def _get_seen_artworks(self, user_id: str) -> List[str]:
        """
        Get list of artwork IDs already seen by user
        """
        seen_ids = []
        
        # From likes
        likes = self.db.query(UserLike.artworkId).filter(UserLike.userId == user_id).all()
        seen_ids.extend([like.artworkId for like in likes])
        
        # From recommendation history
        history = self.db.query(RecommendationHistory.artworkId).filter(
            RecommendationHistory.userId == user_id
        ).all()
        seen_ids.extend([rec.artworkId for rec in history])
        
        return list(set(seen_ids))
    
    async def _record_recommendations(
        self,
        user_id: str,
        recommendations: List[tuple],
        recommendation_id: str
    ):
        """
        Record recommendations in history for tracking
        """
        try:
            for position, (artwork, score) in enumerate(recommendations):
                rec_history = RecommendationHistory(
                    userId=user_id,
                    artworkId=artwork.id,
                    recommendationId=recommendation_id,
                    algorithmVersion="v1.0",
                    position=position + 1,
                    score=score
                )
                self.db.add(rec_history)
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error recording recommendations: {str(e)}")
            raise
    
    def _generate_recommendation_reason(
        self,
        artwork: Artwork,
        user_profile: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable reason for recommendation
        """
        reasons = []
        
        if artwork.category in user_profile.get("preferred_categories", {}):
            reasons.append(f"matches your interest in {artwork.category}")
        
        if artwork.style in user_profile.get("preferred_styles", {}):
            reasons.append(f"similar to {artwork.style} works you've liked")
        
        if not reasons:
            reasons.append("discovered based on your general preferences")
        
        return "Recommended because it " + " and ".join(reasons)