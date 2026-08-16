from pydantic import BaseModel
from typing import Optional, List, Union


class JobSearchRequest(BaseModel):
    """Request body for searching jobs."""
    keyword: Union[str, List[str]]
    location: str = "remote"
    company_preference: Optional[Union[str, List[str]]] = None
    results_per_page: int = 5

    @property
    def keyword_list(self) -> List[str]:
        if isinstance(self.keyword, list):
            return [k.strip() for k in self.keyword if k and k.strip()]
        if isinstance(self.keyword, str):
            return [k.strip() for k in self.keyword.split(",") if k and k.strip()]
        return []

    @property
    def company_preference_list(self) -> List[str]:
        if not self.company_preference:
            return []
        if isinstance(self.company_preference, list):
            return [c.strip() for c in self.company_preference if c and c.strip()]
        if isinstance(self.company_preference, str):
            return [c.strip() for c in self.company_preference.split(",") if c and c.strip()]
        return []


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
    search_time_seconds: Optional[float] = None


class JobAnalysisRequest(BaseModel):
    """Request body for analyzing a specific job."""
    job_data: dict
    user_bio: str = "I'm a professional looking for new opportunities."


class JobAnalysisResponse(BaseModel):
    """Response from job analysis (resume tweak + cover letter)."""
    jd_summary: str
    resume_tweaks: str
    cover_letter: str
    company_profile: str
    interview_prep: str
    hiring_score: int
    hiring_score_reasoning: str
