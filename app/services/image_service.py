"""
Image service for processing and analyzing artwork images
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import logging
import asyncio

from app.core.database import get_db
from app.models.database import Artwork, ImageFeature
from app.models.schemas import ImageAnalysisResponse, SimilarImageResponse, ArtworkResponse
from app.ml.image_processor import ImageProcessor

logger = logging.getLogger(__name__)

class ImageService:
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
        self.image_processor = ImageProcessor()
    
    async def analyze_image(self, image_data: bytes, filename: str) -> ImageAnalysisResponse:
        """
        Analyze uploaded image and extract features
        """
        try:
            # Process image
            analysis_result = await self.image_processor.analyze_image(image_data, filename)
            
            # Convert to response model
            response = ImageAnalysisResponse(**analysis_result)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in image analysis service: {str(e)}")
            raise
    
    async def find_similar_images(
        self,
        image_data: bytes,
        limit: int = 10,
        threshold: float = 0.8
    ) -> List[SimilarImageResponse]:
        """
        Find similar images in the database
        """
        try:
            from PIL import Image
            import io
            
            # Load and process query image
            query_image = Image.open(io.BytesIO(image_data))
            if query_image.mode != 'RGB':
                query_image = query_image.convert('RGB')
            
            # Extract features from query image
            query_features = await self.image_processor.extract_features(query_image)
            
            # Get all artworks with features
            artworks_with_features = self.db.query(Artwork, ImageFeature).join(
                ImageFeature, Artwork.id == ImageFeature.artworkId
            ).filter(Artwork.isPublic == True).all()
            
            # Calculate similarities
            similarities = []
            for artwork, image_feature in artworks_with_features:
                if image_feature.cnn_features:
                    # Convert stored features back to numpy array
                    stored_features = image_feature.cnn_features
                    if isinstance(stored_features, list):
                        import numpy as np
                        stored_features = np.array(stored_features)
                    
                    # Calculate similarity
                    similarity = self.image_processor.calculate_image_similarity(
                        query_features, stored_features
                    )
                    
                    if similarity >= threshold:
                        similarities.append((artwork, similarity))
            
            # Sort by similarity and limit results
            similarities.sort(key=lambda x: x[1], reverse=True)
            similarities = similarities[:limit]
            
            # Convert to response format
            response = []
            for artwork, similarity in similarities:
                artwork_response = ArtworkResponse.from_orm(artwork)
                similar_image = SimilarImageResponse(
                    artwork=artwork_response,
                    similarity_score=similarity,
                    matching_features=["color", "style", "composition"]  # Placeholder
                )
                response.append(similar_image)
            
            return response
            
        except Exception as e:
            logger.error(f"Error finding similar images: {str(e)}")
            raise
    
    async def extract_artwork_features(self, artwork_id: str) -> List[float]:
        """
        Extract and store features for existing artwork
        """
        try:
            # Get artwork
            artwork = self.db.query(Artwork).filter(Artwork.id == artwork_id).first()
            if not artwork:
                raise ValueError(f"Artwork {artwork_id} not found")
            
            # TODO: Download image from artwork.imageUrl
            # For now, skip actual download and return dummy features
            
            # Extract features (placeholder)
            import numpy as np
            features = np.random.rand(512).tolist()
            
            # Store features in database
            existing_feature = self.db.query(ImageFeature).filter(
                ImageFeature.artworkId == artwork_id
            ).first()
            
            if existing_feature:
                existing_feature.cnn_features = features
                existing_feature.model_version = "v1.0"
                existing_feature.extraction_method = "resnet50"
            else:
                new_feature = ImageFeature(
                    artworkId=artwork_id,
                    cnn_features=features,
                    model_version="v1.0",
                    extraction_method="resnet50"
                )
                self.db.add(new_feature)
            
            self.db.commit()
            
            return features
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error extracting artwork features: {str(e)}")
            raise
    
    async def batch_process_artworks(self, batch_size: int = 10):
        """
        Process artworks in batches to extract features
        """
        try:
            # Get artworks without features
            artworks_without_features = self.db.query(Artwork).outerjoin(
                ImageFeature, Artwork.id == ImageFeature.artworkId
            ).filter(ImageFeature.id.is_(None)).limit(batch_size).all()
            
            logger.info(f"Processing {len(artworks_without_features)} artworks")
            
            # Process each artwork
            for artwork in artworks_without_features:
                try:
                    await self.extract_artwork_features(artwork.id)
                    logger.info(f"Processed artwork {artwork.id}")
                except Exception as e:
                    logger.error(f"Error processing artwork {artwork.id}: {str(e)}")
                    continue
            
            logger.info("Batch processing completed")
            
        except Exception as e:
            logger.error(f"Error in batch processing: {str(e)}")
            raise
    
    async def update_artwork_features(self, artwork_id: str, features: Dict[str, Any]):
        """
        Update stored features for an artwork
        """
        try:
            image_feature = self.db.query(ImageFeature).filter(
                ImageFeature.artworkId == artwork_id
            ).first()
            
            if image_feature:
                if features.get('cnn_features'):
                    image_feature.cnn_features = features['cnn_features']
                if features.get('clip_features'):
                    image_feature.clip_features = features['clip_features']
                if features.get('color_histogram'):
                    image_feature.color_histogram = features['color_histogram']
                
                self.db.commit()
                logger.info(f"Updated features for artwork {artwork_id}")
            else:
                logger.warning(f"No features found for artwork {artwork_id}")
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating artwork features: {str(e)}")
            raise