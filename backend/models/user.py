import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Integer
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    google_id = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    picture_url = Column(String, nullable=True)
    skills = Column(String, nullable=True)
    role = Column(String, default="job_seeker", nullable=False)  # "job_seeker" or "hr"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # UAT / Safeguard Limits (flexible and configurable via DB)
    max_resumes = Column(Integer, default=50, nullable=False)
    resumes_count = Column(Integer, default=0, nullable=False)
    max_jds = Column(Integer, default=10, nullable=False)
    jds_count = Column(Integer, default=0, nullable=False)
    max_screenings = Column(Integer, default=50, nullable=False)
    screenings_count = Column(Integer, default=25, nullable=False)
    max_conversations = Column(Integer, default=10, nullable=False)
    conversations_count = Column(Integer, default=0, nullable=False)
    max_messages_per_conversation = Column(Integer, default=50, nullable=False)

    def __repr__(self):
        return f"<User {self.email}>"
