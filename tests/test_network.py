from fastapi.testclient import TestClient

def test_person_network(client: TestClient):
    response = client.get("/api/v1/persons/P017/network?depth=2")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    net = data["data"]
    nodes = {n["id"] for n in net["nodes"]}
    assert "P017" in nodes
    assert "P024" in nodes

def test_network_pathfinding(client: TestClient):
    response = client.get("/api/v1/network/path?source=P017&target=P031")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    path = data["data"]
    assert path["hops"] == 2
    assert path["nodes"] == ["P017", "P024", "P031"]
