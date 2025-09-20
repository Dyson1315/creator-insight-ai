"""
Core recommendation engine using machine learning
"""

import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import logging

from app.models.database import Artwork

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """
    Hybrid recommendation engine combining collaborative and content-based filtering
    """
    
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.model_loaded = False
        self._load_models()
    
    def _load_models(self):
        """Load pre-trained models"""
        try:
            # TODO: Load actual trained models
            # For now, initialize with placeholder
            self.model_loaded = True
            logger.info("Recommendation models loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load pre-trained models: {str(e)}")
            self.model_loaded = False
    
    async def recommend_artworks(
        self,
        user_profile: Dict[str, Any],
        candidate_artworks: List[Artwork],
        limit: int = 10
    ) -> List[Tuple[Artwork, float]]:
        """
        Generate artwork recommendations using hybrid approach
        """
        try:
            if not candidate_artworks:
                return []
            
            # Content-based scoring
            content_scores = self._content_based_scoring(user_profile, candidate_artworks)
            
            # Collaborative filtering scores (placeholder)
            collaborative_scores = self._collaborative_filtering_scoring(user_profile, candidate_artworks)
            
            # Popularity-based scoring
            popularity_scores = self._popularity_based_scoring(candidate_artworks)
            
            # Combine scores with weights
            final_scores = []
            for i, artwork in enumerate(candidate_artworks):
                content_weight = 0.5
                collaborative_weight = 0.3
                popularity_weight = 0.2
                
                # Adjust weights based on user profile strength
                profile_strength = user_profile.get("profile_strength", 0.0)
                if profile_strength < 0.3:
                    # New users: rely more on popularity
                    content_weight = 0.3
                    collaborative_weight = 0.2
                    popularity_weight = 0.5
                
                final_score = (
                    content_scores[i] * content_weight +
                    collaborative_scores[i] * collaborative_weight +
                    popularity_scores[i] * popularity_weight
                )
                
                final_scores.append((artwork, final_score))
            
            # Sort by score and return top recommendations
            final_scores.sort(key=lambda x: x[1], reverse=True)
            return final_scores[:limit]
            
        except Exception as e:
            logger.error(f"Error in artwork recommendation: {str(e)}")
            # Fallback: return random selection
            import random
            random.shuffle(candidate_artworks)
            return [(artwork, 0.5) for artwork in candidate_artworks[:limit]]
    
    async def recommend_artists(
        self,
        user_profile: Dict[str, Any],
        limit: int = 10
    ) -> List[Tuple[str, float, Optional[Artwork]]]:
        """
        Generate artist recommendations
        """
        try:
            # TODO: Implement artist recommendation logic
            # For now, return placeholder
            return []
            
        except Exception as e:
            logger.error(f"Error in artist recommendation: {str(e)}")
            return []
    
    def _content_based_scoring(
        self,
        user_profile: Dict[str, Any],
        artworks: List[Artwork]
    ) -> List[float]:
        """
        Score artworks based on content similarity to user preferences
        """
        scores = []
        preferred_categories = user_profile.get("preferred_categories", {})
        preferred_styles = user_profile.get("preferred_styles", {})
        
        for artwork in artworks:
            score = 0.0
            
            # Category preference score
            if artwork.category and artwork.category in preferred_categories:
                category_count = preferred_categories[artwork.category]
                total_likes = user_profile.get("total_likes", 1)
                score += (category_count / total_likes) * 0.6
            
            # Style preference score
            if artwork.style and artwork.style in preferred_styles:
                style_count = preferred_styles[artwork.style]
                total_likes = user_profile.get("total_likes", 1)
                score += (style_count / total_likes) * 0.4
            
            # Tag similarity (if available)
            if artwork.tags and len(artwork.tags) > 0:
                # TODO: Implement tag-based similarity
                pass
            
            # AI feature similarity (if available)
            if artwork.aiFeatureVector:
                # TODO: Implement feature vector similarity
                pass
            
            scores.append(min(score, 1.0))  # Cap at 1.0
        
        return scores
    
    def _collaborative_filtering_scoring(
        self,
        user_profile: Dict[str, Any],
        artworks: List[Artwork]
    ) -> List[float]:
        """
        Score artworks based on collaborative filtering
        """
        # TODO: Implement actual collaborative filtering
        # For now, return neutral scores
        return [0.5] * len(artworks)
    
    def _popularity_based_scoring(
        self,
        artworks: List[Artwork]
    ) -> List[float]:
        """
        Score artworks based on popularity metrics
        """
        scores = []
        
        for artwork in artworks:
            score = 0.5  # Base score
            
            # Recent artworks get slight boost
            if artwork.createdAt:
                from datetime import datetime, timedelta
                age_days = (datetime.utcnow() - artwork.createdAt).days
                if age_days < 30:
                    score += 0.1
                elif age_days < 90:
                    score += 0.05
            
            # Portfolio artworks get boost
            if artwork.isPortfolio:
                score += 0.2
            
            scores.append(min(score, 1.0))
        
        return scores
    
    def extract_image_features(self, image_data: bytes) -> np.ndarray:
        """
        Extract features from image data using deep learning
        """
        try:
            # TODO: Implement actual feature extraction
            # For now, return dummy features
            return np.random.rand(512)  # 512-dimensional feature vector
            
        except Exception as e:
            logger.error(f"Error extracting image features: {str(e)}")
            return np.zeros(512)
    
    def find_similar_images(
        self,
        query_features: np.ndarray,
        image_database: List[Tuple[str, np.ndarray]],
        threshold: float = 0.8
    ) -> List[Tuple[str, float]]:
        """
        Find similar images based on feature similarity
        """
        try:
            if len(image_database) == 0:
                return []
            
            # Extract features for comparison
            db_features = np.array([features for _, features in image_database])
            
            # Calculate cosine similarity
            similarities = cosine_similarity([query_features], db_features)[0]
            
            # Filter by threshold and sort
            similar_images = []
            for i, similarity in enumerate(similarities):
                if similarity >= threshold:
                    artwork_id, _ = image_database[i]
                    similar_images.append((artwork_id, similarity))
            
            # Sort by similarity score
            similar_images.sort(key=lambda x: x[1], reverse=True)
            
            return similar_images
            
        except Exception as e:
            logger.error(f"Error finding similar images: {str(e)}")
            return []