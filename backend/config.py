import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID") or os.getenv("VITE_GOOGLE_CLIENT_ID") or ""
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET") or ""

    # API Keys
    GEMINI_API_KEY: str = ""
    USAJOBS_API_KEY: str = ""
    AGENTOPS_API_KEY: str = ""

    # JWT
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # Database
    DATABASE_URL: str = "sqlite:///./data/app.db"

    # File Storage
    DATA_DIR: str = "data"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
