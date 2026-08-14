"""
HR Dashboard Router — all endpoints for the HR/Hiring Manager Dashboard.

Handles candidate management, job descriptions, AI screening, and vetting Q&A generation.
All endpoints require authenticated user with HR role.
"""
import asyncio
import logging
import uuid
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func

import re as re_module
from backend.config import settings

from backend.database import get_db
from backend.deps import require_hr_role
from backend.models.user import User
from backend.models.candidate import Candidate
from backend.models.job_description import JobDescription
from backend.models.screening_result import ScreeningResult
from backend.schemas.hr import (
    CandidateDetail,
    CandidateUploadResponse,
    StatusUpdate,
    JobDescriptionCreate,
    JobDescriptionUpdate,
    JobDescriptionResponse,
    ScreenRequest,
    ScreeningResultResponse,
    VettingRequest,
    VettingQuestionResponse,
    DashboardStats,
    TaskResponse,
)
from backend.tasks import process_bulk_resumes_task, run_ai_screening_task
from backend.services.pdf_service import extract_text_from_pdf
from backend.services.storage_service import save_candidate_resume, generate_candidate_resume_download_url
from backend.services.vector_service import VectorService
from backend.services.screening_service import ScreeningService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hr", tags=["HR Dashboard"])

ALLOWED_EXTENSIONS = {".pdf"}


def _process_single_resume(
    resume_text: str,
    source_label: str,
    category: str | None,
    screening_service: ScreeningService,
    vector_service: VectorService,
    current_user: User,
    db: Session,
    candidate_id: str | None = None,
) -> CandidateUploadResponse | None:
    """Process a single resume text into a Candidate record synchronously (used by Celery worker)."""
    if not resume_text or not resume_text.strip():
        logger.warning("Empty resume text for %s", source_label)
        return None

    # Extract candidate info via AI
    try:
        candidate_info = screening_service.extract_candidate_info(resume_text)
    except Exception as e:
        logger.warning("Failed to extract candidate info from %s: %s", source_label, e)
        candidate_info = {"name": source_label, "email": "", "phone": ""}

    if not candidate_id:
        candidate_id = str(uuid.uuid4())
    candidate = Candidate(
        id=candidate_id,
        name=candidate_info.get("name", "Unknown"),
        email=candidate_info.get("email", ""),
        phone=candidate_info.get("phone", ""),
        resume_filename=source_label,
        resume_text=resume_text,
        uploaded_by=current_user.id,
        status="new",
    )

    # Ingest into ChromaDB
    try:
        chroma_doc_id = vector_service.add_resume(candidate_id, resume_text)
        candidate.chroma_doc_id = chroma_doc_id
    except Exception as e:
        logger.error("Failed to ingest %s into vector store: %s", source_label, e)

    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    return CandidateUploadResponse(
        id=candidate.id,
        name=candidate.name,
        email=candidate.email,
        phone=candidate.phone,
        filename=candidate.resume_filename,
        status=candidate.status,
    )


