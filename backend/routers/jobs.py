import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.deps import get_current_user
from backend.models.user import User
from backend.models.conversation import Conversation, Message
from backend.schemas.job import JobSearchRequest, JobSearchResponse, JobResult
from backend.services.job_service import fetch_linkedin_jobs, parse_job_item
from backend.services.agent_service import run_hiring_score

router = APIRouter(prefix="/conversations", tags=["Jobs"])


async def _score_single_job(parsed: dict, resume_text: str, user_skills: str | None, company_preference: str | None) -> tuple[JobResult, int]:
    """Score a single parsed job item concurrently in a non-blocking thread."""
    tokens = 0
    try:
        score_result = await asyncio.to_thread(
            run_hiring_score,
            parsed["job_summary"],
            resume_text,
            user_skills,
            company_preference,
        )
        parsed["hiring_score"] = score_result["score"]
        parsed["hiring_score_reasoning"] = score_result["reasoning"]
        tokens = score_result.get("tokens", 0)
    except Exception as e:
        parsed["hiring_score"] = None
        parsed["hiring_score_reasoning"] = f"Score unavailable: {e}"
    return JobResult(**parsed), tokens


import time
from backend.services.token_service import add_tokens_async

@router.post("/{conversation_id}/search-jobs", response_model=JobSearchResponse)
async def search_jobs(
    conversation_id: str,
    body: JobSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search for jobs and score each against the uploaded resume asynchronously."""
    start_time = time.time()

    # Validate conversation
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
    )
    convo = result.scalar_one_or_none()
    if not convo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    if not convo.resume_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload a resume first before searching for jobs.",
        )

    # Fetch jobs from LinkedIn asynchronously using keyword list
    keywords_input = body.keyword_list if body.keyword_list else body.keyword
    company_pref_str = ", ".join(body.company_preference_list) if body.company_preference_list else (body.company_preference if isinstance(body.company_preference, str) else None)

    raw_jobs = await fetch_linkedin_jobs(keywords_input, body.location, body.results_per_page)

    # Parse and score each job concurrently if results exist
    results = []
    if raw_jobs:
        score_tasks = [
            _score_single_job(
                parse_job_item(item),
                convo.resume_text,
                current_user.skills,
                company_pref_str,
            )
            for item in raw_jobs
        ]
        score_outputs = await asyncio.gather(*score_tasks)
        results = [r for r, _ in score_outputs]
        total_tokens = sum(t for _, t in score_outputs)

        # Sort by hiring score (highest first)
        results.sort(key=lambda j: j.hiring_score or 0, reverse=True)

        if total_tokens > 0:
            await add_tokens_async(current_user.id, generative_tokens=total_tokens)

    search_duration = round(time.time() - start_time, 2)

    # Save search as a user message + results as assistant message
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=f"Search jobs: {body.keyword} in {body.location}{f' (Preference: {body.company_preference})' if body.company_preference else ''}",
        metadata_={
            "type": "job_search", 
            "keyword": body.keyword, 
            "location": body.location, 
            "company_preference": body.company_preference,
            "search_time_seconds": search_duration
        },
    )
    db.add(user_msg)

    assistant_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=f"Found {len(results)} jobs for '{body.keyword}' in {body.location}",
        metadata_={
            "type": "job_results",
            "jobs": [r.model_dump() for r in results],
            "search_time_seconds": search_duration,
        },
    )
    db.add(assistant_msg)

    # Update conversation title if it's still default
    if convo.title == "New Conversation":
        convo.title = f"{body.keyword} — {body.location}"
    convo.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return JobSearchResponse(jobs=results, total=len(results), search_time_seconds=search_duration)
