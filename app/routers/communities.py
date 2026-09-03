from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.community_service import CommunityService

router = APIRouter(prefix="/communities", tags=["Communities"])

@router.get("")
def get_communities(db: Session = Depends(get_db)):
    service = CommunityService(db)
    communities = service.get_all_communities()
    return {"success": True, "data": communities}

@router.get("/{community_id}")
def get_community_detail(community_id: str, db: Session = Depends(get_db)):
    service = CommunityService(db)
    comm = service.get_community_by_id(community_id)
    if not comm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COMMUNITY_NOT_FOUND", "message": f"Community {community_id} was not found"}
        )
    return {"success": True, "data": comm}

@router.get("/{community_id}/network")
def get_community_network(community_id: str, db: Session = Depends(get_db)):
    service = CommunityService(db)
    net = service.get_community_network(community_id)
    if not net:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COMMUNITY_NOT_FOUND", "message": f"Community {community_id} was not found"}
        )
    return {"success": True, "data": net}
