from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.deps import get_current_user
from backend.models.user import User
from backend.models.conversation import Conversation, Message
from backend.schemas.conversation import (
    ConversationCreate,
    ConversationSummary,
    ConversationDetail,
)

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get("", response_model=List[ConversationSummary])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all conversations for the current user, newest first."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
    )
    convos = result.scalars().all()
    return [ConversationSummary.model_validate(c) for c in convos]


@router.post("", response_model=ConversationDetail, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Enforce conversation limit safeguard
    if current_user.conversations_count >= current_user.max_conversations:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Conversation limit exceeded. You can create up to {current_user.max_conversations} conversations (Current: {current_user.conversations_count})."
        )

    convo = Conversation(
        user_id=current_user.id,
        title=body.title or "New Conversation",
    )
    db.add(convo)
    
    # Increment historical conversations count
    current_user.conversations_count += 1
    
    await db.commit()
    await db.refresh(convo)
    
    # Load relationships for response model
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == convo.id)
    )
    loaded_convo = result.scalar_one()
    return ConversationDetail.model_validate(loaded_convo)


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a conversation with all its messages."""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
    )
    convo = result.scalar_one_or_none()
    if not convo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return ConversationDetail.model_validate(convo)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation and all its messages."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
    )
    convo = result.scalar_one_or_none()
    if not convo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    await db.delete(convo)
    await db.commit()
