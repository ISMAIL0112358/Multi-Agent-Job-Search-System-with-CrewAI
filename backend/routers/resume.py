import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import get_current_user
from backend.models.user import User
from backend.models.conversation import Conversation, Message
from backend.services.pdf_service import extract_text_from_pdf
from backend.services.storage_service import save_resume

router = APIRouter(prefix="/conversations", tags=["Resume"])


@router.post("/{conversation_id}/resume")
async def upload_resume(
    conversation_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a PDF resume to a conversation. Extracts text and stores file."""
    # Validate conversation belongs to user
    convo = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not convo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are accepted")

    # Read and process the file
    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

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
    db.commit()

    # Add a system message recording the upload
    msg = Message(
        conversation_id=conversation_id,
        role="system",
        content=f"Resume uploaded: {file.filename}",
        metadata_={"type": "resume_upload", "filename": file.filename},
    )
    db.add(msg)
    db.commit()

    return {
        "message": "Resume uploaded and text extracted successfully",
        "filename": file.filename,
        "text_preview": resume_text[:500] + ("..." if len(resume_text) > 500 else ""),
        "text_length": len(resume_text),
    }
