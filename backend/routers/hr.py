"""
HR Dashboard Router — all endpoints for the HR/Hiring Manager Dashboard.

Handles candidate management, job descriptions, AI screening, and vetting Q&A generation.
All endpoints require authenticated user with HR role.
"""
import logging
import uuid
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

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
)
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
    """Process a single resume text into a Candidate record.

    Shared logic between PDF and spreadsheet flows.
    """
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
def get_dashboard_stats(
    current_user: User = Depends(require_hr_role),
    db: Session = Depends(get_db),
):
    """Get aggregate stats for the HR dashboard header."""
    total_candidates = current_user.resumes_count
    open_positions = current_user.jds_count
    shortlisted = db.query(Candidate).filter(
        Candidate.uploaded_by == current_user.id,
        Candidate.status == "shortlisted"
    ).count()
    hired = db.query(Candidate).filter(
        Candidate.uploaded_by == current_user.id,
        Candidate.status == "hired"
    ).count()

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

@router.post("/candidates/upload", response_model=list[CandidateUploadResponse])
async def upload_candidates(
    files: list[UploadFile] = File(...),
    current_user: User = Depends(require_hr_role),
    db: Session = Depends(get_db),
):
    """Upload candidate resumes as PDFs.

    **PDF**: Each file is parsed via PyMuPDF to extract text.
    """
    # Enforce upload limit safeguard
    if current_user.resumes_count + len(files) > current_user.max_resumes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Upload limit exceeded. You can upload up to {current_user.max_resumes} resumes (Current: {current_user.resumes_count})."
        )

    results = []
    vector_service = VectorService.get_instance()
    screening_service = ScreeningService(vector_service)

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

        # ── PDF Upload ───────────────────────────────────────
        try:
            resume_text = extract_text_from_pdf(file_bytes)
        except Exception as e:
            logger.error("Failed to extract text from %s: %s", file.filename, e)
            continue

        candidate_id = str(uuid.uuid4())
        save_candidate_resume(candidate_id, file.filename, file_bytes)

        result = _process_single_resume(
            resume_text=resume_text,
            source_label=file.filename,
            category=None,
            screening_service=screening_service,
            vector_service=vector_service,
            current_user=current_user,
            db=db,
            candidate_id=candidate_id,
        )
        if result:
            results.append(result)

    if not results:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid resumes were found in the uploaded files. Supported: PDF.",
        )

    # Increment historical uploads count
    current_user.resumes_count += len(results)
    db.commit()

    return results


@router.get("/candidates", response_model=list[CandidateDetail])
def list_candidates(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_hr_role),
    db: Session = Depends(get_db),
):
    """List all candidates, optionally filtered by status."""
    query = db.query(Candidate).filter(Candidate.uploaded_by == current_user.id)
    if status_filter:
        query = query.filter(Candidate.status == status_filter)
    query = query.order_by(Candidate.created_at.desc())

    offset = (page - 1) * page_size
    candidates = query.offset(offset).limit(page_size).all()
    return [CandidateDetail.model_validate(c) for c in candidates]


@router.get("/candidates/{candidate_id}", response_model=CandidateDetail)
def get_candidate(
    candidate_id: str,
    current_user: User = Depends(require_hr_role),
    db: Session = Depends(get_db),
):
    """Get full details for a single candidate."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id, Candidate.uploaded_by == current_user.id).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    return CandidateDetail.model_validate(candidate)


@router.get("/candidates/{candidate_id}/download")
def download_candidate_resume(
    candidate_id: str,
    current_user: User = Depends(require_hr_role),
    db: Session = Depends(get_db),
):
    """Download the candidate's original resume PDF file."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id, Candidate.uploaded_by == current_user.id).first()
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
def update_candidate_status(
    candidate_id: str,
    body: StatusUpdate,
    current_user: User = Depends(require_hr_role),
    db: Session = Depends(get_db),
):
    """Update a candidate's pipeline status."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id, Candidate.uploaded_by == current_user.id).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    candidate.status = body.status
    candidate.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(candidate)

    logger.info("Candidate %s status updated to %s by %s", candidate_id, body.status, current_user.id)
    return CandidateDetail.model_validate(candidate)


@router.delete("/candidates/{candidate_id}")
def delete_candidate(
    candidate_id: str,
    current_user: User = Depends(require_hr_role),
    db: Session = Depends(get_db),
):
    """Delete a candidate and their vector data."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id, Candidate.uploaded_by == current_user.id).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    # Remove from ChromaDB
    try:
        vector_service = VectorService.get_instance()
        vector_service.delete_resume(candidate_id)
    except Exception as e:
        logger.warning("Failed to delete vector data for candidate %s: %s", candidate_id, e)

    db.delete(candidate)
    db.commit()

    logger.info("Candidate %s deleted by %s", candidate_id, current_user.id)
    return {"message": "Candidate deleted successfully"}


