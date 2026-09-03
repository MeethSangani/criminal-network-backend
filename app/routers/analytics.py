from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.analytics_service import AnalyticsService

router = APIRouter(tags=["Analytics"])

@router.get("/persons/{person_id}/analytics")
def get_person_analytics(person_id: str, db: Session = Depends(get_db)):
    service = AnalyticsService(db)
    res = service.get_person_analytics(person_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PERSON_NOT_FOUND", "message": f"Person {person_id} was not found"}
        )
    return {"success": True, "data": res}

@router.get("/persons/{person_id}/priority")
def get_person_priority(person_id: str, db: Session = Depends(get_db)):
    service = AnalyticsService(db)
    res = service.get_investigation_priority(person_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PERSON_NOT_FOUND", "message": f"Person {person_id} was not found"}
        )
    return {"success": True, "data": res}
