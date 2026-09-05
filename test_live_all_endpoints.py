import json
import random
import time
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000/api/v1"

def make_request(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    
    req_headers = {"Content-Type": "application/json"}
    req_headers.update(headers)

    encoded_data = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=encoded_data, headers=req_headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status_code = resp.getcode()
            body_bytes = resp.read()
            body = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
            return status_code, body
    except urllib.error.HTTPError as e:
        body_bytes = e.read()
        body = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        return e.code, body
    except Exception as ex:
        return 500, {"success": False, "error": str(ex)}

def run_live_tests():
    print("=" * 70)
    print("STARTING LIVE ENDPOINT TESTING ON FASTAPI SERVER (http://localhost:8000)")
    print("=" * 70)

    results = []

    def check(name, status, expected_status, body):
        passed = (status == expected_status) and body.get("success", False)
        symbol = "PASS" if passed else "FAIL"
        print(f"[{symbol}] {name} (HTTP {status})")
        if not passed:
            print(f"   Response Body: {json.dumps(body, indent=2)[:300]}")
        results.append((name, passed, status, body))
        return body

    # 1. Health Endpoint
    st, body = make_request(f"{BASE_URL}/health")
    check("GET /health", st, 200, body)

    # 2. Auth: Register Citizen User
    c_user = f"citizen_{random.randint(10000, 99999)}"
    st, body = make_request(f"{BASE_URL}/auth/register", method="POST", data={
        "username": c_user,
        "email": f"{c_user}@sih.gov.in",
        "password": "password123",
        "full_name": "Live Test Citizen",
        "role": "CITIZEN"
    })
    check("POST /auth/register (Citizen)", st, 201, body)
    c_token = body.get("access_token")
    c_headers = {"Authorization": f"Bearer {c_token}"} if c_token else {}

    # 3. Auth: Login Admin Account
    st, body = make_request(f"{BASE_URL}/auth/login", method="POST", data={
        "username_or_email": "admin",
        "password": "admin123"
    })
    check("POST /auth/login (Admin)", st, 200, body)
    admin_token = body.get("access_token")
    admin_headers = {"Authorization": f"Bearer {admin_token}"} if admin_token else {}

    # 4. Auth: Profile GET /auth/me
    st, body = make_request(f"{BASE_URL}/auth/me", headers=c_headers)
    check("GET /auth/me (Citizen Profile)", st, 200, body)

    # 5. Citizen Report: Submit
    st, body = make_request(f"{BASE_URL}/citizen-reports", method="POST", data={
        "title": "Suspicious Vehicle & Container Movement",
        "description": "Black SUV MH01AB1234 parked near warehouse with 3 suspects.",
        "location": "Warehouse Sector 4",
        "vehicle_details": "MH01AB1234 Black SUV"
    }, headers=c_headers)
    rep_body = check("POST /citizen-reports", st, 201, body)
    report_id = rep_body.get("report", {}).get("id")

    # 6. Citizen Report: My Reports
    st, body = make_request(f"{BASE_URL}/citizen-reports/my-reports", headers=c_headers)
    check("GET /citizen-reports/my-reports", st, 200, body)

    # 7. Citizen Report: Get by ID
    if report_id:
        st, body = make_request(f"{BASE_URL}/citizen-reports/{report_id}", headers=c_headers)
        check(f"GET /citizen-reports/{report_id}", st, 200, body)

    # 8. Admin: List Citizen Reports Queue
    st, body = make_request(f"{BASE_URL}/admin/reports", headers=admin_headers)
    check("GET /admin/reports (Admin Queue)", st, 200, body)

    # 9. Admin: Review and Approve Report
    if report_id:
        st, body = make_request(f"{BASE_URL}/admin/reports/{report_id}/review", method="POST", data={
            "action": "APPROVE",
            "notes": "Verified against local CCTV feed."
        }, headers=admin_headers)
        check(f"POST /admin/reports/{report_id}/review", st, 200, body)

    # 10. Admin: Users Management & Audit Logs
    st, body = make_request(f"{BASE_URL}/admin/users", headers=admin_headers)
    check("GET /admin/users", st, 200, body)

    st, body = make_request(f"{BASE_URL}/admin/audit-logs", headers=admin_headers)
    check("GET /admin/audit-logs", st, 200, body)

    # 11. Persons: List & Details
    st, body = make_request(f"{BASE_URL}/persons")
    check("GET /persons", st, 200, body)
    persons_data = body.get("data", [])
    test_p_id = persons_data[0]["id"] if persons_data else "P017"

    st, body = make_request(f"{BASE_URL}/persons/{test_p_id}")
    check(f"GET /persons/{test_p_id}", st, 200, body)

    st, body = make_request(f"{BASE_URL}/persons/{test_p_id}/network")
    check(f"GET /persons/{test_p_id}/network", st, 200, body)

    st, body = make_request(f"{BASE_URL}/persons/{test_p_id}/analytics")
    check(f"GET /persons/{test_p_id}/analytics", st, 200, body)

    # 12. Search Endpoint
    st, body = make_request(f"{BASE_URL}/search?q=Rahul")
    check("GET /search?q=Rahul", st, 200, body)

    # 13. Cases: List, Detail, and Ingestion
    st, body = make_request(f"{BASE_URL}/cases")
    check("GET /cases", st, 200, body)
    cases_data = body.get("data", [])
    test_case_id = cases_data[0]["id"] if cases_data else "C101"

    st, body = make_request(f"{BASE_URL}/cases/{test_case_id}")
    check(f"GET /cases/{test_case_id}", st, 200, body)

    st, body = make_request(f"{BASE_URL}/cases", method="POST", data={
        "title": "Live Hawala & Cyber Syndicate Case",
        "description": "Suspect Rahul Sharma (P017) transferred funds to ACC001 and used vehicle MH12CX9999.",
        "type": "CYBERCRIME"
    }, headers=admin_headers)
    check("POST /cases (Incremental Ingestion)", st, 201, body)

    # 14. Network Pathfinding & Analytics
    st, body = make_request(f"{BASE_URL}/network/path?source=P017&target=P024")
    check("GET /network/path", st, 200, body)

    st, body = make_request(f"{BASE_URL}/persons/{test_p_id}/priority")
    check(f"GET /persons/{test_p_id}/priority", st, 200, body)

    st, body = make_request(f"{BASE_URL}/communities")
    check("GET /communities", st, 200, body)

    st, body = make_request(f"{BASE_URL}/anomalies")
    check("GET /anomalies", st, 200, body)

    st, body = make_request(f"{BASE_URL}/entity-resolution/{test_p_id}")
    check(f"GET /entity-resolution/{test_p_id}", st, 200, body)

    # 15. NLP NER Extraction
    st, body = make_request(f"{BASE_URL}/nlp/extract", method="POST", data={
        "text": "Rahul Sharma and Ajay Kumar spotted in Bandra near vehicle MH01AB1234 calling 9876543210."
    })
    check("POST /nlp/extract", st, 200, body)

    # 16. Evidence Lookup
    st, body = make_request(f"{BASE_URL}/evidence/CDR-104")
    check("GET /evidence/CDR-104", st, 200, body)

    # 17. Dynamic AI Query (Vehicle Intent)
    st, body = make_request(f"{BASE_URL}/ai/query", method="POST", data={
        "question": "Who is driving vehicle MH01AB1234?"
    })
    check("POST /ai/query (Vehicle Intent)", st, 200, body)

    # 18. Dynamic AI Query (Financial Intent)
    st, body = make_request(f"{BASE_URL}/ai/query", method="POST", data={
        "question": "Show all wire transfers and hawala accounts for P017"
    })
    check("POST /ai/query (Financial Intent)", st, 200, body)

    # 19. Simulation: Remove Node
    st, body = make_request(f"{BASE_URL}/simulation/remove-node", method="POST", data={
        "entity_id": test_p_id
    })
    check("POST /simulation/remove-node", st, 200, body)

    print("=" * 70)
    passed_count = sum(1 for r in results if r[1])
    total_count = len(results)
    print(f"LIVE TEST RESULTS: {passed_count} / {total_count} ENDPOINTS PASSED PERFECTLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_live_tests()
