from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.entity_resolution.matching import resolve_person_entity

class EntityResolutionService:
    def __init__(self, db: Session):
        self.db = db

    def get_entity_resolution(self, entity_id: str) -> Optional[Dict[str, Any]]:
        result = resolve_person_entity(self.db, entity_id)
        if not result:
            return None
        return result
