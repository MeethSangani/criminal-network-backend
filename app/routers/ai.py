from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

class AIQueryRequest(BaseModel):
    question: str

@router.post("/query")
def query_ai_assistant(body: AIQueryRequest, db: Session = Depends(get_db)):
    if not body.question or not body.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_QUERY", "message": "Question parameter cannot be empty."}
        )
    service = AIService(db)
    response_data = service.process_query(body.question)
    return {
        "success": True,
        "data": response_data
    }
