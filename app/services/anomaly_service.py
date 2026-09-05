from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.analytics.anomalies import detect_financial_anomalies, detect_communication_anomalies

class AnomalyService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_anomalies(self) -> List[Dict[str, Any]]:
        fin_anomalies = detect_financial_anomalies(self.db)
        comm_anomalies = detect_communication_anomalies(self.db)
        return fin_anomalies + comm_anomalies

    def detect_anomalies(self) -> List[Dict[str, Any]]:
        return self.get_all_anomalies()

    def get_anomalies_for_person(self, person_id: str) -> List[Dict[str, Any]]:
        all_anomalies = self.get_all_anomalies()
        return [ano for ano in all_anomalies if ano.get("entity_id") == person_id]

