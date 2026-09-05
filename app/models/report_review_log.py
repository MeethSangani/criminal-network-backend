from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from app.database import Base

class ReportReviewLog(Base):
    __tablename__ = "report_review_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String, ForeignKey("citizen_reports.id"), nullable=False, index=True)
    reviewed_by_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    old_status = Column(String, nullable=False)
    new_status = Column(String, nullable=False)
    action = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "report_id": self.report_id,
            "reviewed_by_id": self.reviewed_by_id,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "action": self.action,
            "notes": self.notes,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
