from pydantic import BaseModel
from typing import Optional, List


class JobSearchRequest(BaseModel):
    """Request body for searching jobs."""
    keyword: str
    location: str = "remote"
    results_per_page: int = 5


class JobResult(BaseModel):
    """A single job result with hiring score."""
    position_title: str
    organization_name: str
    location: str
    job_summary: str
    url: str
    hiring_score: Optional[int] = None
    hiring_score_reasoning: Optional[str] = None
    raw_data: Optional[dict] = None


class JobSearchResponse(BaseModel):
    """Response from job search endpoint."""
    jobs: List[JobResult]
    total: int


class JobAnalysisRequest(BaseModel):
    """Request body for analyzing a specific job."""
    job_data: dict
    user_bio: str = "I'm a professional looking for new opportunities."


class JobAnalysisResponse(BaseModel):
    """Response from job analysis (resume tweak + cover letter)."""
    jd_summary: str
    resume_tweaks: str
    cover_letter: str
    hiring_score: int
    hiring_score_reasoning: str
