import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.config import settings
from backend.database import get_db
from backend.deps import get_current_user
from backend.models.user import User
from backend.models.conversation import Conversation, Message
from backend.services.pdf_service import extract_text_from_pdf
from backend.services.storage_service import save_resume, get_user_documents

router = APIRouter(prefix="/conversations", tags=["Resume"])
user_resumes_router = APIRouter(prefix="/user-resumes", tags=["User Resumes"])


class SelectResumeRequest(BaseModel):
    filename: str


@user_resumes_router.get("")
async def list_user_resumes(current_user: User = Depends(get_current_user)):
    """List all previously uploaded resumes for the current user."""
    docs = get_user_documents(current_user.id, "resumes")
    return [d for d in docs if d["filename"].lower().endswith(".pdf")]


@user_resumes_router.delete("/{filename}")
async def delete_resume(filename: str, current_user: User = Depends(get_current_user)):
    """Delete a previously uploaded resume by filename."""
    filepath = os.path.join(settings.DATA_DIR, "users", current_user.id, "resumes", filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
        
    try:
        os.remove(filepath)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete resume: {str(e)}")
        
    return {"message": "Resume deleted successfully"}


@user_resumes_router.post("/upload")
async def upload_independent_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload a PDF resume independently of a conversation."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are accepted")

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
    if len(file_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds the 20MB limit")

    try:
        resume_text = extract_text_from_pdf(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to extract text from PDF: {str(e)}")

    if not resume_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not extract any text from the PDF.")

    save_resume(current_user.id, file.filename, file_bytes)

    return {
        "message": "Resume uploaded successfully",
        "filename": file.filename,
    }


@router.post("/{conversation_id}/resume")
async def upload_resume(
    conversation_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a PDF resume to a conversation. Extracts text and stores file."""
    # Validate conversation belongs to user
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
    )
    convo = result.scalar_one_or_none()
    if not convo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are accepted")

    # Read and process the file
    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
    if len(file_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds the 20MB limit")

    # Extract text from PDF
    try:
        resume_text = extract_text_from_pdf(file_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to extract text from PDF: {str(e)}",
        )

    if not resume_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract any text from the PDF. Please try a different file.",
        )

    # Save file to disk
    save_resume(current_user.id, file.filename, file_bytes)

    # Update conversation
    convo.resume_filename = file.filename
    convo.resume_text = resume_text
    convo.updated_at = datetime.now(timezone.utc)

    # Add a system message recording the upload
    msg = Message(
        conversation_id=conversation_id,
        role="system",
        content=f"Resume uploaded: {file.filename}",
        metadata_={"type": "resume_upload", "filename": file.filename},
    )
    db.add(msg)
    await db.commit()

    return {
        "message": "Resume uploaded and text extracted successfully",
        "filename": file.filename,
        "text_preview": resume_text[:500] + ("..." if len(resume_text) > 500 else ""),
        "text_length": len(resume_text),
    }


@router.post("/{conversation_id}/resume/select")
async def select_resume(
    conversation_id: str,
    body: SelectResumeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Select a previously uploaded resume by filename and attach to conversation."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
    )
    convo = result.scalar_one_or_none()
    if not convo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    filepath = os.path.join(settings.DATA_DIR, "users", current_user.id, "resumes", body.filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    try:
        with open(filepath, "rb") as f:
            file_bytes = f.read()
        resume_text = extract_text_from_pdf(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to read resume: {str(e)}")

    if not resume_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not extract text from the selected PDF.")

    convo.resume_filename = body.filename
    convo.resume_text = resume_text
    convo.updated_at = datetime.now(timezone.utc)

    msg = Message(
        conversation_id=conversation_id,
        role="system",
        content=f"Selected existing resume: {body.filename}",
        metadata_={"type": "resume_select", "filename": body.filename},
    )
    db.add(msg)
    await db.commit()

    return {
        "message": "Resume selected and text extracted successfully",
        "filename": body.filename,
    }
