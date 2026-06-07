import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    google_id = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    picture_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<User {self.email}>"
