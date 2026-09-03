from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.anomaly_service import AnomalyService

router = APIRouter(tags=["Anomalies"])

@router.get("/anomalies")
def get_anomalies(db: Session = Depends(get_db)):
    service = AnomalyService(db)
    anomalies = service.get_all_anomalies()
    return {"success": True, "data": anomalies}

@router.get("/persons/{person_id}/anomalies")
def get_person_anomalies(person_id: str, db: Session = Depends(get_db)):
    service = AnomalyService(db)
    anomalies = service.get_anomalies_for_person(person_id)
    return {"success": True, "data": anomalies}
