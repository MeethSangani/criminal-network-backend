from fastapi.testclient import TestClient

def test_evidence_lookup(client: TestClient):
    response = client.get("/api/v1/evidence/CDR-104")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    ev = data["data"]
    assert ev["evidence_id"] == "CDR-104"
    assert ev["source_type"] == "CALL_DETAIL_RECORD"

def test_ai_query_path(client: TestClient):
    response = client.post(
        "/api/v1/ai/query",
        json={"question": "How is P017 connected to P031?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    res = data["data"]
    assert "answer" in res
    assert "reason" in res
    assert "evidence" in res
    assert "limitations" in res
    assert "P017" in res["answer"]

def test_ai_query_priority(client: TestClient):
    response = client.post(
        "/api/v1/ai/query",
        json={"question": "Why is P017 high priority?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Score" in data["data"]["answer"] or "Priority" in data["data"]["answer"] or "HIGH" in data["data"]["answer"] or "risk" in data["data"]["answer"].lower()

def test_node_removal_simulation(client: TestClient):
    response = client.post(
        "/api/v1/simulation/remove-node",
        json={"entity_id": "P017"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    sim = data["data"]
    assert sim["entity_removed"] == "P017"
    assert "before" in sim
    assert "after" in sim
    assert "impact" in sim
