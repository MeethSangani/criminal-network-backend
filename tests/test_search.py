from fastapi.testclient import TestClient

def test_global_search(client: TestClient):
    response = client.get("/api/v1/search?q=Rahul")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    results = data["data"]["results"]
    assert len(results) >= 1
    assert results[0]["id"] == "P017"
    assert results[0]["type"] == "PERSON"
    assert results[0]["name"] == "Rahul Sharma"
