from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.evidence_service import EvidenceService

router = APIRouter(prefix="/evidence", tags=["Evidence"])

@router.get("/{evidence_id}")
def get_evidence_record(evidence_id: str, db: Session = Depends(get_db)):
    service = EvidenceService(db)
    ev = service.get_evidence(evidence_id)
    if not ev:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "EVIDENCE_NOT_FOUND", "message": f"Evidence {evidence_id} was not found"}
        )
    return {"success": True, "data": ev}
