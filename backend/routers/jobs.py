import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import get_current_user
from backend.models.user import User
from backend.models.conversation import Conversation, Message
from backend.schemas.job import JobSearchRequest, JobSearchResponse, JobResult
from backend.services.job_service import fetch_linkedin_jobs, parse_job_item
from backend.services.agent_service import run_hiring_score

router = APIRouter(prefix="/conversations", tags=["Jobs"])


@router.post("/{conversation_id}/search-jobs", response_model=JobSearchResponse)
def search_jobs(
    conversation_id: str,
    body: JobSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search for jobs and score each against the uploaded resume."""
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
            detail="Please upload a resume first before searching for jobs.",
        )

    # Fetch jobs from LinkedIn
    raw_jobs = fetch_linkedin_jobs(body.keyword, body.location, body.results_per_page)

    # Parse and score each job if results exist
    results = []
    if raw_jobs:
        for item in raw_jobs:
            parsed = parse_job_item(item)

            # Run hiring score agent
            try:
                score_result = run_hiring_score(parsed["job_summary"], convo.resume_text)
                parsed["hiring_score"] = score_result["score"]
                parsed["hiring_score_reasoning"] = score_result["reasoning"]
            except Exception:
                parsed["hiring_score"] = None
                parsed["hiring_score_reasoning"] = "Score unavailable"

            results.append(JobResult(**parsed))

        # Sort by hiring score (highest first)
        results.sort(key=lambda j: j.hiring_score or 0, reverse=True)

    # Save search as a user message + results as assistant message
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=f"Search jobs: {body.keyword} in {body.location}",
        metadata_={"type": "job_search", "keyword": body.keyword, "location": body.location},
    )
    db.add(user_msg)

    assistant_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=f"Found {len(results)} jobs for '{body.keyword}' in {body.location}",
        metadata_={
            "type": "job_results",
            "jobs": [r.model_dump() for r in results],
        },
    )
    db.add(assistant_msg)

    # Update conversation title if it's still default
    if convo.title == "New Conversation":
        convo.title = f"{body.keyword} — {body.location}"
    convo.updated_at = datetime.now(timezone.utc)
    db.commit()

    return JobSearchResponse(jobs=results, total=len(results))
