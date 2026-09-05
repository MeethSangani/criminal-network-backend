import enum
from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Enum
from app.database import Base

class UserRole(str, enum.Enum):
    CITIZEN = "CITIZEN"
    INVESTIGATOR = "INVESTIGATOR"
    ADMIN = "ADMIN"

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CITIZEN, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.value if isinstance(self.role, UserRole) else str(self.role),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
