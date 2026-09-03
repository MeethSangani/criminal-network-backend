from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from app.models.person import Person

def resolve_person_entity(db: Session, person_id: str) -> Dict[str, Any]:
    person = db.scalar(select(Person).where(Person.id == person_id))
    if not person:
        return {}

    # Find candidate alias matches based on same last name or partial first name
    candidates_stmt = select(Person).where(
        (Person.id != person_id) &
        (
            (Person.last_name.ilike(person.last_name)) |
            (Person.first_name.ilike(person.first_name))
        )
    )
    candidate_persons = db.scalars(candidates_stmt).all()

    matches = []
    aliases = set()
    if person.alias:
        aliases.add(person.alias)

    for cand in candidate_persons:
        # Simple attribute similarity scoring
        score = 0.5
        if cand.last_name == person.last_name:
            score += 0.25
        if cand.dob and person.dob and cand.dob == person.dob:
            score += 0.2
        if cand.nationality and person.nationality and cand.nationality == person.nationality:
            score += 0.05
        
        score = round(min(score, 0.98), 2)
        if cand.alias:
            aliases.add(cand.alias)

        matches.append({
            "record_id": cand.id,
            "name": cand.full_name,
            "score": score,
            "matching_attributes": ["last_name"] if cand.last_name == person.last_name else []
        })

    return {
        "canonical_entity": person.id,
        "canonical_name": person.full_name,
        "aliases": list(aliases),
        "matches": matches
    }
