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

def match_person(db: Session, person_data: Dict[str, Any]) -> Dict[str, Any]:
    full_name = person_data.get("full_name", "")
    if not full_name:
        return {"match_found": False, "confidence": 0.0}
    
    all_persons = db.scalars(select(Person)).all()
    for p in all_persons:
        if p.full_name and p.full_name.strip().lower() == full_name.strip().lower():
            return {"match_found": True, "matched_entity_id": p.id, "confidence": 1.0}
        if p.full_name and (full_name.strip().lower() in p.full_name.strip().lower() or p.full_name.strip().lower() in full_name.strip().lower()):
            return {"match_found": True, "matched_entity_id": p.id, "confidence": 0.85}

    return {"match_found": False, "confidence": 0.0}

def match_vehicle(db: Session, vehicle_data: Dict[str, Any]) -> Dict[str, Any]:
    plate = vehicle_data.get("license_plate", "")
    if not plate:
        return {"match_found": False, "confidence": 0.0}
    
    from app.models.vehicle import Vehicle
    veh = db.scalar(select(Vehicle).where(Vehicle.license_plate.ilike(plate)))
    if veh:
        return {"match_found": True, "matched_entity_id": veh.id, "confidence": 1.0}
    
    return {"match_found": False, "confidence": 0.0}

