from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.case_service import CaseService
from app.services.ingestion_service import IngestionService
from app.schemas.case import CaseResponse, CaseListResponse
from app.schemas.person import PersonResponse
from app.deps import get_current_investigator_or_admin
from app.models.user import User

router = APIRouter(prefix="/cases", tags=["Cases"])

class CaseCreateRequest(BaseModel):
    title: str
    description: str
    type: Optional[str] = "GENERAL"

@router.get("", response_model=CaseListResponse)
def get_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    service = CaseService(db)
    cases, total = service.list_cases(skip=skip, limit=limit)
    return {
        "success": True,
        "total": total,
        "data": [CaseResponse.model_validate(c) for c in cases]
    }

@router.post("", status_code=status.HTTP_201_CREATED)
def create_case_ingestion(
    payload: CaseCreateRequest,
    current_user: User = Depends(get_current_investigator_or_admin),
    db: Session = Depends(get_db)
):
    """Create a new case file and incrementally extract, resolve, and link entities."""
    ingestion = IngestionService(db)
    result = ingestion.ingest_case_and_entities(
        title=payload.title,
        description=payload.description,
        case_type=payload.type,
        created_by_id=current_user.id,
        created_by_username=current_user.username
    )
    return result

@router.get("/{case_id}")
def get_case(case_id: str, db: Session = Depends(get_db)):
    service = CaseService(db)
    case_obj = service.get_case_by_id(case_id)
    if not case_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "CASE_NOT_FOUND",
                "message": f"Case {case_id} was not found"
            }
        )
    return {
        "success": True,
        "data": CaseResponse.model_validate(case_obj)
    }

@router.get("/{case_id}/persons")
def get_case_persons(case_id: str, db: Session = Depends(get_db)):
    service = CaseService(db)
    case_obj = service.get_case_by_id(case_id)
    if not case_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "CASE_NOT_FOUND",
                "message": f"Case {case_id} was not found"
            }
        )
    persons = service.get_case_persons(case_id)
    return {
        "success": True,
        "data": [PersonResponse.model_validate(p) for p in persons]
    }
