import os
import sys
import uuid
from fastapi.testclient import TestClient

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.main import app

client = TestClient(app)

def run_history_tests():
    print("=========================================")
    print("PHASE 13: INTERVIEW HISTORY TEST SUITE")
    print("=========================================")

    # 1. Register test user
    print("\n>>> 1. Authenticating test user...")
    rand_email = f"history_{uuid.uuid4().hex[:8]}@example.com"
    reg_resp = client.post("/api/auth/register", json={
        "name": "History Candidate",
        "email": rand_email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] User registered and authenticated")

    # 2. Check Empty State
    print("\n>>> 2. Verifying Initial Empty History State...")
    empty_resp = client.get("/api/interview/history", headers=headers)
    assert empty_resp.status_code == 200
    empty_data = empty_resp.json()
    assert empty_data["total_interviews"] == 0
    assert len(empty_data["interviews"]) == 0
    print("[PASS] Empty history state confirmed")

    # 3. Create & Complete Interview 1 (Software Developer, Medium)
    print("\n>>> 3. Completing Interview 1 (Software Developer, Medium)...")
    s1_resp = client.post("/api/interview/start", headers=headers, json={
        "target_role": "Software Developer",
        "interview_type": "Technical",
        "difficulty": "Medium",
        "num_questions": 1
    })
    assert s1_resp.status_code == 201
    id1 = s1_resp.json()["id"]

    client.get(f"/api/interview/{id1}/current-question", headers=headers)
    ans1 = client.post(f"/api/interview/{id1}/submit-answer", headers=headers, json={
        "transcript": "In Python I created microservices and REST APIs with Flask and database tables.",
        "duration_seconds": 20
    })
    client.post(f"/api/interview/{id1}/answer/{ans1.json()['id']}/evaluate", headers=headers)
    client.get(f"/api/interview/{id1}/results", headers=headers)
    print(f"[PASS] Interview 1 completed (ID: {id1})")

    # 4. Create & Complete Interview 2 (Data Analyst, Easy)
    print("\n>>> 4. Completing Interview 2 (Data Analyst, Easy)...")
    s2_resp = client.post("/api/interview/start", headers=headers, json={
        "target_role": "Data Analyst",
        "interview_type": "Mixed",
        "difficulty": "Easy",
        "num_questions": 1
    })
    assert s2_resp.status_code == 201
    id2 = s2_resp.json()["id"]

    client.get(f"/api/interview/{id2}/current-question", headers=headers)
    ans2 = client.post(f"/api/interview/{id2}/submit-answer", headers=headers, json={
        "transcript": "I analyzed datasets with SQL aggregations and Python pandas.",
        "duration_seconds": 18
    })
    client.post(f"/api/interview/{id2}/answer/{ans2.json()['id']}/evaluate", headers=headers)
    client.get(f"/api/interview/{id2}/results", headers=headers)
    print(f"[PASS] Interview 2 completed (ID: {id2})")

    # 5. Retrieve Interview History
    print("\n>>> 5. Fetching Interview History (GET /api/interview/history)...")
    hist_resp = client.get("/api/interview/history", headers=headers)
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()

    print(f"[PASS] Total Interviews: {hist_data['total_interviews']}")
    print(f"[PASS] Average Score:    {hist_data['average_score']}")
    assert hist_data["total_interviews"] == 2
    assert len(hist_data["interviews"]) == 2

    # Verify chronological ordering (Interview 2 is newest)
    item_latest = hist_data["interviews"][0]
    item_older = hist_data["interviews"][1]

    print(f"\n[PASS] Most Recent Session:")
    print(f"       Role:       {item_latest['target_role']}")
    print(f"       Type:       {item_latest['interview_type']} • {item_latest['difficulty']}")
    print(f"       Score:      {item_latest['overall_score']}/100")
    print(f"       Status:     {item_latest['status']}")
    print(f"       Date:       {item_latest['created_at']}")

    assert item_latest["target_role"] == "Data Analyst"
    assert item_latest["overall_score"] is not None
    assert item_latest["status"] == "completed"

    assert item_older["target_role"] == "Software Developer"
    assert item_older["overall_score"] is not None
    assert item_older["status"] == "completed"

    # 6. Test Security & Isolation
    print("\n>>> 6. Testing Security & User Data Isolation...")
    # Unauthenticated
    unauth = client.get("/api/interview/history")
    assert unauth.status_code == 401
    print("[PASS] Unauthenticated history blocked (401)")

    # Different user sees 0 interviews
    diff_email = f"other_{uuid.uuid4().hex[:8]}@example.com"
    diff_reg = client.post("/api/auth/register", json={
        "name": "Different User",
        "email": diff_email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    diff_token = diff_reg.json()["access_token"]
    diff_hist = client.get("/api/interview/history", headers={"Authorization": f"Bearer {diff_token}"})
    assert diff_hist.status_code == 200
    assert diff_hist.json()["total_interviews"] == 0
    print("[PASS] User data isolation verified (Other user sees 0 interviews)")

    print("\n=========================================")
    print("ALL INTERVIEW HISTORY TESTS PASSED!")
    print("=========================================")

if __name__ == "__main__":
    run_history_tests()
