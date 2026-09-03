from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class CDR(Base):
    __tablename__ = "cdrs"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    caller_phone: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    receiver_phone: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    caller_person_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    receiver_person_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
