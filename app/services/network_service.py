from typing import Optional, List, Dict, Any, Set
import networkx as nx
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from app.models.person import Person
from app.models.relationship import Relationship
from app.models.cdr import CDR
from app.models.transaction import Transaction
from app.schemas.network import NodeSchema, EdgeSchema, NetworkGraphData, PathFindingData

class NetworkService:
    def __init__(self, db: Session):
        self.db = db

    def build_full_graph(
        self,
        relationship_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> nx.Graph:
        """Construct a NetworkX Graph from database relationships, CDRs, and Transactions."""
        G = nx.Graph()

        # 1. Add Person nodes
        persons = self.db.scalars(select(Person)).all()
        for p in persons:
            G.add_node(p.id, label=p.full_name, type="PERSON")

        # 2. Add Explicit Relationships
        rel_stmt = select(Relationship)
        if relationship_type:
            rel_stmt = rel_stmt.where(Relationship.relationship_type == relationship_type)
        
        relationships = self.db.scalars(rel_stmt).all()
        for rel in relationships:
            if not G.has_node(rel.source_id):
                G.add_node(rel.source_id, label=rel.source_id, type=rel.source_type)
            if not G.has_node(rel.target_id):
                G.add_node(rel.target_id, label=rel.target_id, type=rel.target_type)
            
            G.add_edge(
                rel.source_id,
                rel.target_id,
                type=rel.relationship_type,
                timestamp=rel.start_date.isoformat() if rel.start_date else None
            )

        # 3. Add Call Detail Records (CDRs)
        cdr_stmt = select(CDR)
        cdrs = self.db.scalars(cdr_stmt).all()
        for c in cdrs:
            src = c.caller_person_id or c.caller_phone
            tgt = c.receiver_person_id or c.receiver_phone
            if not G.has_node(src):
                G.add_node(src, label=c.caller_phone, type="PHONE" if not c.caller_person_id else "PERSON")
            if not G.has_node(tgt):
                G.add_node(tgt, label=c.receiver_phone, type="PHONE" if not c.receiver_person_id else "PERSON")
            
            G.add_edge(
                src,
                tgt,
                type="CALLED",
                timestamp=c.timestamp.isoformat() if c.timestamp else None,
                evidence_id=f"CDR-{c.id}"
            )

        # 4. Add Financial Transactions
        tx_stmt = select(Transaction)
        transactions = self.db.scalars(tx_stmt).all()
        for tx in transactions:
            src = tx.sender_person_id or tx.sender_account
            tgt = tx.receiver_person_id or tx.receiver_account
            if not G.has_node(src):
                G.add_node(src, label=tx.sender_account, type="BANK_ACCOUNT" if not tx.sender_person_id else "PERSON")
            if not G.has_node(tgt):
                G.add_node(tgt, label=tx.receiver_account, type="BANK_ACCOUNT" if not tx.receiver_person_id else "PERSON")

            G.add_edge(
                src,
                tgt,
                type="TRANSFERRED_FUNDS",
                timestamp=tx.timestamp.isoformat() if tx.timestamp else None,
                evidence_id=f"TX-{tx.id}"
            )

        return G

    def get_person_network(
        self,
        person_id: str,
        depth: int = 2,
        relationship_type: Optional[str] = None
    ) -> NetworkGraphData:
        G = self.build_full_graph(relationship_type=relationship_type)
        
        if not G.has_node(person_id):
            # Check if person exists in DB even if disconnected
            p = self.db.scalar(select(Person).where(Person.id == person_id))
            if not p:
                return NetworkGraphData(nodes=[], edges=[])
            return NetworkGraphData(
                nodes=[NodeSchema(id=p.id, label=p.full_name, type="PERSON")],
                edges=[]
            )

        # Subgraph up to specified depth
        subgraph_nodes: Set[str] = {person_id}
        current_layer = {person_id}
        for _ in range(depth):
            next_layer = set()
            for node in current_layer:
                neighbors = set(G.neighbors(node))
                next_layer.update(neighbors - subgraph_nodes)
            subgraph_nodes.update(next_layer)
            current_layer = next_layer

        subgraph = G.subgraph(subgraph_nodes)

        nodes: List[NodeSchema] = []
        for n, data in subgraph.nodes(data=True):
            nodes.append(
                NodeSchema(
                    id=n,
                    label=data.get("label", n),
                    type=data.get("type", "PERSON")
                )
            )

        edges: List[EdgeSchema] = []
        for u, v, data in subgraph.edges(data=True):
            edges.append(
                EdgeSchema(
                    source=u,
                    target=v,
                    type=data.get("type", "CONNECTED"),
                    timestamp=data.get("timestamp")
                )
            )

        return NetworkGraphData(nodes=nodes, edges=edges)

    def find_shortest_path(self, source_id: str, target_id: str) -> Optional[PathFindingData]:
        G = self.build_full_graph()
        if not G.has_node(source_id) or not G.has_node(target_id):
            return None

        try:
            path_nodes = nx.shortest_path(G, source=source_id, target=target_id)
        except nx.NetworkXNoPath:
            return None

        edges: List[EdgeSchema] = []
        evidence_ids: List[str] = []
        for i in range(len(path_nodes) - 1):
            u = path_nodes[i]
            v = path_nodes[i+1]
            edge_data = G.get_edge_data(u, v) or {}
            edges.append(
                EdgeSchema(
                    source=u,
                    target=v,
                    type=edge_data.get("type", "CONNECTED"),
                    timestamp=edge_data.get("timestamp")
                )
            )
            ev_id = edge_data.get("evidence_id")
            if ev_id:
                evidence_ids.append(ev_id)

        return PathFindingData(
            hops=len(path_nodes) - 1,
            nodes=path_nodes,
            edges=edges,
            evidence_ids=evidence_ids
        )
