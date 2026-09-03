from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from app.models.case import Case
from app.models.person import Person
from app.models.relationship import Relationship
from app.schemas.case import CaseCreate

class CaseService:
    def __init__(self, db: Session):
        self.db = db

    def get_case_by_id(self, case_id: str) -> Optional[Case]:
        stmt = select(Case).where(Case.id == case_id)
        return self.db.scalar(stmt)

    def list_cases(self, skip: int = 0, limit: int = 50) -> Tuple[List[Case], int]:
        total_stmt = select(func.count()).select_from(Case)
        total = self.db.scalar(total_stmt) or 0
        stmt = select(Case).offset(skip).limit(limit)
        cases = list(self.db.scalars(stmt).all())
        return cases, total

    def create_case(self, case_in: CaseCreate) -> Case:
        db_case = Case(**case_in.model_dump())
        self.db.add(db_case)
        self.db.commit()
        self.db.refresh(db_case)
        return db_case

    def get_case_persons(self, case_id: str) -> List[Person]:
        # Find relationships where source or target is case_id and type is ASSOCIATED_WITH_CASE or LINKED
        rel_stmt = select(Relationship).where(
            or_(
                (Relationship.source_id == case_id),
                (Relationship.target_id == case_id)
            )
        )
        relationships = self.db.scalars(rel_stmt).all()
        person_ids = []
        for r in relationships:
            if r.source_id != case_id and r.source_type == "PERSON":
                person_ids.append(r.source_id)
            elif r.target_id != case_id and r.target_type == "PERSON":
                person_ids.append(r.target_id)
        
        if not person_ids:
            return []

        persons_stmt = select(Person).where(Person.id.in_(person_ids))
        return list(self.db.scalars(persons_stmt).all())
