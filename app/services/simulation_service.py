from typing import Dict, Any, Optional
import networkx as nx
from sqlalchemy.orm import Session
from app.services.network_service import NetworkService

class SimulationService:
    def __init__(self, db: Session):
        self.db = db
        self.net_service = NetworkService(db)

    def simulate_node_removal(self, entity_id: str) -> Optional[Dict[str, Any]]:
        # 1. Build original graph (in-memory NetworkX copy)
        G_before = self.net_service.build_full_graph()
        
        if not G_before.has_node(entity_id):
            return None

        # Gather metrics before removal
        comp_before = nx.number_connected_components(G_before)
        density_before = round(nx.density(G_before), 4)
        neighbors = list(G_before.neighbors(entity_id))

        # 2. Create temporary graph and remove node
        G_after = G_before.copy()
        G_after.remove_node(entity_id)

        comp_after = nx.number_connected_components(G_after)
        density_after = round(nx.density(G_after), 4)

        return {
            "entity_removed": entity_id,
            "before": {
                "total_nodes": len(G_before),
                "total_edges": len(G_before.edges()),
                "connected_components": comp_before,
                "network_density": density_before
            },
            "after": {
                "total_nodes": len(G_after),
                "total_edges": len(G_after.edges()),
                "connected_components": comp_after,
                "network_density": density_after
            },
            "impact": {
                "affected_neighbors": neighbors,
                "component_increase": comp_after - comp_before,
                "density_change": round(density_after - density_before, 4)
            }
        }
