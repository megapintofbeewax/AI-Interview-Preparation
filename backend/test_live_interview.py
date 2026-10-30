import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_live_interview_flow():
    print(">>> 1. Authenticating test user...")
    user_payload = {
        "name": "Live Candidate",
        "email": "live.candidate@example.com",
        "password": "password123",
        "confirm_password": "password123"
    }
    resp = client.post("/api/auth/register", json=user_payload)
    if resp.status_code == 400:
        resp = client.post("/api/auth/login", json={"email": "live.candidate@example.com", "password": "password123"})
    assert resp.status_code in [200, 201]
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] User authenticated")

    print("\n>>> 2. Initializing interview session...")
    setup_payload = {
        "target_role": "Software Developer",
        "interview_type": "Technical",
        "difficulty": "Medium",
        "num_questions": 10
    }
    resp = client.post("/api/interview/start", json=setup_payload, headers=headers)
    assert resp.status_code == 201
    interview = resp.json()
    interview_id = interview["id"]
    print(f"[PASS] Session created with ID: {interview_id}")

    print("\n>>> 3. Fetching current question (GET /api/interview/{id}/current-question)...")
    resp = client.get(f"/api/interview/{interview_id}/current-question", headers=headers)
    assert resp.status_code == 200, f"Failed to get current question: {resp.text}"
    q_data = resp.json()
    assert q_data["question_index"] == 1
    assert q_data["total_questions"] == 10
    assert len(q_data["question_text"]) > 10
    print("[PASS] Question 1 generated and retrieved:")
    print(f"   \"{q_data['question_text']}\"")

    print("\n>>> 4. Verifying question stability on repeated fetch...")
    resp_again = client.get(f"/api/interview/{interview_id}/current-question", headers=headers)
    assert resp_again.status_code == 200
    q_again = resp_again.json()
    assert q_again["id"] == q_data["id"]
    assert q_again["question_text"] == q_data["question_text"]
    print("[PASS] Question is stable and persisted in database")

    print("\n>>> 5. Submitting user answer transcript...")
    answer_payload = {
        "transcript": "Flask is a Python web framework that I used to create the backend of my project. It handled routing, database models, and API requests.",
        "duration_seconds": 18
    }
    resp = client.post(f"/api/interview/{interview_id}/submit-answer", json=answer_payload, headers=headers)
    assert resp.status_code == 201, f"Failed to submit answer: {resp.text}"
    ans_data = resp.json()
    assert ans_data["question_id"] == q_data["id"]
    assert ans_data["duration_seconds"] == 18
    assert "Flask is a Python web framework" in ans_data["transcript"]
    print("[PASS] Answer submitted and stored successfully")

    print("\n=========================================")
    print("ALL LIVE INTERVIEW TESTS PASSED!")
    print("=========================================")

if __name__ == "__main__":
    test_live_interview_flow()
