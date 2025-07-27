from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Keys
    GEMINI_API_KEY: Optional[str] = os.getenv("AIzaSyCySUjbUHrdLz1teFok_nAePXLJnefHZM0")
    
    # Database
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = "eduview"
    
    # File Storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 500 * 1024 * 1024  # 500MB
    ALLOWED_VIDEO_EXTENSIONS: list = [".mp4", ".avi", ".mov", ".mkv"]
    
    # Analysis Settings
    FRAME_SAMPLE_RATE: int = 30  # Process every 30th frame
    AUDIO_CHUNK_DURATION: int = 5  # seconds
    
    # Scoring Weights
    BODY_LANGUAGE_WEIGHT: float = 0.25
    VOICE_WEIGHT: float = 0.25
    CONTENT_FLOW_WEIGHT: float = 0.25
    INTERACTION_WEIGHT: float = 0.25
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # İlgisiz alanları yoksay

settings = Settings() 