from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from app.database import get_db
from app.services.person_service import PersonService
from app.schemas.person import PersonResponse, PersonListResponse
from app.models.relationship import Relationship
from app.models.case import Case
from app.models.transaction import Transaction
from app.models.cdr import CDR

router = APIRouter(prefix="/persons", tags=["Persons"])

@router.get("", response_model=PersonListResponse)
def get_persons(
    skip: int = Query(0, ge=0, description="Items to skip"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    db: Session = Depends(get_db)
):
    service = PersonService(db)
    persons, total = service.list_persons(skip=skip, limit=limit)
    return {
        "success": True,
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [PersonResponse.model_validate(p) for p in persons]
    }

@router.get("/{person_id}")
def get_person(person_id: str, db: Session = Depends(get_db)):
    service = PersonService(db)
    person = service.get_person_by_id(person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PERSON_NOT_FOUND",
                "message": f"Person {person_id} was not found"
            }
        )
    return {
        "success": True,
        "data": PersonResponse.model_validate(person)
    }

@router.get("/{person_id}/relationships")
def get_person_relationships(person_id: str, db: Session = Depends(get_db)):
    service = PersonService(db)
    if not service.get_person_by_id(person_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PERSON_NOT_FOUND", "message": f"Person {person_id} was not found"}
        )
    rel_stmt = select(Relationship).where(
        or_(Relationship.source_id == person_id, Relationship.target_id == person_id)
    )
    relationships = db.scalars(rel_stmt).all()
    res = []
    for r in relationships:
        res.append({
            "id": r.id,
            "source_id": r.source_id,
            "target_id": r.target_id,
            "relationship_type": r.relationship_type,
            "confidence_score": r.confidence_score,
            "start_date": r.start_date.isoformat() if r.start_date else None
        })
    return {"success": True, "data": res}

@router.get("/{person_id}/cases")
def get_person_cases(person_id: str, db: Session = Depends(get_db)):
    service = PersonService(db)
    if not service.get_person_by_id(person_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PERSON_NOT_FOUND", "message": f"Person {person_id} was not found"}
        )
    rel_stmt = select(Relationship).where(
        or_(
            (Relationship.source_id == person_id) & (Relationship.target_type == "CASE"),
            (Relationship.target_id == person_id) & (Relationship.source_type == "CASE")
        )
    )
    rels = db.scalars(rel_stmt).all()
    case_ids = [r.target_id if r.source_id == person_id else r.source_id for r in rels]
    cases = db.scalars(select(Case).where(Case.id.in_(case_ids))).all() if case_ids else []
    return {
        "success": True,
        "data": [{"id": c.id, "case_number": c.case_number, "title": c.title, "status": c.status} for c in cases]
    }

@router.get("/{person_id}/transactions")
def get_person_transactions(person_id: str, db: Session = Depends(get_db)):
    service = PersonService(db)
    if not service.get_person_by_id(person_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PERSON_NOT_FOUND", "message": f"Person {person_id} was not found"}
        )
    tx_stmt = select(Transaction).where(
        or_(Transaction.sender_person_id == person_id, Transaction.receiver_person_id == person_id)
    ).order_by(Transaction.timestamp.desc())
    txs = db.scalars(tx_stmt).all()
    return {
        "success": True,
        "data": [
            {
                "id": t.id,
                "sender_account": t.sender_account,
                "receiver_account": t.receiver_account,
                "amount": t.amount,
                "currency": t.currency,
                "timestamp": t.timestamp.isoformat() if t.timestamp else None
            } for t in txs
        ]
    }

@router.get("/{person_id}/communications")
def get_person_communications(person_id: str, db: Session = Depends(get_db)):
    service = PersonService(db)
    if not service.get_person_by_id(person_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PERSON_NOT_FOUND", "message": f"Person {person_id} was not found"}
        )
    cdr_stmt = select(CDR).where(
        or_(CDR.caller_person_id == person_id, CDR.receiver_person_id == person_id)
    ).order_by(CDR.timestamp.desc())
    cdrs = db.scalars(cdr_stmt).all()
    return {
        "success": True,
        "data": [
            {
                "id": c.id,
                "caller_phone": c.caller_phone,
                "receiver_phone": c.receiver_phone,
                "duration_seconds": c.duration_seconds,
                "timestamp": c.timestamp.isoformat() if c.timestamp else None
            } for c in cdrs
        ]
    }

@router.get("/{person_id}/timeline")
def get_person_timeline(person_id: str, db: Session = Depends(get_db)):
    service = PersonService(db)
    if not service.get_person_by_id(person_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PERSON_NOT_FOUND", "message": f"Person {person_id} was not found"}
        )
    events = []
    
    # 1. CDRs
    cdrs = db.scalars(select(CDR).where(or_(CDR.caller_person_id == person_id, CDR.receiver_person_id == person_id))).all()
    for c in cdrs:
        events.append({
            "event_type": "CALL",
            "timestamp": c.timestamp.isoformat() if c.timestamp else None,
            "description": f"Call between {c.caller_phone} and {c.receiver_phone} ({c.duration_seconds}s)",
            "evidence_id": f"CDR-{c.id}"
        })
        
    # 2. Transactions
    txs = db.scalars(select(Transaction).where(or_(Transaction.sender_person_id == person_id, Transaction.receiver_person_id == person_id))).all()
    for t in txs:
        events.append({
            "event_type": "TRANSACTION",
            "timestamp": t.timestamp.isoformat() if t.timestamp else None,
            "description": f"Transfer of {t.amount} {t.currency} from {t.sender_account} to {t.receiver_account}",
            "evidence_id": f"TX-{t.id}"
        })

    events.sort(key=lambda x: x["timestamp"] or "", reverse=True)
    return {"success": True, "data": events}
