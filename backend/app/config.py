"""
Configuration settings for the Simple Cloud Photo Gallery App.
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    
    # Database
    DATABASE_URL: str = "sqlite:///./photo_gallery.db"
    
    # API Settings
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8002
    API_TITLE: str = "Simple Cloud Photo Gallery API"
    API_VERSION: str = "1.0.0"
    
    # CORS Settings
    CORS_ORIGINS: list = ["http://localhost:3001", "http://localhost:5173", "http://127.0.0.1:3001", "http://127.0.0.1:5173"]
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "uploads"
    ALLOWED_EXTENSIONS: set = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}
    
    # AI Integration Settings
    OPENROUTER_API_KEY: Optional[str] = ""
    AI_MODEL: str = "anthropic/claude-3.5-sonnet"
    AI_MAX_RETRIES: int = 3
    AI_RETRY_DELAY: float = 1.0
    AI_TIMEOUT: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Validate required settings
if not settings.OPENROUTER_API_KEY:
    print("WARNING: OPENROUTER_API_KEY not found. AI analysis will be disabled.")
    print("Please set OPENROUTER_API_KEY in your .env file or environment variables.")
