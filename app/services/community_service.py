from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.services.network_service import NetworkService
from app.analytics.communities import detect_communities
from app.schemas.network import NetworkGraphData

class CommunityService:
    def __init__(self, db: Session):
        self.db = db
        self.net_service = NetworkService(db)

    def get_all_communities(self) -> List[Dict[str, Any]]:
        G = self.net_service.build_full_graph()
        return detect_communities(G)

    def get_community_by_id(self, community_id: str) -> Optional[Dict[str, Any]]:
        communities = self.get_all_communities()
        for comm in communities:
            if comm["community_id"] == community_id:
                return comm
        return None

    def get_community_network(self, community_id: str) -> Optional[NetworkGraphData]:
        comm = self.get_community_by_id(community_id)
        if not comm:
            return None
        members = comm["members"]
        G = self.net_service.build_full_graph()
        subgraph = G.subgraph(members)
        
        nodes = [{"id": n, "label": G.nodes[n].get("label", n), "type": G.nodes[n].get("type", "PERSON")} for n in subgraph.nodes()]
        edges = [{"source": u, "target": v, "type": data.get("type", "CONNECTED"), "timestamp": data.get("timestamp")} for u, v, data in subgraph.edges(data=True)]
        
        return NetworkGraphData(nodes=nodes, edges=edges)
