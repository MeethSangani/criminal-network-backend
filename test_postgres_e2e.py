import json
from fastapi.testclient import TestClient
from app.main import app

def test_full_system_integration():
    client = TestClient(app)
    print("\n================ SYSTEM INTEGRATION TEST ================")

    # 1. Health Check
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["data"]["database"] == "connected"
    print("[OK] Health Check API: OK (Database connected)")

    # 2. List Persons
    r = client.get("/api/v1/persons")
    assert r.status_code == 200
    assert r.json()["total"] == 500
    print(f"[OK] Persons API: OK ({r.json()['total']} persons listed)")

    # 3. Person Detail
    r = client.get("/api/v1/persons/P017")
    assert r.status_code == 200
    assert r.json()["data"]["id"] == "P017"
    print(f"[OK] Person Detail API (P017): OK ({r.json()['data']['full_name']})")

    # 4. Multi-Entity Search
    r = client.get("/api/v1/search?q=Aryan")
    assert r.status_code == 200
    assert len(r.json()["data"]["results"]) >= 1
    print(f"[OK] Search API: OK ({len(r.json()['data']['results'])} matches found for 'Aryan')")

    # 5. Network Graph API
    r = client.get("/api/v1/persons/P017/network?depth=2")
    assert r.status_code == 200
    nodes = r.json()["data"]["nodes"]
    edges = r.json()["data"]["edges"]
    print(f"[OK] Graph Network API: OK ({len(nodes)} nodes, {len(edges)} edges)")

    # 6. Pathfinding API
    r = client.get("/api/v1/network/path?source=P017&target=P031")
    assert r.status_code == 200
    path = r.json()["data"]
    print(f"[OK] Pathfinding API: OK (Path: {' -> '.join(path['nodes'])}, Hops: {path['hops']})")

    # 7. Graph Analytics & Priority Score
    r_analytics = client.get("/api/v1/persons/P017/analytics")
    r_priority = client.get("/api/v1/persons/P017/priority")
    assert r_analytics.status_code == 200
    assert r_priority.status_code == 200
    priority_score = r_priority.json()["data"]["score"]
    print(f"[OK] Analytics & Priority API: OK (P017 Priority Score: {priority_score}/100)")

    # 8. Communities & Anomalies
    r_comm = client.get("/api/v1/communities")
    r_ano = client.get("/api/v1/anomalies")
    assert r_comm.status_code == 200
    assert r_ano.status_code == 200
    print(f"[OK] Intelligence APIs: OK ({len(r_comm.json()['data'])} communities, {len(r_ano.json()['data'])} anomalies detected)")

    # 9. Evidence Traceability
    r = client.get("/api/v1/evidence/CDR00001")
    assert r.status_code == 200
    print(f"[OK] Evidence Traceability API: OK ({r.json()['data']['title']})")

    # 10. AI Assistant Query
    r = client.post("/api/v1/ai/query", json={"question": "How is P017 connected to P031?"})
    assert r.status_code == 200
    print(f"[OK] AI Assistant API: OK (Answer length: {len(r.json()['data']['answer'])} chars)")

    # 11. Network Simulation
    r = client.post("/api/v1/simulation/remove-node", json={"entity_id": "P017"})
    assert r.status_code == 200
    sim = r.json()["data"]
    print(f"[OK] Network Simulation API: OK (Removed P017 -> Components change: {sim['before']['connected_components']} -> {sim['after']['connected_components']})")

    print("\n================ ALL 11 ENDPOINT CATEGORIES PASSED PERFECTLY ================\n")

if __name__ == "__main__":
    test_full_system_integration()
