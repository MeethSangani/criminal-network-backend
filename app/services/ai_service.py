import os
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
import networkx as nx

from app.config import settings
from app.models.person import Person
from app.models.vehicle import Vehicle
from app.models.phone import Phone
from app.models.bank_account import BankAccount
from app.models.case import Case
from app.models.organization import Organization
from app.models.cdr import CDR
from app.models.transaction import Transaction
from app.models.relationship import Relationship
from app.services.network_service import NetworkService
from app.services.anomaly_service import AnomalyService
from app.analytics.centrality import calculate_graph_centralities

logger = logging.getLogger("criminal_network.ai_service")

class AIService:
    """
    Universal Multi-Entity Law Enforcement AI Assistant Service.
    Supports queries for Persons, Vehicles, Phone Numbers, Bank Accounts, Cases, and Organizations.
    Uses Google Gemini 2.5 Flash API with RAG database context & automated threat flagging.
    """

    def __init__(self, db: Session):
        self.db = db
        self.net_service = NetworkService(db)
        self.anomaly_service = AnomalyService(db)

    def _gather_database_context(self, question: str) -> Dict[str, Any]:
        q_upper = question.upper()
        q_words = [w.strip("?,.!") for w in q_upper.split()]

        matched_persons = []
        matched_vehicles = []
        matched_phones = []
        matched_accounts = []
        matched_cases = []
        matched_orgs = []

        # 1. Vehicle Search (by Plate or ID)
        all_vehicles = self.db.scalars(select(Vehicle)).all()
        for v in all_vehicles:
            if v.id.upper() in q_upper or v.license_plate.upper() in q_upper or any(w in v.license_plate.upper() for w in q_words if len(w) >= 4):
                matched_vehicles.append(v)
                if v.owner_id:
                    p = self.db.get(Person, v.owner_id)
                    if p and p not in matched_persons:
                        matched_persons.append(p)

        # 2. Phone Search (by Number or ID)
        all_phones = self.db.scalars(select(Phone)).all()
        for ph in all_phones:
            if ph.id.upper() in q_upper or ph.phone_number in q_upper:
                matched_phones.append(ph)
                if ph.owner_id:
                    p = self.db.get(Person, ph.owner_id)
                    if p and p not in matched_persons:
                        matched_persons.append(p)

        # 3. Bank Account Search (by Account Number or ID)
        all_accounts = self.db.scalars(select(BankAccount)).all()
        for acc in all_accounts:
            if acc.id.upper() in q_upper or acc.account_number in q_upper:
                matched_accounts.append(acc)
                if acc.owner_id:
                    p = self.db.get(Person, acc.owner_id)
                    if p and p not in matched_persons:
                        matched_persons.append(p)

        # 4. Case Search (by Case Number or ID)
        all_cases = self.db.scalars(select(Case)).all()
        for c in all_cases:
            if c.id.upper() in q_upper or c.case_number.upper() in q_upper or (c.type and c.type.upper() in q_upper):
                matched_cases.append(c)

        # 5. Organization Search
        all_orgs = self.db.scalars(select(Organization)).all()
        for o in all_orgs:
            if o.id.upper() in q_upper or o.name.upper() in q_upper:
                matched_orgs.append(o)

        # 6. Person Search (by Name or ID)
        all_persons = self.db.scalars(select(Person)).all()
        for p in all_persons:
            if p.id.upper() in q_upper or (p.first_name and p.first_name.upper() in q_upper) or (p.last_name and p.last_name.upper() in q_upper) or (p.full_name and p.full_name.upper() in q_upper):
                if p not in matched_persons:
                    matched_persons.append(p)

        if not (matched_persons or matched_vehicles or matched_phones or matched_accounts or matched_cases or matched_orgs):
            high_risk = self.db.scalars(select(Person).where(Person.risk_level == "HIGH").limit(3)).all()
            matched_persons.extend(high_risk)

        person_ids = [p.id for p in matched_persons]

        # 7. Pathfinding between first two mentioned persons
        paths_context = []
        if len(person_ids) >= 2:
            path_res = self.net_service.find_shortest_path(person_ids[0], person_ids[1])
            if path_res:
                paths_context.append(path_res.model_dump() if hasattr(path_res, "model_dump") else dict(path_res))

        # 8. Relationships / Graph Edges
        rel_context = []
        if person_ids:
            rels = self.db.scalars(
                select(Relationship).where(
                    or_(Relationship.source_id.in_(person_ids), Relationship.target_id.in_(person_ids))
                ).limit(15)
            ).all()
            for r in rels:
                rel_context.append({
                    "id": r.id,
                    "source": f"{r.source_type}:{r.source_id}",
                    "relationship": r.relationship_type,
                    "target": f"{r.target_type}:{r.target_id}",
                    "confidence": r.confidence_score
                })

        # 9. Call Detail Records (CDRs)
        cdrs_found = []
        phone_nums = [ph.phone_number for ph in matched_phones]
        if person_ids or phone_nums:
            cdrs = self.db.scalars(
                select(CDR).where(
                    or_(
                        CDR.caller_person_id.in_(person_ids),
                        CDR.receiver_person_id.in_(person_ids),
                        CDR.caller_phone.in_(phone_nums),
                        CDR.receiver_phone.in_(phone_nums)
                    )
                ).limit(15)
            ).all()
            for c in cdrs:
                cdrs_found.append({
                    "id": c.id,
                    "caller": c.caller_person_id or c.caller_phone,
                    "receiver": c.receiver_person_id or c.receiver_phone,
                    "duration_seconds": c.duration_seconds,
                    "timestamp": str(c.timestamp)
                })

        # 10. Financial Transactions
        txs_found = []
        acc_ids = [acc.id for acc in matched_accounts]
        if person_ids or acc_ids:
            txs = self.db.scalars(
                select(Transaction).where(
                    or_(
                        Transaction.sender_person_id.in_(person_ids),
                        Transaction.receiver_person_id.in_(person_ids),
                        Transaction.sender_account.in_(acc_ids),
                        Transaction.receiver_account.in_(acc_ids)
                    )
                ).limit(15)
            ).all()
            for t in txs:
                txs_found.append({
                    "id": t.id,
                    "sender": t.sender_person_id or t.sender_account,
                    "receiver": t.receiver_person_id or t.receiver_account,
                    "amount": t.amount,
                    "type": t.transaction_type,
                    "timestamp": str(t.timestamp)
                })

        # 11. Anomalies
        all_anomalies = self.anomaly_service.get_all_anomalies()
        matched_anomalies = [a for a in all_anomalies if any(p_id in str(a) for p_id in person_ids)] if person_ids else all_anomalies[:5]

        # 12. Determine Flag & Threat Assessment
        flag_status = "CLEAN"
        risk_score = 45
        if matched_vehicles:
            flag_status = "FLAGGED: SUSPECT VEHICLE LINK"
            risk_score = 78
        if any(p.risk_level == "HIGH" for p in matched_persons):
            flag_status = "FLAGGED: HIGH RISK SUSPECT"
            risk_score = 92
        if len(txs_found) > 5 or any(t["amount"] > 50000 for t in txs_found):
            flag_status = "FLAGGED: HAWALA / FINANCIAL SPIKE"
            risk_score = 88

        return {
            "query": question,
            "flag_status": flag_status,
            "risk_score": risk_score,
            "matched_vehicles": [{"id": v.id, "plate": v.license_plate, "make": v.make, "model": v.model, "owner_id": v.owner_id} for v in matched_vehicles],
            "matched_phones": [{"id": ph.id, "number": ph.phone_number, "carrier": ph.carrier, "owner_id": ph.owner_id} for ph in matched_phones],
            "matched_accounts": [{"id": acc.id, "number": acc.account_number, "bank": acc.bank_name, "owner_id": acc.owner_id} for acc in matched_accounts],
            "matched_cases": [{"id": c.id, "number": c.case_number, "type": c.type, "status": c.status, "priority": c.priority, "description": c.description} for c in matched_cases],
            "matched_organizations": [{"id": o.id, "name": o.name, "type": o.type} for o in matched_orgs],
            "persons_profile": [{"id": p.id, "full_name": p.full_name, "occupation": p.occupation, "risk_level": p.risk_level, "status": p.status, "notes": p.notes} for p in matched_persons],
            "relationships": rel_context,
            "paths": paths_context,
            "call_logs": cdrs_found,
            "financial_transactions": txs_found,
            "anomalies": matched_anomalies[:5]
        }

    def _query_gemini_api(self, api_key: str, question: str, db_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            prompt = f"""
You are an elite Law Enforcement AI Criminal Intelligence Analyst for a national security agency.
Analyze the investigator's query and the real-time database context below. Provide a comprehensive, professional, highly structured Executive Intelligence Report.

=== REAL-TIME DATABASE CONTEXT (RAG) ===
{json_serialize_context(db_context)}

=== INVESTIGATOR QUERY ===
"{question}"

=== MANDATORY REPORT TEMPLATE FORMAT ===
Format your entire response using the following structured Markdown layout:

# [LAW ENFORCEMENT INTELLIGENCE REPORT]
**Primary Target / Subject Analyzed:** [Name / Vehicle Plate / Phone / Account / ID]
**Investigative Threat Status:** [{db_context.get('flag_status', 'FLAGGED: HIGH RISK')}]
**Composite Threat Risk Score:** [{db_context.get('risk_score', 85)} / 100]

---

## 1. Primary Subject & Entity Overview
- Detail the exact entity details (Vehicle Plate, Owner Name, Phone, Account, Occupation, Risk Level, Status).

## 2. Network & Case Connections
- Detail how this entity is linked to other suspects, vehicles, phone numbers, bank accounts, organizations, or active crime case files.
- Mention specific multi-hop connections or path links found in the database graph.

## 3. Verified Evidence Traceability Log
List exact IDs for verification in court:
- **Call Detail Records (CDRs):** [List CDR IDs e.g. CDR00001]
- **Financial Transactions:** [List TX IDs e.g. TX00001]
- **Case Files & Vehicles:** [List Case IDs and Vehicle IDs]

## 4. Suspicious Pattern & Anomaly Triggers
- Explain any unusual call durations, suspicious bank wire amounts, or flagged high-risk behaviors.

## 5. Actionable Next Steps for Law Enforcement
1. [Recommendation 1 - e.g. Issue surveillance warrant / intercept calls]
2. [Recommendation 2 - e.g. Freeze linked bank account]
3. [Recommendation 3 - e.g. Interrogate primary driver/owner]
"""

            model_name = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")
            answer_text = None

            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                answer_text = response.text
            except Exception as e1:
                logger.warning(f"google.genai SDK attempt failed: {e1}")
                try:
                    import google.generativeai as genai_legacy
                    genai_legacy.configure(api_key=api_key)
                    m = genai_legacy.GenerativeModel(model_name)
                    res = m.generate_content(prompt)
                    answer_text = res.text
                except Exception as e2:
                    logger.warning(f"google.generativeai legacy attempt failed: {e2}")

            if answer_text:
                return {
                    "answer": answer_text,
                    "engine": f"Google Gemini API ({model_name})",
                    "flag_status": db_context.get("flag_status"),
                    "risk_score": db_context.get("risk_score"),
                    "evidence": self._extract_evidence_ids(db_context),
                    "connected_entities": self._extract_connected_entities(db_context),
                    "reason": "Generated using real-time RAG context retrieval and Gemini 2.5 Flash intelligence reasoning.",
                    "limitations": "AI-generated investigative report. Verify all evidence against primary database records before court filings."
                }
        except Exception as e:
            logger.error(f"Gemini API execution failed: {e}")

        return None

    def _extract_evidence_ids(self, db_context: Dict[str, Any]) -> List[str]:
        ev_ids = []
        for c in db_context.get("call_logs", []):
            ev_ids.append(f"CDR-{c['id']}")
        for t in db_context.get("financial_transactions", []):
            ev_ids.append(f"TX-{t['id']}")
        for v in db_context.get("matched_vehicles", []):
            ev_ids.append(f"VEH-{v['id']}")
        for cs in db_context.get("matched_cases", []):
            ev_ids.append(f"CASE-{cs['id']}")
        return list(set(ev_ids))[:10]

    def _extract_connected_entities(self, db_context: Dict[str, Any]) -> List[str]:
        entities = []
        for p in db_context.get("persons_profile", []):
            entities.append(p["id"])
        for v in db_context.get("matched_vehicles", []):
            entities.append(v["id"])
        for ph in db_context.get("matched_phones", []):
            entities.append(ph["id"])
        for acc in db_context.get("matched_accounts", []):
            entities.append(acc["id"])
        return list(set(entities))

    def _fallback_local_engine(self, question: str, db_context: Dict[str, Any]) -> Dict[str, Any]:
        vehicles = db_context.get("matched_vehicles", [])
        persons = db_context.get("persons_profile", [])
        cases = db_context.get("matched_cases", [])
        cdrs = db_context.get("call_logs", [])
        txs = db_context.get("financial_transactions", [])
        
        lines = []
        lines.append("# LAW ENFORCEMENT INTELLIGENCE REPORT (OFFLINE ENGINE)")
        lines.append(f"**Investigative Threat Status:** {db_context.get('flag_status', 'FLAGGED')}")
        lines.append(f"**Composite Risk Score:** {db_context.get('risk_score', 80)} / 100\n")
        lines.append("---")
        
        if vehicles:
            v = vehicles[0]
            lines.append(f"## 1. Primary Vehicle Details")
            lines.append(f"- **Vehicle ID:** {v['id']} | **Plate:** {v['plate']}")
            lines.append(f"- **Make/Model:** {v['make']} {v['model']}")
            lines.append(f"- **Registered Owner ID:** {v['owner_id']}")
        elif persons:
            p = persons[0]
            lines.append(f"## 1. Primary Suspect Details")
            lines.append(f"- **Person ID:** {p['id']} | **Full Name:** {p['full_name']}")
            lines.append(f"- **Occupation:** {p['occupation']} | **Status:** {p['status']}")
            lines.append(f"- **Risk Level:** {p['risk_level']}")
        else:
            lines.append(f"## 1. Query Analysis")
            lines.append(f"- Query '{question}' matched database graph records.")

        lines.append(f"\n## 2. Connected Network & Evidence")
        lines.append(f"- **Connected Persons:** {', '.join([p['id'] for p in persons[:4]]) if persons else 'None'}")
        lines.append(f"- **Call Logs (CDRs):** {len(cdrs)} records found")
        lines.append(f"- **Financial Transactions:** {len(txs)} wire transfers found")
        if cases:
            lines.append(f"- **Associated Case Files:** {', '.join([c['number'] for c in cases])}")

        lines.append(f"\n## 3. Actionable Next Steps")
        lines.append("1. Issue law enforcement trace on linked communications and vehicle movements.")
        lines.append("2. Freeze associated financial accounts pending further investigative audit.")

        return {
            "answer": "\n".join(lines),
            "engine": "Local Deterministic Graph Engine (Offline Fallback)",
            "flag_status": db_context.get("flag_status"),
            "risk_score": db_context.get("risk_score"),
            "evidence": self._extract_evidence_ids(db_context),
            "connected_entities": self._extract_connected_entities(db_context),
            "reason": "Query processed using local database graph context extraction.",
            "limitations": "Add GEMINI_API_KEY to .env to enable live Gemini LLM intelligence reporting."
        }

    def process_query(self, question: str) -> Dict[str, Any]:
        db_context = self._gather_database_context(question)
        api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        if api_key and api_key.strip() and api_key.strip() != "your_gemini_api_key_here":
            llm_result = self._query_gemini_api(api_key.strip(), question, db_context)
            if llm_result:
                return llm_result

        return self._fallback_local_engine(question, db_context)

def json_serialize_context(ctx: Dict[str, Any]) -> str:
    import json
    return json.dumps(ctx, indent=2, default=str)
