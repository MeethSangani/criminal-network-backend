from app.routers.health import router as health_router
from app.routers.persons import router as persons_router
from app.routers.search import router as search_router
from app.routers.cases import router as cases_router
from app.routers.network import router as network_router
from app.routers.analytics import router as analytics_router
from app.routers.communities import router as communities_router
from app.routers.anomalies import router as anomalies_router
from app.routers.entity_resolution import router as entity_resolution_router
from app.routers.nlp import router as nlp_router
from app.routers.evidence import router as evidence_router
from app.routers.ai import router as ai_router
from app.routers.simulation import router as simulation_router
from app.routers.auth import router as auth_router
from app.routers.citizen_reports import router as citizen_reports_router
from app.routers.admin import router as admin_router

__all__ = [
    "health_router",
    "persons_router",
    "search_router",
    "cases_router",
    "network_router",
    "analytics_router",
    "communities_router",
    "anomalies_router",
    "entity_resolution_router",
    "nlp_router",
    "evidence_router",
    "ai_router",
    "simulation_router",
    "auth_router",
    "citizen_reports_router",
    "admin_router",
]
