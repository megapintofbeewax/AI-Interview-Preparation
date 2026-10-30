import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_interview_setup_flow():
    print(">>> 1. Authenticating test user...")
    user_payload = {
        "name": "Interview Setup Candidate",
        "email": "interview.candidate@example.com",
        "password": "password123",
        "confirm_password": "password123"
    }
    resp = client.post("/api/auth/register", json=user_payload)
    if resp.status_code == 400:
        resp = client.post("/api/auth/login", json={"email": "interview.candidate@example.com", "password": "password123"})
    assert resp.status_code in [200, 201]
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] User authenticated")

    print("\n>>> 2. Testing GET /api/interview/roles...")
    resp = client.get("/api/interview/roles")
    assert resp.status_code == 200
    roles = resp.json()["roles"]
    assert "Software Developer" in roles
    print("[PASS] Roles retrieved successfully:", len(roles), "roles found")

    print("\n>>> 3. Testing POST /api/interview/start (Technical, Medium, 10 questions)...")
    setup_payload = {
        "target_role": "Software Developer",
        "interview_type": "Technical",
        "difficulty": "Medium",
        "num_questions": 10
    }
    resp = client.post("/api/interview/start", json=setup_payload, headers=headers)
    assert resp.status_code == 201, f"Failed to start interview: {resp.text}"
    interview_data = resp.json()
    assert interview_data["target_role"] == "Software Developer"
    assert interview_data["interview_type"] == "Technical"
    assert interview_data["difficulty"] == "Medium"
    assert interview_data["num_questions"] == 10
    assert interview_data["status"] == "in_progress"
    interview_id = interview_data["id"]
    print("[PASS] Interview session created successfully with ID:", interview_id)

    print("\n>>> 4. Testing invalid interview type rejection...")
    bad_type_payload = {
        "target_role": "Software Developer",
        "interview_type": "InvalidType",
        "difficulty": "Medium",
        "num_questions": 10
    }
    resp = client.post("/api/interview/start", json=bad_type_payload, headers=headers)
    assert resp.status_code == 400
    print(f"[PASS] Invalid interview type rejected: {resp.json()['detail']}")

    print("\n>>> 5. Testing invalid difficulty rejection...")
    bad_diff_payload = {
        "target_role": "Software Developer",
        "interview_type": "Technical",
        "difficulty": "SuperHard",
        "num_questions": 10
    }
    resp = client.post("/api/interview/start", json=bad_diff_payload, headers=headers)
    assert resp.status_code == 400
    print(f"[PASS] Invalid difficulty rejected: {resp.json()['detail']}")

    print(f"\n>>> 6. Testing GET /api/interview/{interview_id}...")
    resp = client.get(f"/api/interview/{interview_id}", headers=headers)
    assert resp.status_code == 200
    fetched = resp.json()
    assert fetched["id"] == interview_id
    assert fetched["target_role"] == "Software Developer"
    print("[PASS] Interview details retrieved successfully")

    print("\n>>> 7. Testing unauthenticated access...")
    resp = client.post("/api/interview/start", json=setup_payload)
    assert resp.status_code == 401
    print("[PASS] Unauthenticated access blocked")

    print("\n=========================================")
    print("ALL INTERVIEW SETUP TESTS PASSED!")
    print("=========================================")

if __name__ == "__main__":
    test_interview_setup_flow()
