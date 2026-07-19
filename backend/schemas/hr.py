"""Pydantic schemas for the HR Dashboard API."""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


# ── Candidate Schemas ───────────────────────────────────────────────

class CandidateDetail(BaseModel):
    """Full candidate information."""
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    resume_filename: str
    resume_text: Optional[str] = None
    status: str
    uploaded_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CandidateUploadResponse(BaseModel):
    """Response after uploading a candidate resume."""
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    filename: str
    status: str


class StatusUpdate(BaseModel):
    """Request to update a candidate's status."""
    status: Literal["new", "screening", "shortlisted", "interview", "hired", "closed"]


# ── Job Description Schemas ─────────────────────────────────────────

class JobDescriptionCreate(BaseModel):
    """Request to create a new Job Description."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    department: Optional[str] = None


class JobDescriptionUpdate(BaseModel):
    """Request to update a Job Description."""
    title: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    status: Optional[Literal["open", "closed"]] = None


class JobDescriptionResponse(BaseModel):
    """Full Job Description info."""
    id: str
    title: str
    description: str
    department: Optional[str] = None
    created_by: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Screening Schemas ───────────────────────────────────────────────

class ScreenRequest(BaseModel):
    """Request to screen candidates against a JD."""
    job_description_id: str
    top_n: int = Field(default=10, ge=1, le=50)


class ScreeningResultResponse(BaseModel):
    """A single screening result for a candidate-JD pair."""
    id: str
    candidate: CandidateDetail
    match_score: float
    match_justification: Optional[str] = None
    vetting_questions: Optional[list] = None
    created_at: Optional[datetime] = None


# ── Vetting Schemas ─────────────────────────────────────────────────

class VettingRequest(BaseModel):
    """Request to generate vetting questions."""
    candidate_id: str
    job_description_id: str


class VettingQuestionResponse(BaseModel):
    """A single vetting question."""
    question: str
    expected_answer: str
    skill_area: str
    difficulty: str


# ── Dashboard Schemas ───────────────────────────────────────────────

class DashboardStats(BaseModel):
    """Stats for the HR dashboard header."""
    total_candidates: int
    open_positions: int
    shortlisted: int
    hired: int
