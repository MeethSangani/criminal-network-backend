from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from app.models.transaction import Transaction
from app.models.cdr import CDR

def detect_financial_anomalies(db: Session, threshold_amount: float = 200000.0) -> List[Dict[str, Any]]:
    anomalies = []
    stmt = select(Transaction).where(Transaction.amount >= threshold_amount)
    high_value_txs = db.scalars(stmt).all()

    for tx in high_value_txs:
        person_id = tx.sender_person_id or tx.receiver_person_id or tx.sender_account
        anomalies.append({
            "anomaly_id": f"ANO-TX-{tx.id}",
            "entity_id": person_id,
            "type": "UNUSUAL_TRANSACTION",
            "score": min(round(tx.amount / 1000000.0, 2), 0.99),
            "timestamp": tx.timestamp.isoformat() if tx.timestamp else None,
            "description": f"High value transaction of {tx.amount} {tx.currency}",
            "evidence_ids": [f"TX-{tx.id}"]
        })
    return anomalies

def detect_communication_anomalies(db: Session, duration_threshold: int = 600) -> List[Dict[str, Any]]:
    anomalies = []
    stmt = select(CDR).where(CDR.duration_seconds >= duration_threshold)
    long_calls = db.scalars(stmt).all()

    for cdr in long_calls:
        person_id = cdr.caller_person_id or cdr.receiver_person_id or cdr.caller_phone
        anomalies.append({
            "anomaly_id": f"ANO-CDR-{cdr.id}",
            "entity_id": person_id,
            "type": "UNUSUAL_COMMUNICATION_DURATION",
            "score": min(round(cdr.duration_seconds / 1800.0, 2), 0.95),
            "timestamp": cdr.timestamp.isoformat() if cdr.timestamp else None,
            "description": f"Unusually long communication duration ({cdr.duration_seconds} seconds)",
            "evidence_ids": [f"CDR-{cdr.id}"]
        })
    return anomalies
