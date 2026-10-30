import os
import sys
import uuid
from fastapi.testclient import TestClient

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.main import app

client = TestClient(app)

def run_interview_results_tests():
    print("=========================================")
    print("PHASE 10: INTERVIEW RESULTS TEST SUITE")
    print("=========================================")

    # 1. Register test user
    print("\n>>> 1. Authenticating test user...")
    rand_email = f"results_{uuid.uuid4().hex[:8]}@example.com"
    reg_resp = client.post("/api/auth/register", json={
        "name": "Results Candidate",
        "email": rand_email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] User registered and authenticated")

    # 2. Setup interview session
    print("\n>>> 2. Initializing interview session (3 questions)...")
    setup_resp = client.post("/api/interview/start", headers=headers, json={
        "target_role": "Full Stack Developer",
        "interview_type": "Technical",
        "difficulty": "Medium",
        "num_questions": 3
    })
    assert setup_resp.status_code == 201
    interview_id = setup_resp.json()["id"]
    print(f"[PASS] Interview session created with ID: {interview_id}")

    # 3. Answer & Evaluate Question 1
    print("\n>>> 3. Fetching, answering, and evaluating Question 1...")
    q1_resp = client.get(f"/api/interview/{interview_id}/current-question", headers=headers)
    assert q1_resp.status_code == 200
    q1_id = q1_resp.json()["id"]

    sub1_resp = client.post(f"/api/interview/{interview_id}/submit-answer", headers=headers, json={
        "transcript": "I built backend services using Python and Flask with database connection and REST APIs to serve client data.",
        "duration_seconds": 22
    })
    assert sub1_resp.status_code == 201
    ans1_id = sub1_resp.json()["id"]

    eval1_resp = client.post(f"/api/interview/{interview_id}/answer/{ans1_id}/evaluate", headers=headers)
    assert eval1_resp.status_code == 200
    score1 = eval1_resp.json()["overall_score"]
    print(f"[PASS] Question 1 evaluated: {score1}/10")

    # Advance to Question 2
    adv1 = client.post(f"/api/interview/{interview_id}/advance-question", headers=headers)
    assert adv1.status_code == 200

    # 4. Answer & Evaluate Question 2
    print("\n>>> 4. Fetching, answering, and evaluating Question 2...")
    q2_resp = client.get(f"/api/interview/{interview_id}/current-question", headers=headers)
    assert q2_resp.status_code == 200

    sub2_resp = client.post(f"/api/interview/{interview_id}/submit-answer", headers=headers, json={
        "transcript": "For database queries I used SQL and relational models to optimize data fetching and maintain consistent state across requests.",
        "duration_seconds": 26
    })
    assert sub2_resp.status_code == 201
    ans2_id = sub2_resp.json()["id"]

    eval2_resp = client.post(f"/api/interview/{interview_id}/answer/{ans2_id}/evaluate", headers=headers)
    assert eval2_resp.status_code == 200
    score2 = eval2_resp.json()["overall_score"]
    print(f"[PASS] Question 2 evaluated: {score2}/10")

    # Complete Interview
    client.post(f"/api/interview/{interview_id}/advance-question", headers=headers)

    # 5. Retrieve Interview Results
    print("\n>>> 5. Fetching Interview Results (GET /{id}/results)...")
    res_resp = client.get(f"/api/interview/{interview_id}/results", headers=headers)
    assert res_resp.status_code == 200
    data = res_resp.json()

    print(f"[PASS] Overall Score: {data['overall_score']} / 100")
    print(f"[PASS] Performance Breakdown:")
    print(f"       Technical Accuracy: {data['performance']['technical_accuracy']}/10")
    print(f"       Relevance:          {data['performance']['relevance']}/10")
    print(f"       Completeness:       {data['performance']['completeness']}/10")
    print(f"       Clarity:            {data['performance']['clarity']}/10")
    print(f"[PASS] Questions Answered: {data['questions_answered']} / {data['total_questions']}")
    print(f"[PASS] Status: {data['status']}")

    assert data["interview_id"] == interview_id
    assert data["target_role"] == "Full Stack Developer"
    assert data["interview_type"] == "Technical"
    assert data["overall_score"] >= 70, f"Expected scaled score >= 70, got {data['overall_score']}"
    assert data["questions_answered"] == 2
    assert data["total_questions"] == 3
    assert data["status"] == "completed"
    assert len(data["questions"]) >= 2

    # 6. Verify security / unauthorized access
    print("\n>>> 6. Testing Unauthorized & Cross-user Security...")
    # Unauthenticated
    unauth_resp = client.get(f"/api/interview/{interview_id}/results")
    assert unauth_resp.status_code == 401
    print("[PASS] Unauthenticated access blocked (401)")

    # Different user
    diff_email = f"other_{uuid.uuid4().hex[:8]}@example.com"
    diff_reg = client.post("/api/auth/register", json={
        "name": "Other User",
        "email": diff_email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    diff_token = diff_reg.json()["access_token"]
    diff_headers = {"Authorization": f"Bearer {diff_token}"}

    cross_resp = client.get(f"/api/interview/{interview_id}/results", headers=diff_headers)
    assert cross_resp.status_code == 404
    print("[PASS] Cross-user access blocked (404)")

    print("\n=========================================")
    print("ALL INTERVIEW RESULTS TESTS PASSED!")
    print("=========================================")

if __name__ == "__main__":
    run_interview_results_tests()