# ══════════════════════════════════════════════════════════════════════
# Job Description Management
# ══════════════════════════════════════════════════════════════════════

@router.post("/job-descriptions", response_model=JobDescriptionResponse)
def create_job_description(
    body: JobDescriptionCreate,
    current_user: User = Depends(require_hr_role),
    db: Session = Depends(get_db),
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
    
    db.commit()
    db.refresh(jd)
    return JobDescriptionResponse.model_validate(jd)


@router.get("/job-descriptions", response_model=list[JobDescriptionResponse])
def list_job_descriptions(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(require_hr_role),
    db: Session = Depends(get_db),
):
    """List all Job Descriptions."""
    query = db.query(JobDescription).filter(JobDescription.created_by == current_user.id)
    if status_filter:
        query = query.filter(JobDescription.status == status_filter)
    jds = query.order_by(JobDescription.created_at.desc()).all()
    return [JobDescriptionResponse.model_validate(jd) for jd in jds]


@router.get("/job-descriptions/{jd_id}", response_model=JobDescriptionResponse)
def get_job_description(
    jd_id: str,
    current_user: User = Depends(require_hr_role),
    db: Session = Depends(get_db),
):
    """Get a single Job Description."""
    jd = db.query(JobDescription).filter(JobDescription.id == jd_id, JobDescription.created_by == current_user.id).first()
    if not jd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job Description not found")
    return JobDescriptionResponse.model_validate(jd)


@router.patch("/job-descriptions/{jd_id}", response_model=JobDescriptionResponse)
def update_job_description(
    jd_id: str,
    body: JobDescriptionUpdate,
    current_user: User = Depends(require_hr_role),
    db: Session = Depends(get_db),
):
    """Update a Job Description."""
    jd = db.query(JobDescription).filter(JobDescription.id == jd_id, JobDescription.created_by == current_user.id).first()
    if not jd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job Description not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(jd, key, value)
    jd.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(jd)
    return JobDescriptionResponse.model_validate(jd)


@router.delete("/job-descriptions/{jd_id}")
def delete_job_description(
    jd_id: str,
    current_user: User = Depends(require_hr_role),
    db: Session = Depends(get_db),
):
    """Delete a Job Description and its screening results."""
    jd = db.query(JobDescription).filter(JobDescription.id == jd_id, JobDescription.created_by == current_user.id).first()
    if not jd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job Description not found")

    db.delete(jd)
    db.commit()
    return {"message": "Job Description deleted successfully"}


# ══════════════════════════════════════════════════════════════════════
# AI Screening
# ══════════════════════════════════════════════════════════════════════

@router.post("/screen", response_model=list[ScreeningResultResponse])
def screen_candidates(
    body: ScreenRequest,
    current_user: User = Depends(require_hr_role),
    db: Session = Depends(get_db),
):
    """Run AI screening: match candidates from the pool against a Job Description.

    Uses RAG to retrieve semantically similar resumes, then LLM to score each match.
    Results are persisted in the screening_results table.
    """
    # Enforce screening limit safeguard
    if current_user.screenings_count >= current_user.max_screenings:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Screening limit exceeded. You can perform up to {current_user.max_screenings} screening runs (Current: {current_user.screenings_count})."
        )

    # Get the JD
    jd = db.query(JobDescription).filter(JobDescription.id == body.job_description_id, JobDescription.created_by == current_user.id).first()
    if not jd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job Description not found")

    # Run screening pipeline
    vector_service = VectorService.get_instance()
    screening_service = ScreeningService(vector_service)

    # Build a map of candidate_id → full resume text for accurate scoring
    all_candidates = db.query(Candidate).filter(Candidate.uploaded_by == current_user.id).all()
    candidate_resumes = {c.id: c.resume_text for c in all_candidates}

    try:
        raw_results = screening_service.screen_candidates(
            jd_text=jd.description,
            top_n=body.top_n,
            candidate_resumes=candidate_resumes,
        )
    except Exception as e:
        logger.error("Screening pipeline failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Screening failed: {str(e)}",
        )

    # Delete previous results for this JD to avoid duplicates
    db.query(ScreeningResult).filter(ScreeningResult.job_description_id == jd.id).delete()

    # Persist results
    response_results = []
    for raw in raw_results:
        candidate = db.query(Candidate).filter(Candidate.id == raw["candidate_id"], Candidate.uploaded_by == current_user.id).first()
        if not candidate:
            continue

        screening_result = ScreeningResult(
            job_description_id=jd.id,
            candidate_id=candidate.id,
            match_score=raw["match_score"],
            match_justification=raw["match_justification"],
        )
        db.add(screening_result)
        db.flush()  # Get the ID

        response_results.append(ScreeningResultResponse(
            id=screening_result.id,
            candidate=CandidateDetail.model_validate(candidate),
            match_score=screening_result.match_score,
            match_justification=screening_result.match_justification,
            vetting_questions=screening_result.vetting_questions,
            created_at=screening_result.created_at,
        ))

    # Increment screening run count
    current_user.screenings_count += 1
    db.commit()
    logger.info("Screening complete: %d results for JD %s", len(response_results), jd.id)
    return response_results


