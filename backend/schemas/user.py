from pydantic import BaseModel
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

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    """Request body for updating user profile."""
    name: Optional[str] = None
    picture_url: Optional[str] = None
    skills: Optional[str] = None
    role: Optional[str] = None  # "job_seeker" or "hr"


class GoogleAuthRequest(BaseModel):
    """Request body for Google OAuth login."""
    code: str
    role: Optional[str] = "job_seeker"  # "job_seeker" or "hr"


class AuthTokenResponse(BaseModel):
    """JWT token response after successful auth."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
