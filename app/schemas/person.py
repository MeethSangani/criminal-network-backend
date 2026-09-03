from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class PersonBase(BaseModel):
    first_name: str
    last_name: str
    full_name: str
    alias: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[str] = None
    nationality: Optional[str] = None
    occupation: Optional[str] = None
    risk_level: Optional[str] = "LOW"
    status: Optional[str] = "ACTIVE"
    notes: Optional[str] = None

class PersonCreate(PersonBase):
    id: str

class PersonResponse(PersonBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class PersonListResponse(BaseModel):
    success: bool = True
    total: int
    skip: int
    limit: int
    data: List[PersonResponse]
