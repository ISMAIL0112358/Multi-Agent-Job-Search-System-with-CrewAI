import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


def _load_aws_secrets():
    secret_name = os.getenv("AWS_SECRET_NAME")
    if not secret_name:
        return

    region_name = os.getenv("AWS_REGION") or "us-east-1"
    try:
        import boto3
        import json

        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )

        response = client.get_secret_value(SecretId=secret_name)
        if 'SecretString' in response:
            secrets = json.loads(response['SecretString'])
            for key, val in secrets.items():
                # Load them into os.environ so Pydantic automatically picks them up
                os.environ[key] = str(val)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(
            f"Failed to load secrets from AWS Secrets Manager ({secret_name}): {e}"
        )


_load_aws_secrets()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID") or os.getenv("VITE_GOOGLE_CLIENT_ID") or ""
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET") or ""

    # API Keys & Models
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL_NAME: str = "gemini/gemini-3.5-flash"
    USAJOBS_API_KEY: str = ""
    AGENTOPS_API_KEY: str = ""

    # JWT
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # Environment (local vs prod)
    ENV: str = os.getenv("ENV") or "prod"

    # Local Ollama Settings
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434"
    LOCAL_LLM_MODEL: str = os.getenv("LOCAL_LLM_MODEL") or "gemma4"
    LOCAL_EMBEDDING_MODEL: str = os.getenv("LOCAL_EMBEDDING_MODEL") or "embeddinggemma"

    # Database
    DATABASE_URL: str = "sqlite:///./data/app.db"

    # File Storage
    DATA_DIR: str = "data"
    STORAGE_PROVIDER: str = os.getenv("STORAGE_PROVIDER") or "local"
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME") or ""
    AWS_REGION: str = os.getenv("AWS_REGION") or "us-east-1"

    # Vector Database (ChromaDB / pgvector)
    CHROMA_PERSIST_DIR: str = "data/chroma"
    VECTOR_STORE_PROVIDER: str = os.getenv("VECTOR_STORE_PROVIDER") or "chroma"

    # LangSmith (optional — for tracing LangChain calls)
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "hr-dashboard"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
