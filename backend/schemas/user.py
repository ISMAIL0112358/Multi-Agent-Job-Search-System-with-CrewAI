from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class UserResponse(BaseModel):
    """User info returned to the frontend."""
    id: str
    email: str
    name: str
    picture_url: Optional[str] = None
    skills: Optional[str] = None
    role: str = "job_seeker"
    created_at: datetime

    # UAT limits mapping
    max_resumes: int = 50
    resumes_count: int = 0
    max_jds: int = 10
    jds_count: int = 0
    max_screenings: int = 50
    screenings_count: int = 0
    max_conversations: int = 10
    conversations_count: int = 0
    max_messages_per_conversation: int = 50

    # Cumulative Token Tracking
    generative_tokens_count: int = 0
    embedding_tokens_count: int = 0

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Request body for updating user profile."""
    name: Optional[str] = None
    picture_url: Optional[str] = None
    skills: Optional[str] = None
    role: Optional[str] = None  # "job_seeker" or "hr"


class GoogleAuthRequest(BaseModel):
    """Request body for Google OpenID Connect ID Token authentication."""
    id_token: str = Field(..., description="Google signed OpenID Connect ID Token (JWT)")
    role: Optional[str] = "job_seeker"  # "job_seeker" or "hr"


class AuthTokenResponse(BaseModel):
    """OAuth 2.0 / OpenID Connect standard Bearer token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
