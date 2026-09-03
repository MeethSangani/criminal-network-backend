from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.search_service import SearchService
from app.schemas.search import SearchResponse, SearchData

router = APIRouter(tags=["Search"])

@router.get("/search", response_model=SearchResponse)
def global_search(
    q: str = Query(..., min_length=1, description="Search query string"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    db: Session = Depends(get_db)
):
    service = SearchService(db)
    results = service.search_all(query=q, limit=limit)
    return {
        "success": True,
        "data": {
            "results": results
        }
    }
