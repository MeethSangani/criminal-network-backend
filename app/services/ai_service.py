import os
import json
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
    Supports dynamic, intent-tailored responses for Persons, Vehicles, Phone Numbers, Bank Accounts, Cases, and Organizations.
    Uses Google Gemini 2.5 Flash API with RAG database context & dynamic prompt synthesis.
    """

    def __init__(self, db: Session):
        self.db = db
        self.net_service = NetworkService(db)
        self.anomaly_service = AnomalyService(db)

    def _detect_query_intent(self, question: str) -> str:
        """Classify investigator question intent for dynamic report formatting."""
        q = question.lower()
        if any(w in q for w in ["vehicle", "plate", "car", "driving", "driver", "registration", "license", "veh-", "v0"]):
            return "VEHICLE_INTENT"
        elif any(w in q for w in ["money", "account", "bank", "transaction", "wire", "transfer", "hawala", "amount", "tx-", "acc"]):
            return "FINANCIAL_INTENT"
        elif any(w in q for w in ["case", "fir", "crime file", "investigation", "syndicate", "c0", "case-"]):
            return "CASE_INTENT"
        elif any(w in q for w in ["trigger", "anomaly", "suspicious", "flag", "alert", "severity"]):
            return "ANOMALY_TRIGGER_INTENT"
        elif any(w in q for w in ["person", "suspect", "who is", "connection", "associates", "p0", "phone", "cdr"]):
            return "SUSPECT_PERSON_INTENT"
        return "GENERAL_INTELLIGENCE"

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

        # 3. Bank Account Search
        all_accounts = self.db.scalars(select(BankAccount)).all()
        for acc in all_accounts:
            if acc.id.upper() in q_upper or acc.account_number in q_upper:
                matched_accounts.append(acc)
                if acc.owner_id:
                    p = self.db.get(Person, acc.owner_id)
                    if p and p not in matched_persons:
                        matched_persons.append(p)

        # 4. Case Search
        all_cases = self.db.scalars(select(Case)).all()
        for c in all_cases:
            if c.id.upper() in q_upper or c.case_number.upper() in q_upper or (c.type and c.type.upper() in q_upper):
                matched_cases.append(c)

        # 5. Organization Search
        all_orgs = self.db.scalars(select(Organization)).all()
        for o in all_orgs:
            if o.id.upper() in q_upper or o.name.upper() in q_upper:
                matched_orgs.append(o)

        # 6. Person Search
        all_persons = self.db.scalars(select(Person)).all()
        for p in all_persons:
            if p.id.upper() in q_upper or (p.first_name and p.first_name.upper() in q_upper) or (p.last_name and p.last_name.upper() in q_upper) or (p.full_name and p.full_name.upper() in q_upper):
                if p not in matched_persons:
                    matched_persons.append(p)

        if not (matched_persons or matched_vehicles or matched_phones or matched_accounts or matched_cases or matched_orgs):
            high_risk = self.db.scalars(select(Person).where(Person.risk_level == "HIGH").limit(3)).all()
            matched_persons.extend(high_risk)

        person_ids = [p.id for p in matched_persons]
        rel_context = []
        if person_ids:
            rels = self.db.scalars(
                select(Relationship).where(
                    or_(
                        Relationship.source_id.in_(person_ids),
                        Relationship.target_id.in_(person_ids)
                    )
                )
            ).all()
            for r in rels[:10]:
                rel_context.append({
                    "source": r.source_id,
                    "target": r.target_id,
                    "type": getattr(r, "relationship_type", "ASSOCIATED"),
                    "weight": getattr(r, "confidence_score", 1.0)
                })

        cdrs_found = []
        if matched_phones:
            phone_nums = [ph.phone_number for ph in matched_phones]
            cdrs = self.db.scalars(
                select(CDR).where(
                    or_(
                        CDR.caller_number.in_(phone_nums),
                        CDR.receiver_number.in_(phone_nums)
                    )
                ).limit(10)
            ).all()
            for c in cdrs:
                cdrs_found.append({
                    "id": c.id,
                    "caller": c.caller_number,
                    "receiver": c.receiver_number,
                    "duration_sec": c.duration_seconds,
                    "timestamp": c.timestamp.isoformat() if c.timestamp else None
                })

        txs_found = []
        if matched_accounts:
            acc_nums = [a.account_number for a in matched_accounts]
            txs = self.db.scalars(
                select(Transaction).where(
                    or_(
                        Transaction.sender_account.in_(acc_nums),
                        Transaction.receiver_account.in_(acc_nums)
                    )
                ).limit(10)
            ).all()
            for t in txs:
                txs_found.append({
                    "id": t.id,
                    "sender": t.sender_account,
                    "receiver": t.receiver_account,
                    "amount": float(t.amount) if t.amount else 0,
                    "timestamp": t.timestamp.isoformat() if t.timestamp else None
                })

        paths_context = []
        if len(person_ids) >= 2:
            try:
                p_path = self.net_service.get_shortest_path(person_ids[0], person_ids[1])
                if p_path:
                    paths_context.append(p_path)
            except Exception:
                pass

        matched_anomalies = self.anomaly_service.detect_anomalies()
        if person_ids:
            matched_anomalies = [a for a in matched_anomalies if a.get("entity_id") in person_ids or a.get("target_id") in person_ids]

        flag_status = "FLAGGED: HIGH RISK" if any(p.risk_level == "HIGH" for p in matched_persons) else "UNDER OBSERVATION"
        risk_score = 88 if flag_status == "FLAGGED: HIGH RISK" else 65

        return {
            "intent": self._detect_query_intent(question),
            "flag_status": flag_status,
            "risk_score": risk_score,
            "matched_vehicles": [
                {
                    "id": v.id,
                    "plate": v.license_plate,
                    "make": v.make,
                    "model": v.model,
                    "color": v.color,
                    "owner_id": v.owner_id
                } for v in matched_vehicles
            ],
            "persons_profile": [
                {
                    "id": p.id,
                    "full_name": p.full_name,
                    "occupation": p.occupation,
                    "status": p.status,
                    "risk_level": p.risk_level
                } for p in matched_persons
            ],
            "matched_phones": [{"id": ph.id, "number": ph.phone_number, "owner_id": ph.owner_id} for ph in matched_phones],
            "matched_accounts": [{"id": acc.id, "number": acc.account_number, "bank": acc.bank_name, "owner_id": acc.owner_id} for acc in matched_accounts],
            "matched_cases": [{"id": cs.id, "number": cs.case_number, "title": cs.title, "status": cs.status} for cs in matched_cases],
            "relationships": rel_context,
            "paths": paths_context,
            "call_logs": cdrs_found,
            "financial_transactions": txs_found,
            "anomalies": matched_anomalies[:5]
        }

    def _query_gemini_api(self, api_key: str, question: str, db_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            intent = db_context.get("intent", "GENERAL_INTELLIGENCE")
            prompt = f"""
