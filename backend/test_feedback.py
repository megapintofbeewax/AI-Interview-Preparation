import os
import sys
import uuid
from fastapi.testclient import TestClient

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.main import app

client = TestClient(app)

def run_feedback_tests():
    print("=========================================")
    print("PHASE 11: FEEDBACK & WEAKNESS TEST SUITE")
    print("=========================================")

    # 1. Register test user
    print("\n>>> 1. Authenticating test user...")
    rand_email = f"feedback_{uuid.uuid4().hex[:8]}@example.com"
    reg_resp = client.post("/api/auth/register", json={
        "name": "Feedback Candidate",
        "email": rand_email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] User registered and authenticated")

    # 2. Setup Interview 1
    print("\n>>> 2. Initializing Interview 1 (2 questions)...")
    setup1_resp = client.post("/api/interview/start", headers=headers, json={
        "target_role": "Backend Engineer",
        "interview_type": "Technical",
        "difficulty": "Medium",
        "num_questions": 2
    })
    assert setup1_resp.status_code == 201
    id1 = setup1_resp.json()["id"]

    # Question 1: Python (Strong)
    q1_resp = client.get(f"/api/interview/{id1}/current-question", headers=headers)
    assert q1_resp.status_code == 200

    ans1_resp = client.post(f"/api/interview/{id1}/submit-answer", headers=headers, json={
        "transcript": "I built backend services using Python and Flask with database connection and REST APIs to handle client routing.",
        "duration_seconds": 25
    })
    assert ans1_resp.status_code == 201
    ans1_id = ans1_resp.json()["id"]

    eval1_resp = client.post(f"/api/interview/{id1}/answer/{ans1_id}/evaluate", headers=headers)
    assert eval1_resp.status_code == 200
    score1 = eval1_resp.json()["overall_score"]
    assert score1 >= 8.0, f"Expected strong score >= 8.0, got {score1}"
    print(f"[PASS] Question 1 evaluated (Python): {score1}/10 (Strong)")

    # Advance to Question 2
    client.post(f"/api/interview/{id1}/advance-question", headers=headers)

    # Question 2: Weak answer on Database / SQL
    q2_resp = client.get(f"/api/interview/{id1}/current-question", headers=headers)
    assert q2_resp.status_code == 200

    ans2_resp = client.post(f"/api/interview/{id1}/submit-answer", headers=headers, json={
        "transcript": "Not really sure.",
        "duration_seconds": 4
    })
    assert ans2_resp.status_code == 201
    ans2_id = ans2_resp.json()["id"]

    eval2_resp = client.post(f"/api/interview/{id1}/answer/{ans2_id}/evaluate", headers=headers)
    assert eval2_resp.status_code == 200
    score2 = eval2_resp.json()["overall_score"]
    assert score2 < 6.0, f"Expected weak score < 6.0, got {score2}"
    print(f"[PASS] Question 2 evaluated (Weak): {score2}/10")

    # Complete Interview 1
    client.post(f"/api/interview/{id1}/advance-question", headers=headers)

    # 3. Retrieve Feedback for Interview 1
    print("\n>>> 3. Fetching Feedback for Interview 1 (GET /{id}/feedback)...")
    fb1_resp = client.get(f"/api/interview/{id1}/feedback", headers=headers)
    assert fb1_resp.status_code == 200
    fb1_data = fb1_resp.json()

    print(f"[PASS] Strong Areas: {fb1_data['strong_areas']}")
    print(f"[PASS] Weak Areas:   {fb1_data['weak_areas']}")
    print(f"[PASS] Summary:      {fb1_data['summary_notes']}")

    assert len(fb1_data["strong_areas"]) > 0
    assert len(fb1_data["weak_areas"]) > 0
    assert "Python" in fb1_data["strong_areas"] or any("API" in s for s in fb1_data["strong_areas"])
    assert len(fb1_data["question_feedbacks"]) == 2

    # 4. Setup Interview 2 to verify Recurring Weaknesses across sessions
    print("\n>>> 4. Starting Interview 2 to test Cross-Interview Recurring Weaknesses...")
    setup2_resp = client.post("/api/interview/start", headers=headers, json={
        "target_role": "Backend Engineer",
        "interview_type": "Technical",
        "difficulty": "Medium",
        "num_questions": 1
    })
    assert setup2_resp.status_code == 201
    id2 = setup2_resp.json()["id"]

    # Question in Interview 2: Weak answer again
    client.get(f"/api/interview/{id2}/current-question", headers=headers)
    ans3_resp = client.post(f"/api/interview/{id2}/submit-answer", headers=headers, json={
        "transcript": "I have not worked on database normalization or sql scaling.",
        "duration_seconds": 6
    })
    ans3_id = ans3_resp.json()["id"]
    client.post(f"/api/interview/{id2}/answer/{ans3_id}/evaluate", headers=headers)
    client.post(f"/api/interview/{id2}/advance-question", headers=headers)

    # Fetch Feedback for Interview 2
    print(">>> Fetching Feedback for Interview 2...")
    fb2_resp = client.get(f"/api/interview/{id2}/feedback", headers=headers)
    assert fb2_resp.status_code == 200
    fb2_data = fb2_resp.json()

    print(f"[PASS] Interview 2 Recurring Weaknesses: {fb2_data['recurring_weaknesses']}")
    assert len(fb2_data["recurring_weaknesses"]) > 0, "Expected recurring weakness detected across multiple interviews"
    rec = fb2_data["recurring_weaknesses"][0]
    assert rec["frequency"] >= 2
    print(f"[PASS] Recurring weakness detected: '{rec['topic']}' across {rec['frequency']} sessions")

    # 5. Security & Unauthorized Access
    print("\n>>> 5. Testing Security...")
    unauth = client.get(f"/api/interview/{id1}/feedback")
    assert unauth.status_code == 401
    print("[PASS] Unauthenticated access blocked (401)")

    diff_email = f"other_{uuid.uuid4().hex[:8]}@example.com"
    diff_reg = client.post("/api/auth/register", json={
        "name": "Other User",
        "email": diff_email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    diff_token = diff_reg.json()["access_token"]
    cross = client.get(f"/api/interview/{id1}/feedback", headers={"Authorization": f"Bearer {diff_token}"})
    assert cross.status_code == 404
    print("[PASS] Cross-user access blocked (404)")

    print("\n=========================================")
    print("ALL FEEDBACK TESTS PASSED!")
    print("=========================================")

if __name__ == "__main__":
    run_feedback_tests()
