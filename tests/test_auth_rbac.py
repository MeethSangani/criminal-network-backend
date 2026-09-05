import pytest

def test_auth_registration_and_login(client):
    # 1. Register Citizen User
    reg_res = client.post("/api/v1/auth/register", json={
        "username": "citizen_test",
        "email": "citizen@test.com",
        "password": "password123",
        "full_name": "Test Citizen",
        "role": "CITIZEN"
    })
    assert reg_res.status_code == 201
    data = reg_res.json()
    assert data["success"] is True
    assert "access_token" in data
    assert data["user"]["username"] == "citizen_test"

    # 2. Login User
    login_res = client.post("/api/v1/auth/login", json={
        "username_or_email": "citizen_test",
        "password": "password123"
    })
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert token_data["success"] is True
    token = token_data["access_token"]

    # 3. Get /auth/me with Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["user"]["email"] == "citizen@test.com"

def test_citizen_report_submission_and_privacy(client):
    # Register Citizen 1
    c1 = client.post("/api/v1/auth/register", json={
        "username": "citizen1", "email": "c1@test.com", "password": "pass", "role": "CITIZEN"
    }).json()
    token1 = c1["access_token"]

    # Register Citizen 2
    c2 = client.post("/api/v1/auth/register", json={
        "username": "citizen2", "email": "c2@test.com", "password": "pass", "role": "CITIZEN"
    }).json()
    token2 = c2["access_token"]

    # Citizen 1 submits report
    h1 = {"Authorization": f"Bearer {token1}"}
    rep_res = client.post("/api/v1/citizen-reports", json={
        "title": "Suspicious Activity Near Warehouse",
        "description": "Black SUV plate MH01AB1234 parked near suspicious container.",
        "location": "Sector 4 Warehouse",
        "vehicle_details": "MH01AB1234 Black SUV"
    }, headers=h1)
    assert rep_res.status_code == 201
    rep_data = rep_res.json()["report"]
    assert rep_data["status"] == "PENDING"
    report_id = rep_data["id"]

    # Citizen 1 views own report
    get1 = client.get(f"/api/v1/citizen-reports/{report_id}", headers=h1)
    assert get1.status_code == 200

    # Privacy Check: Citizen 2 tries to view Citizen 1's report (Must fail with 403)
    h2 = {"Authorization": f"Bearer {token2}"}
    get2 = client.get(f"/api/v1/citizen-reports/{report_id}", headers=h2)
    assert get2.status_code == 403
    assert get2.json()["error"]["code"] == "PRIVACY_RESTRICTION"

def test_admin_review_and_rbac(client):
    # Register Admin
    admin_reg = client.post("/api/v1/auth/register", json={
        "username": "admin_user", "email": "admin@test.com", "password": "adminpassword", "role": "ADMIN"
    }).json()
    admin_token = admin_reg["access_token"]
    h_admin = {"Authorization": f"Bearer {admin_token}"}

    # Register Citizen and submit report
    c_reg = client.post("/api/v1/auth/register", json={
        "username": "c_report_user", "email": "c_rep@test.com", "password": "pass", "role": "CITIZEN"
    }).json()
    h_citizen = {"Authorization": f"Bearer {c_reg['access_token']}"}

    sub_res = client.post("/api/v1/citizen-reports", json={
        "title": "Hawala Transfer Suspected",
        "description": "Large cash handoff observed at shop."
    }, headers=h_citizen).json()
    rep_id = sub_res["report"]["id"]

    # Non-Admin (Citizen) tries to access Admin user list -> Must fail 403
    fail_users = client.get("/api/v1/admin/users", headers=h_citizen)
    assert fail_users.status_code == 403

    # Admin lists pending reports
    list_res = client.get("/api/v1/admin/reports", headers=h_admin)
    assert list_res.status_code == 200
    assert list_res.json()["count"] >= 1

    # Admin reviews and approves report
    rev_res = client.post(f"/api/v1/admin/reports/{rep_id}/review", json={
        "action": "APPROVE",
        "notes": "Verified with local station CCTV"
    }, headers=h_admin)
    assert rev_res.status_code == 200
    assert rev_res.json()["report"]["status"] == "APPROVED"

    # Admin views audit logs
    audit_res = client.get("/api/v1/admin/audit-logs", headers=h_admin)
    assert audit_res.status_code == 200
    assert audit_res.json()["count"] >= 1

def test_incremental_case_ingestion(client):
    # Register Investigator
    inv = client.post("/api/v1/auth/register", json={
        "username": "investigator_john", "email": "john@sih.gov.in", "password": "invpassword", "role": "INVESTIGATOR"
    }).json()
    h_inv = {"Authorization": f"Bearer {inv['access_token']}"}

    # Post new case for ingestion
    case_res = client.post("/api/v1/cases", json={
        "title": "Cyber Extortion Syndicate File",
        "description": "Suspect Rahul Sharma (P017) linked with new vehicle MH12CX9999 and associate Vikram Singh.",
        "type": "CYBERCRIME"
    }, headers=h_inv)

    assert case_res.status_code == 201
    c_data = case_res.json()
    assert c_data["success"] is True
    assert "case" in c_data
    assert c_data["summary"]["persons_resolved"] != []
