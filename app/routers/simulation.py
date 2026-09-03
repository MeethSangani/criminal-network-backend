from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.simulation_service import SimulationService

router = APIRouter(prefix="/simulation", tags=["Simulation"])

class NodeRemovalRequest(BaseModel):
    entity_id: str

@router.post("/remove-node")
def simulate_node_removal(body: NodeRemovalRequest, db: Session = Depends(get_db)):
    if not body.entity_id or not body.entity_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_ENTITY_ID", "message": "entity_id parameter cannot be empty."}
        )
    service = SimulationService(db)
    result = service.simulate_node_removal(body.entity_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ENTITY_NOT_FOUND", "message": f"Entity {body.entity_id} was not found in the graph network."}
        )
    return {
        "success": True,
        "data": result
    }