@router.get("/screening-results/{jd_id}", response_model=list[ScreeningResultResponse])
def get_screening_results(
    jd_id: str,
    current_user: User = Depends(require_hr_role),
    db: Session = Depends(get_db),
):
    """Get saved screening results for a Job Description."""
    jd = db.query(JobDescription).filter(JobDescription.id == jd_id, JobDescription.created_by == current_user.id).first()
    if not jd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job Description not found")

    results = (
        db.query(ScreeningResult)
        .filter(ScreeningResult.job_description_id == jd_id)
        .order_by(ScreeningResult.match_score.desc())
        .all()
    )

    response = []
    for r in results:
        candidate = db.query(Candidate).filter(Candidate.id == r.candidate_id, Candidate.uploaded_by == current_user.id).first()
        if candidate:
            response.append(ScreeningResultResponse(
                id=r.id,
                candidate=CandidateDetail.model_validate(candidate),
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
def generate_vetting_questions(
    body: VettingRequest,
    current_user: User = Depends(require_hr_role),
    db: Session = Depends(get_db),
):
    """Generate AI-powered vetting Q&As for a candidate-JD pair.

    Questions are designed to verify the candidate's claimed skills
    and detect potential misrepresentation. Results are saved to the
    screening_result record.
    """
    candidate = db.query(Candidate).filter(Candidate.id == body.candidate_id, Candidate.uploaded_by == current_user.id).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    jd = db.query(JobDescription).filter(JobDescription.id == body.job_description_id, JobDescription.created_by == current_user.id).first()
    if not jd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job Description not found")

    # Generate vetting questions
    screening_service = ScreeningService()
    try:
        questions = screening_service.generate_vetting_questions(candidate.resume_text, jd.description)
    except Exception as e:
        logger.error("Vetting Q&A generation failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate vetting questions: {str(e)}",
        )

    # Save to screening result if one exists
    screening_result = (
        db.query(ScreeningResult)
        .filter(
            ScreeningResult.job_description_id == body.job_description_id,
            ScreeningResult.candidate_id == body.candidate_id,
        )
        .first()
    )
    if screening_result:
        screening_result.vetting_questions = questions
        db.commit()

    return [VettingQuestionResponse(**q) for q in questions]
