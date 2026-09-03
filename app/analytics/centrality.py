from typing import Dict, Any, List, Set
import networkx as nx

def calculate_graph_centralities(G: nx.Graph) -> Dict[str, Dict[str, float]]:
    if len(G) == 0:
        return {
            "degree": {},
            "betweenness": {},
            "pagerank": {},
            "closeness": {}
        }

    degree_cent = nx.degree_centrality(G)
    
    # Betweenness centrality (optimized with sampling k=50 for large graphs)
    try:
        if len(G) > 100:
            betweenness_cent = nx.betweenness_centrality(G, k=50)
        else:
            betweenness_cent = nx.betweenness_centrality(G)
    except Exception:
        betweenness_cent = {n: 0.0 for n in G.nodes()}

    # PageRank
    try:
        pagerank_cent = nx.pagerank(G, alpha=0.85, max_iter=50)
    except Exception:
        pagerank_cent = {n: 1.0 / max(len(G), 1) for n in G.nodes()}

    # Closeness centrality (for large graphs, degree centrality approximation is used to ensure instant API responses)
    try:
        if len(G) > 100:
            closeness_cent = degree_cent
        else:
            closeness_cent = nx.closeness_centrality(G)
    except Exception:
        closeness_cent = {n: 0.0 for n in G.nodes()}

    return {
        "degree": degree_cent,
        "betweenness": betweenness_cent,
        "pagerank": pagerank_cent,
        "closeness": closeness_cent
    }

def identify_bridge_entities(G: nx.Graph, top_n: int = 5) -> List[str]:
    if len(G) <= 2:
        return list(G.nodes())
    if len(G) > 100:
        betweenness = nx.betweenness_centrality(G, k=50)
    else:
        betweenness = nx.betweenness_centrality(G)
    sorted_nodes = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)
    return [node for node, score in sorted_nodes[:top_n] if score > 0.0]