# ══════════════════════════════════════════════════════════════════════
# Dashboard Stats
# ══════════════════════════════════════════════════════════════════════

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(require_hr_role),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregate stats for the HR dashboard header asynchronously."""
    total_candidates = current_user.resumes_count
    open_positions = current_user.jds_count

    shortlisted_res = await db.execute(
        select(func.count(Candidate.id)).where(
            Candidate.uploaded_by == current_user.id,
            Candidate.status == "shortlisted"
        )
    )
    shortlisted = shortlisted_res.scalar_one()

    hired_res = await db.execute(
        select(func.count(Candidate.id)).where(
            Candidate.uploaded_by == current_user.id,
            Candidate.status == "hired"
        )
    )
    hired = hired_res.scalar_one()

    return DashboardStats(
        total_candidates=total_candidates,
        open_positions=open_positions,
        shortlisted=shortlisted,
        hired=hired,
        max_resumes=current_user.max_resumes,
        max_jds=current_user.max_jds,
        max_screenings=current_user.max_screenings,
        screenings_count=current_user.screenings_count,
    )


# ══════════════════════════════════════════════════════════════════════
# Candidate Management
# ══════════════════════════════════════════════════════════════════════

@router.post("/candidates/upload", response_model=TaskResponse)
async def upload_candidates(
    files: list[UploadFile] = File(...),
    current_user: User = Depends(require_hr_role),
    db: AsyncSession = Depends(get_db),
):
    """Upload candidate resumes as PDFs asynchronously.
    Dispatches processing to a background Celery task.
    """
    if current_user.resumes_count + len(files) > current_user.max_resumes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Upload limit exceeded. You can upload up to {current_user.max_resumes} resumes (Current: {current_user.resumes_count})."
        )

    files_data = []

    for file in files:
        if not file.filename:
            continue
        ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            logger.warning("Skipping unsupported file type: %s", file.filename)
            continue

        file_bytes = await file.read()
        if len(file_bytes) == 0:
            logger.warning("Skipping empty file: %s", file.filename)
            continue
        if len(file_bytes) > 20 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{file.filename}' exceeds the 20MB limit."
            )

        candidate_id = str(uuid.uuid4())
        filepath = save_candidate_resume(candidate_id, file.filename, file_bytes)

        files_data.append({
            "filename": file.filename,
            "filepath": filepath,
            "candidate_id": candidate_id
        })

    if not files_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid resumes were found in the uploaded files. Supported: PDF.",
        )

    current_user.resumes_count += len(files_data)
    await db.commit()

    task = process_bulk_resumes_task.delay(current_user.id, files_data)

    return TaskResponse(task_id=task.id, status="Processing bulk upload")


@router.get("/candidates", response_model=list[CandidateDetail])
async def list_candidates(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_hr_role),
    db: AsyncSession = Depends(get_db),
):
    """List all candidates, optionally filtered by status asynchronously."""
    query = select(Candidate).where(Candidate.uploaded_by == current_user.id)
    if status_filter:
        query = query.where(Candidate.status == status_filter)
    query = query.order_by(Candidate.created_at.desc())

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    candidates = result.scalars().all()
    return [CandidateDetail.model_validate(c) for c in candidates]


@router.get("/candidates/{candidate_id}", response_model=CandidateDetail)
async def get_candidate(
    candidate_id: str,
    current_user: User = Depends(require_hr_role),
    db: AsyncSession = Depends(get_db),
):
    """Get full details for a single candidate asynchronously."""
    result = await db.execute(
        select(Candidate).where(Candidate.id == candidate_id, Candidate.uploaded_by == current_user.id)
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    return CandidateDetail.model_validate(candidate)


@router.get("/candidates/{candidate_id}/download")
async def download_candidate_resume(
    candidate_id: str,
    current_user: User = Depends(require_hr_role),
    db: AsyncSession = Depends(get_db),
):
    """Download the candidate's original resume PDF file asynchronously."""
    result = await db.execute(
        select(Candidate).where(Candidate.id == candidate_id, Candidate.uploaded_by == current_user.id)
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    if settings.STORAGE_PROVIDER == "s3":
        url = generate_candidate_resume_download_url(candidate.id, candidate.resume_filename)
        if not url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate secure S3 download link."
            )
        return RedirectResponse(url=url)

    safe_name = re_module.sub(r'[\\/*?:"<>|]', "_", candidate.resume_filename)
    filepath = os.path.join(settings.DATA_DIR, "candidates", candidate.id, safe_name)

    if not os.path.exists(filepath):
        # Fallback to general storage name search
        directory = os.path.join(settings.DATA_DIR, "candidates", candidate.id)
        if os.path.exists(directory):
            files = os.listdir(directory)
            if files:
                filepath = os.path.join(directory, files[0])

    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume file not found on disk."
        )

    return FileResponse(
        path=filepath,
        filename=candidate.resume_filename,
        media_type="application/pdf"
    )


