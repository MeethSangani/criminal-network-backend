from fastapi.testclient import TestClient

def test_list_cases(client: TestClient):
    response = client.get("/api/v1/cases")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total"] == 1
    assert data["data"][0]["id"] == "C101"

def test_get_case_detail(client: TestClient):
    response = client.get("/api/v1/cases/C101")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["title"] == "Operation CyberShield"
