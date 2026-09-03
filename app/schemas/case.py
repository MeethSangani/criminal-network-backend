from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class CaseBase(BaseModel):
    case_number: str
    title: str
    type: Optional[str] = None
    status: Optional[str] = "OPEN"
    priority: Optional[str] = "MEDIUM"
    description: Optional[str] = None
    lead_investigator: Optional[str] = None

class CaseCreate(CaseBase):
    id: str

class CaseResponse(CaseBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class CaseListResponse(BaseModel):
    success: bool = True
    total: int
    data: List[CaseResponse]