You are an elite Law Enforcement AI Criminal Intelligence Analyst for a national security agency.
Analyze the investigator's query directly and synthesize an answer based on the real-time database context (RAG) below.

Query Intent Category: {intent}

=== REAL-TIME DATABASE CONTEXT (RAG) ===
{json_serialize_context(db_context)}

=== INVESTIGATOR QUERY ===
"{question}"

=== INSTRUCTIONS ===
1. Answer the question directly in your opening summary paragraph.
2. Tailor your response dynamically to the query intent ({intent}).
3. Use clean Markdown headings (`#`, `##`, `###`), tables, and bold bullet points.
4. Detail linked entities (Person IDs, Vehicle Plates, Phone Numbers, Accounts, Case File IDs).
5. Highlight threat risk levels and suspicious anomalies.
6. Provide 3 specific, actionable next steps for law enforcement.
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
                    "intent": intent,
                    "flag_status": db_context.get("flag_status"),
                    "risk_score": db_context.get("risk_score"),
                    "evidence": self._extract_evidence_ids(db_context),
                    "connected_entities": self._extract_connected_entities(db_context),
                    "reason": "Dynamic intent-tailored response synthesized using real-time RAG context retrieval and Gemini 2.5 Flash.",
                    "limitations": "AI-generated intelligence report. Verify all evidence against primary database records before court filings."
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
        intent = db_context.get("intent", "GENERAL_INTELLIGENCE")
        vehicles = db_context.get("matched_vehicles", [])
        persons = db_context.get("persons_profile", [])
        cases = db_context.get("matched_cases", [])
        cdrs = db_context.get("call_logs", [])
        txs = db_context.get("financial_transactions", [])
        anomalies = db_context.get("anomalies", [])
        
        lines = []

        if intent == "VEHICLE_INTENT":
            lines.append("# VEHICLE INTELLIGENCE & DRIVER ANALYSIS")
            lines.append(f"**Query Direct Answer:** Analyzed vehicle records for query: *\"{question}\"*")
            lines.append(f"**Threat Status:** {db_context.get('flag_status', 'UNDER OBSERVATION')}")
            lines.append(f"**Risk Score:** {db_context.get('risk_score', 75)} / 100\n---")
            if vehicles:
                v = vehicles[0]
                lines.append(f"## 1. Vehicle Registration & Ownership")
                lines.append(f"- **Vehicle ID:** `{v['id']}` | **License Plate:** `{v['plate']}`")
                lines.append(f"- **Make / Model:** {v['make']} {v['model']} ({v['color']})")
                lines.append(f"- **Registered Owner ID:** `{v['owner_id'] or 'Unknown'}`")
            else:
                lines.append("## 1. Vehicle Registration")
                lines.append("- No direct matching vehicle plate found in immediate context; checking linked suspect vehicles.")
            if persons:
                lines.append(f"\n## 2. Suspected Driver & Associated Person")
                p = persons[0]
                lines.append(f"- **Suspect ID:** `{p['id']}` | **Full Name:** {p['full_name']}")
                lines.append(f"- **Occupation:** {p['occupation']} | **Risk Level:** **{p['risk_level']}**")

        elif intent == "FINANCIAL_INTENT":
            lines.append("# FINANCIAL TRANSACTION & HAWALA ANALYSIS")
            lines.append(f"**Query Direct Answer:** Audited financial accounts and wire transfers for query: *\"{question}\"*")
            lines.append(f"**Threat Status:** {db_context.get('flag_status', 'UNDER OBSERVATION')}")
            lines.append(f"**Risk Score:** {db_context.get('risk_score', 85)} / 100\n---")
            lines.append(f"## 1. Transaction Volume & Account Overview")
            lines.append(f"- **Flagged Transactions Found:** {len(txs)} wire transfers")
            if txs:
                total_vol = sum(t['amount'] for t in txs)
                lines.append(f"- **Cumulative Transfer Volume:** ₹{total_vol:,.2f}")
                lines.append(f"- **Primary Sender Account:** `{txs[0]['sender']}`")
                lines.append(f"- **Primary Receiver Account:** `{txs[0]['receiver']}`")
            if persons:
                lines.append(f"\n## 2. Account Holder Profile")
                lines.append(f"- **Linked Suspect ID:** `{persons[0]['id']}` ({persons[0]['full_name']})")

        elif intent == "CASE_INTENT":
            lines.append("# CASE FILE & SYNDICATE INVESTIGATION REPORT")
            lines.append(f"**Query Direct Answer:** Retrieved investigation file details for query: *\"{question}\"*")
            lines.append(f"**Threat Status:** {db_context.get('flag_status', 'FLAGGED')}\n---")
            if cases:
                c = cases[0]
                lines.append(f"## 1. Primary Case File Summary")
                lines.append(f"- **Case ID:** `{c['id']}` | **Case Number:** `{c['number']}`")
                lines.append(f"- **Title:** {c['title']} | **Status:** `{c['status']}`")
            lines.append(f"\n## 2. Associated Suspects & Evidence")
            lines.append(f"- **Key Persons Linked:** {', '.join([f'`{p['id']}` ({p['full_name']})' for p in persons[:3]]) if persons else 'None'}")
            lines.append(f"- **Evidence Logs:** {len(cdrs)} call logs, {len(txs)} wire transfers")

        elif intent == "ANOMALY_TRIGGER_INTENT":
            lines.append("# INVESTIGATIVE ANOMALY & PATTERN TRIGGER ALERT")
            lines.append(f"**Query Direct Answer:** Triggered investigative indicators for query: *\"{question}\"*")
            lines.append(f"**Severity Level:** **HIGH**\n---")
            lines.append("## 1. Flagged Anomaly Events")
            for a in anomalies[:4]:
                lines.append(f"- **Entity:** `{a.get('entity_id')}` | **Type:** `{a.get('type')}` | **Severity:** `{a.get('severity')}`")
                lines.append(f"  *Reasoning:* {a.get('reason')}")

        else:
            lines.append("# LAW ENFORCEMENT EXECUTIVE INTELLIGENCE REPORT")
            lines.append(f"**Query Analyzed:** *\"{question}\"*")
            lines.append(f"**Investigative Status:** {db_context.get('flag_status', 'UNDER OBSERVATION')}")
            lines.append(f"**Risk Score:** {db_context.get('risk_score', 75)} / 100\n---")
            lines.append("## 1. Intelligence Summary")
            if persons:
                lines.append(f"- **Primary Subject:** `{persons[0]['id']}` — {persons[0]['full_name']} ({persons[0]['occupation']})")
                lines.append(f"- **Threat Level:** **{persons[0]['risk_level']}**")
            lines.append(f"- **Connected Graph Nodes:** {len(persons)} persons, {len(cdrs)} call logs, {len(txs)} wire transfers")

        lines.append(f"\n## Actionable Law Enforcement Next Steps")
        lines.append("1. **Surveillance & Intercept:** Issue interception order on flagged communication endpoints and vehicle movements.")
        lines.append("2. **Asset Freeze:** Freeze linked bank accounts pending formal financial audit.")
        lines.append("3. **Interrogation:** Summons primary suspect for formal statement under criminal procedure.")

        return {
            "answer": "\n".join(lines),
            "engine": "Dynamic Intent Local Graph Engine",
            "intent": intent,
            "flag_status": db_context.get("flag_status"),
            "risk_score": db_context.get("risk_score"),
            "evidence": self._extract_evidence_ids(db_context),
            "connected_entities": self._extract_connected_entities(db_context),
            "reason": f"Dynamic {intent} intelligence generated using local graph context.",
            "limitations": "Set GEMINI_API_KEY in .env for full Gemini 2.5 Flash AI reasoning."
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
    return json.dumps(ctx, indent=2, default=str)
