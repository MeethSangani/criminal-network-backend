from fastapi.testclient import TestClient

def test_list_persons(client: TestClient):
    response = client.get("/api/v1/persons")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total"] == 3
    assert len(data["data"]) == 3
    assert data["data"][0]["id"] in ["P017", "P024"]

def test_get_person_p017(client: TestClient):
    response = client.get("/api/v1/persons/P017")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    person = data["data"]
    assert person["id"] == "P017"
    assert person["full_name"] == "Rahul Sharma"
    assert person["risk_level"] == "HIGH"
    assert person["status"] == "UNDER_INVESTIGATION"

def test_get_person_not_found(client: TestClient):
    response = client.get("/api/v1/persons/P999")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "PERSON_NOT_FOUND"
    assert "P999" in data["error"]["message"]
