from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Surveillance(Base):
    __tablename__ = "surveillances"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    location_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    person_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
