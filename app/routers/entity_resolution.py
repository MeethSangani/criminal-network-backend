from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.entity_resolution_service import EntityResolutionService

router = APIRouter(prefix="/entity-resolution", tags=["Entity Resolution"])

@router.get("/{entity_id}")
def get_entity_resolution(entity_id: str, db: Session = Depends(get_db)):
    service = EntityResolutionService(db)
    result = service.get_entity_resolution(entity_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ENTITY_NOT_FOUND", "message": f"Entity {entity_id} was not found"}
        )
    return {"success": True, "data": result}
