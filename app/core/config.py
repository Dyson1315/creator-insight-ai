"""
Application configuration settings
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # App settings
    APP_NAME: str = "Creator-VRidge AI Recommendation"
    DEBUG: bool = False
    VERSION: str = "1.0.0"
    
    # API settings
    API_V1_STR: str = "/api/v1"
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./creator_insight.db"
    
    # Cloudflare settings
    CLOUDFLARE_ACCOUNT_ID: Optional[str] = None
    CLOUDFLARE_API_TOKEN: Optional[str] = None
    CLOUDFLARE_R2_BUCKET: str = "creator-insight-images"
    CLOUDFLARE_KV_NAMESPACE: Optional[str] = None
    
    # Machine Learning settings
    ML_MODEL_PATH: str = "./models"
    IMAGE_FEATURE_DIM: int = 512
    BATCH_SIZE: int = 32
    
    # Cache settings
    CACHE_TTL: int = 3600  # 1 hour
    REDIS_URL: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()