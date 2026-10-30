import os
import sys
import uuid
from fastapi.testclient import TestClient

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.main import app

client = TestClient(app)

def run_recommendations_tests():
    print("==============================================")
    print("PHASE 12: PRACTICE RECOMMENDATIONS TEST SUITE")
    print("==============================================")

    # 1. Register test user
    print("\n>>> 1. Authenticating test user...")
    rand_email = f"recommend_{uuid.uuid4().hex[:8]}@example.com"
    reg_resp = client.post("/api/auth/register", json={
        "name": "Practice Candidate",
        "email": rand_email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] User registered and authenticated")

    # 2. Setup interview session
    print("\n>>> 2. Initializing interview session (2 questions)...")
    setup_resp = client.post("/api/interview/start", headers=headers, json={
        "target_role": "Backend Engineer",
        "interview_type": "Technical",
        "difficulty": "Medium",
        "num_questions": 2
    })
    assert setup_resp.status_code == 201
    interview_id = setup_resp.json()["id"]

    # Question 1: Weak answer on Database / SQL
    client.get(f"/api/interview/{interview_id}/current-question", headers=headers)
    ans1_resp = client.post(f"/api/interview/{interview_id}/submit-answer", headers=headers, json={
        "transcript": "Not really sure about sql queries or database normalization.",
        "duration_seconds": 6
    })
    ans1_id = ans1_resp.json()["id"]
    client.post(f"/api/interview/{interview_id}/answer/{ans1_id}/evaluate", headers=headers)
    client.post(f"/api/interview/{interview_id}/advance-question", headers=headers)

    # Question 2: Weak answer on Scaling
    client.get(f"/api/interview/{interview_id}/current-question", headers=headers)
    ans2_resp = client.post(f"/api/interview/{interview_id}/submit-answer", headers=headers, json={
        "transcript": "I have not worked on distributed system design or caching.",
        "duration_seconds": 5
    })
    ans2_id = ans2_resp.json()["id"]
    client.post(f"/api/interview/{interview_id}/answer/{ans2_id}/evaluate", headers=headers)
    client.post(f"/api/interview/{interview_id}/advance-question", headers=headers)

    # 3. Retrieve Personalized Recommendations
    print("\n>>> 3. Fetching Practice Recommendations (GET /{id}/recommendations)...")
    rec_resp = client.get(f"/api/interview/{interview_id}/recommendations", headers=headers)
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()

    print(f"[PASS] Summary: {rec_data['summary_message']}")
    print(f"[PASS] Suggested Setup: {rec_data['suggested_setup']}")
    print("\n[PASS] Generated Recommendations:")
    for item in rec_data["recommendations"]:
        print(f"       {item['step_number']}. {item['title']} - {item['description']}")

    assert rec_data["interview_id"] == interview_id
    assert len(rec_data["recommendations"]) >= 3
    rec_titles = " ".join([r["title"].lower() for r in rec_data["recommendations"]])
    assert "sql" in rec_titles or "database" in rec_titles or "architecture" in rec_titles
    assert rec_data["suggested_setup"]["difficulty"] in ["Easy", "Medium", "Hard"]

    # 4. Security & Unauthorized Access
    print("\n>>> 4. Testing Security...")
    unauth = client.get(f"/api/interview/{interview_id}/recommendations")
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
    cross = client.get(f"/api/interview/{interview_id}/recommendations", headers={"Authorization": f"Bearer {diff_token}"})
    assert cross.status_code == 404
    print("[PASS] Cross-user access blocked (404)")

    print("\n==============================================")
    print("ALL RECOMMENDATIONS TESTS PASSED!")
    print("==============================================")

if __name__ == "__main__":
    run_recommendations_tests()
