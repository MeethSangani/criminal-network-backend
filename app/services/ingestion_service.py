import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.case import Case
from app.models.person import Person
from app.models.vehicle import Vehicle
from app.models.phone import Phone
from app.models.organization import Organization
from app.models.relationship import Relationship
from app.nlp.ner import extract_entities
from app.entity_resolution.matching import match_person, match_vehicle
from app.services.network_service import NetworkService
from app.services.audit_service import log_audit_event

class IngestionService:
    """
    Incremental Data & Case Ingestion Service.
    Extracts entities via NLP/NER, resolves them against existing DB records without duplication,
    links new relationships, updates the NetworkX graph, and logs audit events.
    """

    def __init__(self, db: Session):
        self.db = db
        self.network_service = NetworkService(db)

    def ingest_case_and_entities(
        self,
        title: str,
        description: str,
        case_type: Optional[str] = "GENERAL",
        created_by_id: Optional[str] = None,
        created_by_username: Optional[str] = None
    ) -> Dict[str, Any]:
        """Ingest new case file and incrementally extract and resolve entities."""
        # 1. Create Case Record
        case_id = f"C-{uuid.uuid4().hex[:6].upper()}"
        case_num = f"CASE-{uuid.uuid4().hex[:6].upper()}"
        case = Case(
            id=case_id,
            case_number=case_num,
            title=title,
            description=description,
            type=case_type or "GENERAL",
            status="ACTIVE"
        )
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)

        # 2. Extract Entities via NER
        text_content = f"{title}. {description}"
        ner_entities = extract_entities(text_content)

        resolved_persons = []
        new_persons_created = 0
        resolved_vehicles = []
        new_vehicles_created = 0

        # 3. Entity Resolution & Creation for Persons
        for p_name in ner_entities.get("persons", []):
            match_res = match_person(self.db, {"full_name": p_name})
            if match_res.get("match_found") and match_res.get("confidence", 0) >= 0.70:
                matched_id = match_res.get("matched_entity_id")
                person = self.db.get(Person, matched_id)
                if person and person not in resolved_persons:
                    resolved_persons.append(person)
            else:
                p_id = f"P{uuid.uuid4().hex[:5].upper()}"
                name_parts = p_name.strip().split(maxsplit=1)
                first_n = name_parts[0] if name_parts else p_name
                last_n = name_parts[1] if len(name_parts) > 1 else ""
                new_person = Person(
                    id=p_id,
                    first_name=first_n,
                    last_name=last_n,
                    full_name=p_name,
                    occupation="Suspect Identified via Ingestion",
                    status="UNDER_INVESTIGATION",
                    risk_level="MEDIUM"
                )
                self.db.add(new_person)
                self.db.commit()
                self.db.refresh(new_person)
                resolved_persons.append(new_person)
                new_persons_created += 1

        # 4. Entity Resolution & Creation for Vehicles
        for v_plate in ner_entities.get("vehicles", []):
            match_v = match_vehicle(self.db, {"license_plate": v_plate})
            if match_v.get("match_found") and match_v.get("confidence", 0) >= 0.70:
                matched_v_id = match_v.get("matched_entity_id")
                veh = self.db.get(Vehicle, matched_v_id)
                if veh and veh not in resolved_vehicles:
                    resolved_vehicles.append(veh)
            else:
                v_id = f"V{uuid.uuid4().hex[:5].upper()}"
                new_veh = Vehicle(
                    id=v_id,
                    license_plate=v_plate,
                    make="Unknown",
                    model="Unknown",
                    color="Unknown",
                    owner_id=resolved_persons[0].id if resolved_persons else None
                )
                self.db.add(new_veh)
                self.db.commit()
                self.db.refresh(new_veh)
                resolved_vehicles.append(new_veh)
                new_vehicles_created += 1

        # 5. Create Relationships between extracted entities
        new_relationships = 0
        if len(resolved_persons) >= 2:
            for i in range(len(resolved_persons) - 1):
                p1 = resolved_persons[i]
                p2 = resolved_persons[i + 1]
                rel = Relationship(
                    id=f"R-{uuid.uuid4().hex[:6].upper()}",
                    source_id=p1.id,
                    source_type="PERSON",
                    target_id=p2.id,
                    target_type="PERSON",
                    relationship_type="ASSOCIATE_IN_CASE",
                    confidence_score=0.9
                )
                self.db.add(rel)
                new_relationships += 1
            self.db.commit()

        # 6. Invalidate & Refresh Network Graph Cache
        try:
            self.network_service.clear_cache()
        except Exception:
            pass

        # 7. Audit Log Entry
        log_audit_event(
            db=self.db,
            action="CASE_INGESTION",
            user_id=created_by_id,
            username=created_by_username,
            resource_type="CASE",
            resource_id=case.id,
            details=f"Ingested case {case.case_number}. Resolved {len(resolved_persons)} persons ({new_persons_created} new) and {len(resolved_vehicles)} vehicles ({new_vehicles_created} new)."
        )

        return {
            "success": True,
            "case": case.to_dict(),
            "summary": {
                "persons_resolved": [
                    {"id": p.id, "full_name": p.full_name, "risk_level": p.risk_level} for p in resolved_persons
                ],
                "new_persons_created": new_persons_created,
                "vehicles_resolved": [
                    {"id": v.id, "license_plate": v.license_plate, "make": v.make} for v in resolved_vehicles
                ],
                "new_vehicles_created": new_vehicles_created,
                "relationships_created": new_relationships
            }
        }
