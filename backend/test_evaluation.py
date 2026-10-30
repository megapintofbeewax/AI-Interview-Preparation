import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_answer_evaluation_flow():
    print(">>> 1. Authenticating test user...")
    user_payload = {
        "name": "Eval Candidate",
        "email": "eval.candidate@example.com",
        "password": "password123",
        "confirm_password": "password123"
    }
    resp = client.post("/api/auth/register", json=user_payload)
    if resp.status_code == 400:
        resp = client.post("/api/auth/login", json={"email": "eval.candidate@example.com", "password": "password123"})
    assert resp.status_code in [200, 201]
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] User authenticated")

    print("\n>>> 2. Initializing interview & generating question...")
    resp = client.post("/api/interview/start", json={
        "target_role": "Software Developer",
        "interview_type": "Technical",
        "difficulty": "Medium",
        "num_questions": 5
    }, headers=headers)
    assert resp.status_code == 201
    interview_id = resp.json()["id"]

    q_resp = client.get(f"/api/interview/{interview_id}/current-question", headers=headers)
    assert q_resp.status_code == 200
    question = q_resp.json()
    print("[PASS] Question ready:", question["question_text"])

    print("\n>>> 3. Submitting candidate voice answer transcript...")
    answer_text = "Flask is a Python web framework that I used to create the backend of my project. It handled API routing, database requests, and server responses efficiently."
    sub_resp = client.post(f"/api/interview/{interview_id}/submit-answer", json={
        "transcript": answer_text,
        "duration_seconds": 16
    }, headers=headers)
    assert sub_resp.status_code == 201
    answer_id = sub_resp.json()["id"]
    print(f"[PASS] Answer submitted with ID: {answer_id}")

    print("\n>>> 4. Evaluating answer with AI (POST /{id}/answer/{aid}/evaluate)...")
    eval_resp = client.post(f"/api/interview/{interview_id}/answer/{answer_id}/evaluate", headers=headers)
    assert eval_resp.status_code == 200, f"Evaluation failed: {eval_resp.text}"
    evaluation = eval_resp.json()
    print("[PASS] Evaluation produced:")
    print(f"   Relevance:          {evaluation['relevance_score']}/10")
    print(f"   Technical Accuracy: {evaluation['technical_accuracy_score']}/10")
    print(f"   Completeness:       {evaluation['completeness_score']}/10")
    print(f"   Clarity:            {evaluation['clarity_score']}/10")
    print(f"   Overall Score:      {evaluation['overall_score']}/10")
    print(f"   Feedback:           {evaluation['feedback']}")

    assert evaluation["relevance_score"] >= 6
    assert evaluation["technical_accuracy_score"] >= 7
    assert evaluation["completeness_score"] >= 6
    assert evaluation["clarity_score"] >= 7
    assert evaluation["overall_score"] >= 6.5
    assert len(evaluation["feedback"]) > 20

    print("\n>>> 5. Fetching saved evaluation via GET...")
    get_eval = client.get(f"/api/interview/{interview_id}/answer/{answer_id}/evaluation", headers=headers)
    assert get_eval.status_code == 200
    assert get_eval.json()["overall_score"] == evaluation["overall_score"]
    print("[PASS] Evaluation persistence verified")

    print("\n>>> 6. Advancing to next question...")
    adv_resp = client.post(f"/api/interview/{interview_id}/advance-question", headers=headers)
    assert adv_resp.status_code == 200
    assert adv_resp.json()["current_question_index"] == 2
    print("[PASS] Advanced to question 2 successfully")

    print("\n>>> 7. Testing unauthenticated access...")
    unauth = client.post(f"/api/interview/{interview_id}/answer/{answer_id}/evaluate")
    assert unauth.status_code == 401
    print("[PASS] Unauthenticated evaluation blocked")

    print("\n=========================================")
    print("ALL EVALUATION TESTS PASSED!")
    print("=========================================")

if __name__ == "__main__":
    test_answer_evaluation_flow()