@router.patch("/candidates/{candidate_id}/status", response_model=CandidateDetail)
async def update_candidate_status(
    candidate_id: str,
    body: StatusUpdate,
    current_user: User = Depends(require_hr_role),
    db: AsyncSession = Depends(get_db),
):
    """Update a candidate's pipeline status asynchronously."""
    result = await db.execute(
        select(Candidate).where(Candidate.id == candidate_id, Candidate.uploaded_by == current_user.id)
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    candidate.status = body.status
    candidate.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(candidate)

    logger.info("Candidate %s status updated to %s by %s", candidate_id, body.status, current_user.id)
    return CandidateDetail.model_validate(candidate)


@router.delete("/candidates/{candidate_id}")
async def delete_candidate(
    candidate_id: str,
    current_user: User = Depends(require_hr_role),
    db: AsyncSession = Depends(get_db),
):
    """Delete a candidate and their vector data asynchronously."""
    result = await db.execute(
        select(Candidate).where(Candidate.id == candidate_id, Candidate.uploaded_by == current_user.id)
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    # Remove from ChromaDB
    try:
        vector_service = VectorService.get_instance()
        vector_service.delete_resume(candidate_id)
    except Exception as e:
        logger.warning("Failed to delete vector data for candidate %s: %s", candidate_id, e)

    await db.delete(candidate)
    await db.commit()

    logger.info("Candidate %s deleted by %s", candidate_id, current_user.id)
    return {"message": "Candidate deleted successfully"}


# ══════════════════════════════════════════════════════════════════════
# Job Description Management
# ══════════════════════════════════════════════════════════════════════

@router.post("/job-descriptions", response_model=JobDescriptionResponse)
async def create_job_description(
    body: JobDescriptionCreate,
    current_user: User = Depends(require_hr_role),
    db: AsyncSession = Depends(get_db),
):
    # Enforce JD limit safeguard
    if current_user.jds_count >= current_user.max_jds:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Job description limit exceeded. You can create up to {current_user.max_jds} JDs (Current: {current_user.jds_count})."
        )

    jd = JobDescription(
        title=body.title,
        description=body.description,
        department=body.department,
        created_by=current_user.id,
    )
    db.add(jd)
    
    # Increment historical JDs count
    current_user.jds_count += 1
    
    await db.commit()
    await db.refresh(jd)
    return JobDescriptionResponse.model_validate(jd)


@router.get("/job-descriptions", response_model=list[JobDescriptionResponse])
async def list_job_descriptions(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(require_hr_role),
    db: AsyncSession = Depends(get_db),
):
    """List all Job Descriptions asynchronously."""
    query = select(JobDescription).where(JobDescription.created_by == current_user.id)
    if status_filter:
        query = query.where(JobDescription.status == status_filter)
    query = query.order_by(JobDescription.created_at.desc())
    result = await db.execute(query)
    jds = result.scalars().all()
    return [JobDescriptionResponse.model_validate(jd) for jd in jds]


@router.get("/job-descriptions/{jd_id}", response_model=JobDescriptionResponse)
async def get_job_description(
    jd_id: str,
    current_user: User = Depends(require_hr_role),
    db: AsyncSession = Depends(get_db),
):
    """Get a single Job Description asynchronously."""
    result = await db.execute(
        select(JobDescription).where(JobDescription.id == jd_id, JobDescription.created_by == current_user.id)
    )
    jd = result.scalar_one_or_none()
    if not jd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job Description not found")
    return JobDescriptionResponse.model_validate(jd)


@router.patch("/job-descriptions/{jd_id}", response_model=JobDescriptionResponse)
async def update_job_description(
    jd_id: str,
    body: JobDescriptionUpdate,
    current_user: User = Depends(require_hr_role),
    db: AsyncSession = Depends(get_db),
):
    """Update a Job Description asynchronously."""
    result = await db.execute(
        select(JobDescription).where(JobDescription.id == jd_id, JobDescription.created_by == current_user.id)
    )
    jd = result.scalar_one_or_none()
    if not jd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job Description not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(jd, key, value)
    jd.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(jd)
    return JobDescriptionResponse.model_validate(jd)


@router.delete("/job-descriptions/{jd_id}")
async def delete_job_description(
    jd_id: str,
    current_user: User = Depends(require_hr_role),
    db: AsyncSession = Depends(get_db),
):
    """Delete a Job Description and its screening results asynchronously."""
    result = await db.execute(
        select(JobDescription).where(JobDescription.id == jd_id, JobDescription.created_by == current_user.id)
    )
    jd = result.scalar_one_or_none()
    if not jd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job Description not found")

    await db.delete(jd)
    await db.commit()
    return {"message": "Job Description deleted successfully"}


# ══════════════════════════════════════════════════════════════════════
# AI Screening
# ══════════════════════════════════════════════════════════════════════

@router.post("/screen", response_model=TaskResponse)
async def screen_candidates(
    body: ScreenRequest,
    current_user: User = Depends(require_hr_role),
    db: AsyncSession = Depends(get_db),
):
    """Run AI screening: match candidates from the pool against a Job Description.
    Dispatches processing to a background Celery task.
    """
    if current_user.screenings_count >= current_user.max_screenings:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Screening limit exceeded. You can perform up to {current_user.max_screenings} screening runs (Current: {current_user.screenings_count})."
        )

    result = await db.execute(
        select(JobDescription).where(JobDescription.id == body.job_description_id, JobDescription.created_by == current_user.id)
    )
    jd = result.scalar_one_or_none()
    if not jd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job Description not found")

    current_user.screenings_count += 1
    await db.commit()

    task = run_ai_screening_task.delay(current_user.id, body.job_description_id, body.top_n)

    return TaskResponse(task_id=task.id, status="Processing screening")


