import os
import sys
import uuid
from fastapi.testclient import TestClient

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.main import app
from app.services.question_generator import generate_interview_question

client = TestClient(app)

def run_adaptive_questioning_tests():
    print("=========================================")
    print("PHASE 9: ADAPTIVE QUESTIONING TEST SUITE")
    print("=========================================")

    # Test 1: Direct Unit Test of generate_interview_question with High Score (>= 8.0)
    print("\n>>> 1. Unit Test: Adaptive Question Escalation on High Score (>= 8.0)...")
    history_high = [
        {
            "question_index": 1,
            "question_text": "Explain how you used Python in your project and what core concepts you applied.",
            "difficulty": "Medium",
            "category": "Technical",
            "transcript": "In our project we built a microservice with Python and Flask with database routing and REST APIs.",
            "overall_score": 8.8,
            "feedback": "Your answer correctly explains Python and its purpose."
        }
    ]
    q_high = generate_interview_question(
        interview_type="Technical",
        difficulty="Medium",
        target_role="Backend Developer",
        question_index=2,
        total_questions=5,
        skills=["Python", "SQL", "Docker"],
        projects=["Cloud Service"],
        asked_questions=["Explain how you used Python in your project and what core concepts you applied."],
        history=history_high
    )

    assert q_high["is_adaptive"] is True, "Question should be marked as adaptive"
    assert q_high["difficulty"] == "Hard", f"Difficulty should have adapted from Medium to Hard, got {q_high['difficulty']}"
    assert "increased" in q_high["adaptive_reason"].lower(), f"Reason should mention increase, got {q_high['adaptive_reason']}"
    print(f"[PASS] Adapted to Hard: '{q_high['question_text']}'")
    print(f"       Reason: {q_high['adaptive_reason']}")

    # Test 2: Direct Unit Test with Low Score (< 6.0)
    print("\n>>> 2. Unit Test: Adaptive Clarifying Follow-Up on Low Score (< 6.0)...")
    history_low = [
        {
            "question_index": 1,
            "question_text": "Explain the internal concurrency and threading model of Python.",
            "difficulty": "Hard",
            "category": "Technical",
            "transcript": "I am not sure, it runs code line by line.",
            "overall_score": 4.2,
            "feedback": "Your response was brief and lacked key technical depth."
        }
    ]
    q_low = generate_interview_question(
        interview_type="Technical",
        difficulty="Hard",
        target_role="Backend Developer",
        question_index=2,
        total_questions=5,
        skills=["Python", "SQL", "Docker"],
        projects=["Cloud Service"],
        asked_questions=["Explain the internal concurrency and threading model of Python."],
        history=history_low
    )

    assert q_low["is_adaptive"] is True, "Question should be marked as adaptive"
    assert q_low["difficulty"] == "Medium", f"Difficulty should have decreased from Hard to Medium, got {q_low['difficulty']}"
    assert "clarifying" in q_low["adaptive_reason"].lower() or "adjusted" in q_low["adaptive_reason"].lower()
    print(f"[PASS] Adapted to Medium follow-up: '{q_low['question_text']}'")
    print(f"       Reason: {q_low['adaptive_reason']}")

    # Test 3: Direct Unit Test with Low Score from Medium -> Easy
    print("\n>>> 3. Unit Test: Downward Adaptation from Medium to Easy...")
    history_low_med = [
        {
            "question_index": 1,
            "question_text": "Explain how you used Python in your project.",
            "difficulty": "Medium",
            "category": "Technical",
            "transcript": "Just python.",
            "overall_score": 3.3,
            "feedback": "Your response was too brief."
        }
    ]
    q_easy = generate_interview_question(
        interview_type="Technical",
        difficulty="Medium",
        target_role="Backend Developer",
        question_index=2,
        total_questions=5,
        skills=["Python", "SQL"],
        projects=["App"],
        asked_questions=["Explain how you used Python in your project."],
        history=history_low_med
    )
    assert q_easy["difficulty"] == "Easy", f"Difficulty should have stepped down to Easy, got {q_easy['difficulty']}"
    print(f"[PASS] Adapted to Easy: '{q_easy['question_text']}'")

    # Test 4: End-to-End API Flow with Live Interview Session
    print("\n>>> 4. End-to-End API Flow: Registration & Login...")
    rand_email = f"adaptive_{uuid.uuid4().hex[:8]}@example.com"
    reg_resp = client.post("/api/auth/register", json={
        "name": "Adaptive Candidate",
        "email": rand_email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Setup Interview
    print(">>> Setting up new Easy interview session...")
    setup_resp = client.post("/api/interview/start", headers=headers, json={
        "target_role": "Backend Developer",
        "interview_type": "Technical",
        "difficulty": "Easy",
        "num_questions": 3
    })
    assert setup_resp.status_code == 201
    interview_id = setup_resp.json()["id"]

    # Question 1
    print(">>> Fetching Question 1 (Base Difficulty: Easy)...")
    q1_resp = client.get(f"/api/interview/{interview_id}/current-question", headers=headers)
    assert q1_resp.status_code == 200
    q1_data = q1_resp.json()
    assert q1_data["question_index"] == 1
    assert q1_data["difficulty"] == "Easy"
    assert q1_data["is_adaptive"] is False
    print(f"[PASS] Question 1 Ready: '{q1_data['question_text']}' ({q1_data['difficulty']})")

    # Submit Strong Answer for Question 1
    print(">>> Submitting strong candidate answer...")
    ans1_resp = client.post(f"/api/interview/{interview_id}/submit-answer", headers=headers, json={
        "transcript": "In my project I used Python and Flask to implement RESTful backend routing and API endpoints with database models.",
        "duration_seconds": 25
    })
    assert ans1_resp.status_code == 201
    ans1_id = ans1_resp.json()["id"]

    # Evaluate Answer 1
    print(">>> Evaluating Answer 1 with AI...")
    eval1_resp = client.post(f"/api/interview/{interview_id}/answer/{ans1_id}/evaluate", headers=headers)
    assert eval1_resp.status_code == 200
    eval1_data = eval1_resp.json()
    score1 = eval1_data["overall_score"]
    print(f"[PASS] Answer 1 Overall Score: {score1}/10")
    assert score1 >= 8.0, f"Expected strong score >= 8.0, got {score1}"

    # Advance to Question 2
    print(">>> Advancing to Question 2...")
    adv_resp = client.post(f"/api/interview/{interview_id}/advance-question", headers=headers)
    assert adv_resp.status_code == 200
    assert adv_resp.json()["current_question_index"] == 2

    # Fetch Question 2 (Should Adapt to Medium based on score1 >= 8.0)
    print(">>> Fetching Question 2 (Expecting Adaptive Difficulty: Medium)...")
    q2_resp = client.get(f"/api/interview/{interview_id}/current-question", headers=headers)
    assert q2_resp.status_code == 200
    q2_data = q2_resp.json()
    assert q2_data["question_index"] == 2
    assert q2_data["is_adaptive"] is True, "Question 2 must be adaptive"
    assert q2_data["difficulty"] == "Medium", f"Expected adapted difficulty Medium, got {q2_data['difficulty']}"
    print(f"[PASS] Question 2 Adaptively Upgraded to {q2_data['difficulty']}: '{q2_data['question_text']}'")
    print(f"       Reason: {q2_data['adaptive_reason']}")

    # Submit Weak Answer for Question 2
    print(">>> Submitting weak candidate answer for Question 2...")
    ans2_resp = client.post(f"/api/interview/{interview_id}/submit-answer", headers=headers, json={
        "transcript": "Not really sure.",
        "duration_seconds": 5
    })
    assert ans2_resp.status_code == 201
    ans2_id = ans2_resp.json()["id"]

    # Evaluate Answer 2
    print(">>> Evaluating Answer 2 with AI...")
    eval2_resp = client.post(f"/api/interview/{interview_id}/answer/{ans2_id}/evaluate", headers=headers)
    assert eval2_resp.status_code == 200
    eval2_data = eval2_resp.json()
    score2 = eval2_data["overall_score"]
    print(f"[PASS] Answer 2 Overall Score: {score2}/10")
    assert score2 < 6.0, f"Expected weak score < 6.0, got {score2}"

    # Advance to Question 3
    print(">>> Advancing to Question 3...")
    adv2_resp = client.post(f"/api/interview/{interview_id}/advance-question", headers=headers)
    assert adv2_resp.status_code == 200
    assert adv2_resp.json()["current_question_index"] == 3

    # Fetch Question 3 (Should Adapt down to Easy with Clarifying follow-up)
    print(">>> Fetching Question 3 (Expecting Adaptive Clarification down to Easy)...")
    q3_resp = client.get(f"/api/interview/{interview_id}/current-question", headers=headers)
    assert q3_resp.status_code == 200
    q3_data = q3_resp.json()
    assert q3_data["question_index"] == 3
    assert q3_data["is_adaptive"] is True
    assert q3_data["difficulty"] == "Easy", f"Expected adapted difficulty Easy, got {q3_data['difficulty']}"
    print(f"[PASS] Question 3 Adaptively Down-scoped to {q3_data['difficulty']}: '{q3_data['question_text']}'")
    print(f"       Reason: {q3_data['adaptive_reason']}")

    print("\n=========================================")
    print("ALL ADAPTIVE QUESTIONING TESTS PASSED!")
    print("=========================================")

if __name__ == "__main__":
    run_adaptive_questioning_tests()
