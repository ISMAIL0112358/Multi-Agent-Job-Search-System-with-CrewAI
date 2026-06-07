from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.config import settings

# Create the database directory if it doesn't exist
import os
os.makedirs(os.path.dirname(settings.DATABASE_URL.replace("sqlite:///", "")) or ".", exist_ok=True)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
