from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "BotHub API"
    DEBUG: bool = False
    FRONTEND_URL: str = "http://localhost:3000"

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/bothub"

    # Security
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # Feishu (飞书)
    FEISHU_APP_ID: str = ""
    FEISHU_APP_SECRET: str = ""
    FEISHU_REDIRECT_URI: str = "http://localhost:3000/oauth/feishu/callback"

    # File Storage (OSS/S3)
    STORAGE_TYPE: str = "local"  # local, oss, s3
    STORAGE_BUCKET: str = ""
    STORAGE_ENDPOINT: str = ""
    STORAGE_ACCESS_KEY: str = ""
    STORAGE_SECRET_KEY: str = ""

    def get_cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
