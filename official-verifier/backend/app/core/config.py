"""Configuration management."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    ENV: str = "dev"
    DATABASE_DSN: str
    REDIS_URL: str
    SECRET_KEY: str
    SENTRY_DSN: Optional[str] = None
    ITUNES_COUNTRY: str = "US"
    RATE_LIMIT_FREE_PER_MIN: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
