from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.case_service import CaseService
from app.schemas.case import CaseResponse, CaseListResponse
from app.schemas.person import PersonResponse

router = APIRouter(prefix="/cases", tags=["Cases"])

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
