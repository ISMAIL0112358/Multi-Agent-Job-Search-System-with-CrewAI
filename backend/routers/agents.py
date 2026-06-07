import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import get_current_user
from backend.models.user import User
from backend.models.conversation import Conversation, Message
from backend.schemas.job import JobAnalysisRequest, JobAnalysisResponse
from backend.services.agent_service import run_full_analysis
from backend.services.storage_service import save_cover_letter, save_generated_resume

router = APIRouter(prefix="/conversations", tags=["Agents"])


@router.post("/{conversation_id}/analyze-job", response_model=JobAnalysisResponse)
def analyze_job(
    conversation_id: str,
    body: JobAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run full CrewAI analysis on a job: JD summary, resume tweaks, cover letter."""
    # Validate conversation
    convo = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not convo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    if not convo.resume_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload a resume first.",
        )

    # Run the full analysis pipeline
    try:
        result = run_full_analysis(body.job_data, convo.resume_text, body.user_bio)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent pipeline failed: {str(e)}",
        )

    # Save generated documents to user's folders
    job_title = body.job_data.get("PositionTitle", body.job_data.get("position_title", "Unknown"))

    if result["cover_letter"]:
        save_cover_letter(current_user.id, job_title, result["cover_letter"])

    if result["resume_tweaks"]:
        save_generated_resume(current_user.id, job_title, result["resume_tweaks"])

    # Save as conversation messages
    assistant_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=json.dumps({
            "jd_summary": result["jd_summary"],
            "resume_tweaks": result["resume_tweaks"],
            "cover_letter": result["cover_letter"],
            "hiring_score": result["hiring_score"],
            "hiring_score_reasoning": result["hiring_score_reasoning"],
        }),
        metadata_={
            "type": "job_analysis",
            "job_title": job_title,
        },
    )
    db.add(assistant_msg)

    convo.updated_at = datetime.now(timezone.utc)
    db.commit()

    return JobAnalysisResponse(**result)
