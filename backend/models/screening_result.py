import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.database import Base


class ScreeningResult(Base):
    __tablename__ = "screening_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_description_id = Column(
        String, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_id = Column(
        String, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    match_score = Column(Float, nullable=False, default=0.0)  # 0.0 – 100.0
    match_justification = Column(Text, nullable=True)
    vetting_questions = Column(JSON, nullable=True)  # List of {question, expected_answer, skill_area, difficulty}
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    job_description = relationship("JobDescription", back_populates="screening_results")
    candidate = relationship("Candidate", back_populates="screening_results")

    def __repr__(self):
        return f"<ScreeningResult JD={self.job_description_id} Candidate={self.candidate_id} Score={self.match_score}>"
