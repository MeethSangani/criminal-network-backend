from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.network_service import NetworkService
from app.schemas.network import NetworkResponse, PathFindingResponse

router = APIRouter(tags=["Network"])

@router.get("/persons/{person_id}/network", response_model=NetworkResponse)
def get_person_network(
    person_id: str,
    depth: int = Query(2, ge=1, le=5, description="Network depth (hops)"),
    relationship_type: Optional[str] = Query(None, description="Filter by relationship type"),
    db: Session = Depends(get_db)
):
    service = NetworkService(db)
    graph_data = service.get_person_network(
        person_id=person_id,
        depth=depth,
        relationship_type=relationship_type
    )
    return {
        "success": True,
        "data": graph_data
    }

@router.get("/network/path", response_model=PathFindingResponse)
def get_network_path(
    source: str = Query(..., description="Source entity ID"),
    target: str = Query(..., description="Target entity ID"),
    db: Session = Depends(get_db)
):
    service = NetworkService(db)
    path_data = service.find_shortest_path(source_id=source, target_id=target)
    if not path_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PATH_NOT_FOUND",
                "message": f"No valid path found between {source} and {target}"
            }
        )
    return {
        "success": True,
        "data": path_data
    }
