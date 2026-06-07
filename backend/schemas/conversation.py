from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Any


class ConversationCreate(BaseModel):
    """Request body for creating a new conversation."""
    title: Optional[str] = "New Conversation"


class MessageResponse(BaseModel):
    """A single message within a conversation."""
    id: str
    role: str
    content: str
    metadata_: Optional[Any] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationSummary(BaseModel):
    """Conversation list item (without messages)."""
    id: str
    title: str
    resume_filename: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationDetail(BaseModel):
    """Full conversation with messages."""
    id: str
    title: str
    resume_filename: Optional[str] = None
    resume_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True
