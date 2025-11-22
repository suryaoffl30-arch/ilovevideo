from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application configuration loaded from environment variables"""
    
    app_port: int = 8000
    download_dir: str = "./downloads"
    debug: bool = False
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    max_video_size_mb: int = 500
    playwright_timeout: int = 30000
    enable_ffmpeg_conversion: bool = True
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

# Ensure download directory exists
os.makedirs(settings.download_dir, exist_ok=True)
