import enum
from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey
from app.database import Base

class ReportStatus(str, enum.Enum):
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"

class CitizenReport(Base):
    __tablename__ = "citizen_reports"

    id = Column(String, primary_key=True, default=lambda: f"REP-{uuid.uuid4().hex[:8].upper()}")
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String, nullable=True)
    event_date = Column(String, nullable=True)
    person_details = Column(Text, nullable=True)  # Store JSON formatted details or raw text
    vehicle_details = Column(Text, nullable=True) # Store JSON formatted details or raw text
    attachment_metadata = Column(Text, nullable=True)
    status = Column(Enum(ReportStatus), default=ReportStatus.PENDING, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "event_date": self.event_date,
            "person_details": self.person_details,
            "vehicle_details": self.vehicle_details,
            "attachment_metadata": self.attachment_metadata,
            "status": self.status.value if isinstance(self.status, ReportStatus) else str(self.status),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
