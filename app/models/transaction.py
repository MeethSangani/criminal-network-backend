from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    sender_account: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    receiver_account: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    sender_person_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    receiver_person_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    transaction_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="WIRE")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
