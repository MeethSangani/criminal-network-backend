from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, DateTime, Column
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Person(Base):
    __tablename__ = "persons"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    alias: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    dob: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    nationality: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    occupation: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    risk_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="LOW")
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="ACTIVE")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
