"""
Image processing and analysis API endpoints
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List, Dict, Any
import logging

from app.services.image_service import ImageService
from app.models.schemas import ImageAnalysisResponse, SimilarImageResponse

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/analyze", response_model=ImageAnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    image_service: ImageService = Depends()
):
    """
    Analyze uploaded image and extract features
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await file.read()
        
        # Analyze image
        analysis_result = await image_service.analyze_image(image_data, file.filename)
        
        return analysis_result
    except Exception as e:
        logger.error(f"Error analyzing image: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/similar", response_model=List[SimilarImageResponse])
async def find_similar_images(
    file: UploadFile = File(...),
    limit: int = 10,
    threshold: float = 0.8,
    image_service: ImageService = Depends()
):
    """
    Find similar images based on uploaded image
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await file.read()
        
        # Find similar images
        similar_images = await image_service.find_similar_images(
            image_data, limit, threshold
        )
        
        return similar_images
    except Exception as e:
        logger.error(f"Error finding similar images: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/features/{artwork_id}")
async def extract_artwork_features(
    artwork_id: str,
    image_service: ImageService = Depends()
):
    """
    Extract features for existing artwork
    """
    try:
        features = await image_service.extract_artwork_features(artwork_id)
        return {"artwork_id": artwork_id, "features": features}
    except Exception as e:
        logger.error(f"Error extracting artwork features: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/stats")
async def get_image_stats():
    """
    Get image processing statistics
    """
    # TODO: Implement statistics collection
    return {
        "total_images_processed": 0,
        "average_processing_time": 0,
        "supported_formats": ["jpg", "jpeg", "png", "webp"]
    }