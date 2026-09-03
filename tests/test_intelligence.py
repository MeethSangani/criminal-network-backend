from fastapi.testclient import TestClient

def test_communities(client: TestClient):
    response = client.get("/api/v1/communities")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) >= 1

def test_anomalies(client: TestClient):
    response = client.get("/api/v1/anomalies")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)

def test_entity_resolution(client: TestClient):
    response = client.get("/api/v1/entity-resolution/P017")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    res = data["data"]
    assert res["canonical_entity"] == "P017"

def test_nlp_extract(client: TestClient):
    response = client.post(
        "/api/v1/nlp/extract",
        json={"text": "Rahul Sharma met Ajay Kumar near Andheri.", "report_id": "REP-99"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    entities = data["data"]["entities"]
    assert len(entities) >= 1
