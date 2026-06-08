import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    resume_filename = Column(String, nullable=False)
    resume_text = Column(Text, nullable=False)
    chroma_doc_id = Column(String, nullable=True)  # Reference to ChromaDB document
    uploaded_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String, default="new", nullable=False, index=True)
    # Possible statuses: "new", "screening", "shortlisted", "interview", "hired", "closed"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    uploader = relationship("User", backref="uploaded_candidates")
    screening_results = relationship("ScreeningResult", back_populates="candidate", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Candidate {self.name} ({self.status})>"
