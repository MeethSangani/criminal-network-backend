from typing import List, Dict, Any, Set
import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities

def detect_communities(G: nx.Graph) -> List[Dict[str, Any]]:
    if len(G) == 0:
        return []

    # If graph is small or disconnected, handle community division
    try:
        raw_communities = list(greedy_modularity_communities(G))
    except Exception:
        # Fallback to connected components as communities
        raw_communities = list(nx.connected_components(G))

    community_results = []
    for idx, comm in enumerate(raw_communities, 1):
        members = list(comm)
        subgraph = G.subgraph(members)
        
        # Calculate centrality within community to identify key members
        deg = dict(subgraph.degree())
        sorted_members = sorted(deg.items(), key=lambda x: x[1], reverse=True)
        important_entities = [m for m, d in sorted_members[:3]]

        community_results.append({
            "community_id": f"COMM-{idx:02d}",
            "member_count": len(members),
            "members": members,
            "important_entities": important_entities,
            "density": round(nx.density(subgraph), 4) if len(members) > 1 else 1.0
        })

    return community_results
