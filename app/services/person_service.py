from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.person import Person
from app.schemas.person import PersonCreate

class PersonService:
    def __init__(self, db: Session):
        self.db = db

    def get_person_by_id(self, person_id: str) -> Optional[Person]:
        stmt = select(Person).where(Person.id == person_id)
        return self.db.scalar(stmt)

    def list_persons(self, skip: int = 0, limit: int = 50) -> Tuple[List[Person], int]:
        total_stmt = select(func.count()).select_from(Person)
        total = self.db.scalar(total_stmt) or 0

        stmt = select(Person).offset(skip).limit(limit)
        persons = list(self.db.scalars(stmt).all())
        return persons, total

    def create_person(self, person_in: PersonCreate) -> Person:
        db_person = Person(**person_in.model_dump())
        self.db.add(db_person)
        self.db.commit()
        self.db.refresh(db_person)
        return db_person
