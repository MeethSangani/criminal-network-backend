from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.nlp.ner import extract_entities_from_text

router = APIRouter(prefix="/nlp", tags=["NLP"])

class NLPExtractRequest(BaseModel):
    text: str
    report_id: Optional[str] = "REP-001"

@router.get("/extract")
@router.post("/extract")
def extract_nlp_entities(body: NLPExtractRequest):
    entities = extract_entities_from_text(body.text, report_id=body.report_id or "REP-001")
    return {
        "success": True,
        "data": {
            "text": body.text,
            "report_id": body.report_id,
            "entities": entities
        }
    }
