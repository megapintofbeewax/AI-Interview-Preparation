import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_speech_to_text_verification():
    print(">>> 1. Authenticating test user...")
    user_payload = {
        "name": "Transcription Candidate",
        "email": "transcribe.candidate@example.com",
        "password": "password123",
        "confirm_password": "password123"
    }
    resp = client.post("/api/auth/register", json=user_payload)
    if resp.status_code == 400:
        resp = client.post("/api/auth/login", json={"email": "transcribe.candidate@example.com", "password": "password123"})
    assert resp.status_code in [200, 201]
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] User authenticated")

    print("\n>>> 2. Creating interview session & question...")
    resp = client.post("/api/interview/start", json={
        "target_role": "Software Developer",
        "interview_type": "Technical",
        "difficulty": "Medium",
        "num_questions": 10
    }, headers=headers)
    assert resp.status_code == 201
    interview_id = resp.json()["id"]

    q_resp = client.get(f"/api/interview/{interview_id}/current-question", headers=headers)
    assert q_resp.status_code == 200
    question = q_resp.json()
    print("[PASS] Question ready:", question["question_text"])

    print("\n>>> 3. Submitting voice answer with speech-to-text transcript...")
    initial_text = "Flask is a Python web framework that I used to create the backend of my project."
    sub_resp = client.post(f"/api/interview/{interview_id}/submit-answer", json={
        "transcript": initial_text,
        "duration_seconds": 15
    }, headers=headers)
    assert sub_resp.status_code == 201
    answer_id = sub_resp.json()["id"]
    print(f"[PASS] Answer submitted with ID: {answer_id}")

    print("\n>>> 4. Testing GET /{interview_id}/answer/{answer_id} (Verification display)...")
    get_resp = client.get(f"/api/interview/{interview_id}/answer/{answer_id}", headers=headers)
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["transcript"] == initial_text
    assert data["question_text"] == question["question_text"]
    assert data["duration_seconds"] == 15
    print("[PASS] Transcribed answer retrieved cleanly with question text")

    print("\n>>> 5. Testing PUT /{interview_id}/answer/{answer_id} (Correction of transcript)...")
    corrected_text = "Flask is a lightweight Python web framework that I used to create the backend REST API of my project, integrating SQLAlchemy."
    put_resp = client.put(f"/api/interview/{interview_id}/answer/{answer_id}", json={
        "transcript": corrected_text
    }, headers=headers)
    assert put_resp.status_code == 200
    updated_data = put_resp.json()
    assert updated_data["transcript"] == corrected_text
    print("[PASS] Transcript updated successfully")

    print("\n>>> 6. Verifying persistence via GET...")
    verify_resp = client.get(f"/api/interview/{interview_id}/answer/{answer_id}", headers=headers)
    assert verify_resp.status_code == 200
    assert verify_resp.json()["transcript"] == corrected_text
    print("[PASS] Corrected transcript verified persistent")

    print("\n>>> 7. Testing unauthenticated access...")
    unauth_resp = client.get(f"/api/interview/{interview_id}/answer/{answer_id}")
    assert unauth_resp.status_code == 401
    print("[PASS] Unauthenticated access blocked correctly")

    print("\n=========================================")
    print("ALL SPEECH-TO-TEXT TESTS PASSED!")
    print("=========================================")

if __name__ == "__main__":
    test_speech_to_text_verification()
