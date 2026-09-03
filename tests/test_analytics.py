from fastapi.testclient import TestClient

def test_person_analytics(client: TestClient):
    response = client.get("/api/v1/persons/P017/analytics")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    analytics = data["data"]
    assert analytics["person_id"] == "P017"
    assert "degree" in analytics
    assert "betweenness" in analytics
    assert "pagerank" in analytics

def test_investigation_priority(client: TestClient):
    response = client.get("/api/v1/persons/P017/priority")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    priority = data["data"]
    assert priority["person_id"] == "P017"
    assert priority["score"] > 0
    assert "factors" in priority
    assert len(priority["explanation"]) > 0