@router.get("/screening-results/{jd_id}", response_model=list[ScreeningResultResponse])
async def get_screening_results(
    jd_id: str,
    current_user: User = Depends(require_hr_role),
    db: AsyncSession = Depends(get_db),
):
    """Get saved screening results for a Job Description asynchronously."""
    result = await db.execute(
        select(JobDescription).where(JobDescription.id == jd_id, JobDescription.created_by == current_user.id)
    )
    jd = result.scalar_one_or_none()
    if not jd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job Description not found")

    sr_result = await db.execute(
        select(ScreeningResult)
        .options(selectinload(ScreeningResult.candidate))
        .where(ScreeningResult.job_description_id == jd_id)
        .order_by(ScreeningResult.match_score.desc())
    )
    results = sr_result.scalars().all()

    response = []
    for r in results:
        if r.candidate and r.candidate.uploaded_by == current_user.id:
            response.append(ScreeningResultResponse(
                id=r.id,
                candidate=CandidateDetail.model_validate(r.candidate),
                match_score=r.match_score,
                match_justification=r.match_justification,
                vetting_questions=r.vetting_questions,
                created_at=r.created_at,
            ))

    return response


# ══════════════════════════════════════════════════════════════════════
# Vetting Q&A
# ══════════════════════════════════════════════════════════════════════

@router.post("/vetting-questions", response_model=list[VettingQuestionResponse])
async def generate_vetting_questions(
    body: VettingRequest,
    current_user: User = Depends(require_hr_role),
    db: AsyncSession = Depends(get_db),
):
    """Generate AI-powered vetting Q&As for a candidate-JD pair asynchronously.

    Questions are designed to verify the candidate's claimed skills
    and detect potential misrepresentation. Results are saved to the
    screening_result record.
    """
    cand_result = await db.execute(
        select(Candidate).where(Candidate.id == body.candidate_id, Candidate.uploaded_by == current_user.id)
    )
    candidate = cand_result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    jd_result = await db.execute(
        select(JobDescription).where(JobDescription.id == body.job_description_id, JobDescription.created_by == current_user.id)
    )
    jd = jd_result.scalar_one_or_none()
    if not jd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job Description not found")

    # Generate vetting questions non-blockingly
    screening_service = ScreeningService()
    try:
        questions = await asyncio.to_thread(
            screening_service.generate_vetting_questions,
            candidate.resume_text,
            jd.description
        )
    except Exception as e:
        logger.error("Vetting Q&A generation failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate vetting questions: {str(e)}",
        )

    # Save to screening result if one exists
    sr_result = await db.execute(
        select(ScreeningResult).where(
            ScreeningResult.job_description_id == body.job_description_id,
            ScreeningResult.candidate_id == body.candidate_id,
        )
    )
    screening_result = sr_result.scalar_one_or_none()
    if screening_result:
        screening_result.vetting_questions = questions
        await db.commit()

    return [VettingQuestionResponse(**q) for q in questions]
