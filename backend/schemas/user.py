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
    created_at: datetime

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    """Request body for updating user profile."""
    name: Optional[str] = None
    picture_url: Optional[str] = None
    skills: Optional[str] = None


class GoogleAuthRequest(BaseModel):
    """Request body for Google OAuth login."""
    code: str


class AuthTokenResponse(BaseModel):
    """JWT token response after successful auth."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
