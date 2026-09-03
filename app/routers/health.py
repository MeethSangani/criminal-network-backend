from fastapi import APIRouter
from app.database import check_database_connection

router = APIRouter(tags=["Health"])

@router.get("/health")
def get_health():
    is_db_connected = check_database_connection()
    db_status = "connected" if is_db_connected else "disconnected"
    return {
        "success": True,
        "data": {
            "api": "ok",
            "database": db_status
        }
    }
