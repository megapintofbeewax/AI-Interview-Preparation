import sys
import os
import io
import unittest
from fastapi.testclient import TestClient
from docx import Document

from app.main import app

def create_sample_docx() -> io.BytesIO:
    doc = Document()
    doc.add_heading("Alex Candidate", 0)
    doc.add_heading("Education", level=1)
    doc.add_paragraph("B.S. in Computer Science - 2024")
    doc.add_heading("Technical Skills", level=1)
    doc.add_paragraph("Python, FastAPI, SQL, Docker, PostgreSQL, Redis")
    doc.add_heading("Key Projects", level=1)
    doc.add_paragraph("Cloud Microservices: Scalable distributed backend built with Python and FastAPI.")
    doc.add_heading("Work Experience", level=1)
    doc.add_paragraph("Backend Developer Intern at Cloud Systems (6 months).")
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

class TestCandidateNavigationJourney(unittest.TestCase):
    """
    Phase 18 Comprehensive Automated Test Suite.
    Validates the entire end-to-end linear candidate flow:
    Register -> Profile -> Resume Upload -> Resume Analysis ->
    Interview Setup -> Live Interview Question -> Speech/STT Answer Submission ->
    Answer Verification -> Evaluation -> Advance to Completion ->
    Interview Results -> Feedback -> Recommendations -> History -> Logout.
    """

    def setUp(self):
        self.client = TestClient(app)
        self.email = f"journey_{os.urandom(4).hex()}@example.com"
        self.password = "SecurePass123"

    def test_complete_linear_candidate_journey(self):
        # 1. Register candidate
        reg_res = self.client.post("/api/auth/register", json={
            "name": "Alex Candidate",
            "email": self.email,
            "password": self.password,
            "confirm_password": self.password
        })
        self.assertEqual(reg_res.status_code, 201)
        token = reg_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Candidate Profile Update
        prof_res = self.client.put("/api/profile", headers=headers, json={
            "name": "Alex Candidate",
            "education": "B.S. in Computer Science",
            "target_role": "Backend Developer",
            "target_difficulty": "Medium",
            "skills": "Python, FastAPI, SQL, Docker"
        })
        self.assertEqual(prof_res.status_code, 200)
        self.assertEqual(prof_res.json()["target_role"], "Backend Developer")

        # 3. Resume Upload (Valid DOCX)
        docx_buf = create_sample_docx()
        upload_res = self.client.post(
            "/api/resume/upload",
            headers=headers,
            files={"file": ("alex_resume.docx", docx_buf, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )
        self.assertEqual(upload_res.status_code, 201)
        resume_id = upload_res.json()["id"]

        # 4. Resume Analysis Extraction (Trigger & Fetch)
        analyze_trigger = self.client.post("/api/resume-analysis/analyze", headers=headers)
        self.assertEqual(analyze_trigger.status_code, 200)

        analysis_res = self.client.get("/api/resume-analysis", headers=headers)
        self.assertEqual(analysis_res.status_code, 200)
        analysis_data = analysis_res.json()
        self.assertIn("skills", analysis_data)

        # 5. Interview Setup
        setup_res = self.client.post("/api/interview/start", headers=headers, json={
            "target_role": "Backend Developer",
            "interview_type": "Technical",
            "difficulty": "Medium",
            "num_questions": 2,
            "resume_id": resume_id
        })
        self.assertEqual(setup_res.status_code, 201)
        interview_id = setup_res.json()["id"]

        # 6. Live Interview - Question 1
        q1_res = self.client.get(f"/api/interview/{interview_id}/current-question", headers=headers)
        self.assertEqual(q1_res.status_code, 200)
        q1_data = q1_res.json()
        self.assertEqual(q1_data["question_index"], 1)

        # 7. Candidate Speech/STT Answer Submission
        ans1_res = self.client.post(f"/api/interview/{interview_id}/submit-answer", headers=headers, json={
            "transcript": "In Python, decorators wrap functions to extend their behavior cleanly without modifying the core implementation.",
            "duration_seconds": 22
        })
        self.assertEqual(ans1_res.status_code, 201)
        ans1_id = ans1_res.json()["id"]

        # 8. Answer Verification & Correction
        edit_res = self.client.put(f"/api/interview/{interview_id}/answer/{ans1_id}", headers=headers, json={
            "transcript": "In Python, decorators wrap functions using higher-order functions to extend behavior without modifying original code."
        })
        self.assertEqual(edit_res.status_code, 200)

        # 9. AI Answer Evaluation
        eval1_res = self.client.post(f"/api/interview/{interview_id}/answer/{ans1_id}/evaluate", headers=headers)
        self.assertEqual(eval1_res.status_code, 200)
        eval1_data = eval1_res.json()
        self.assertIn("overall_score", eval1_data)

        # 10. Advance to Question 2
        adv1_res = self.client.post(f"/api/interview/{interview_id}/advance-question", headers=headers)
        self.assertEqual(adv1_res.status_code, 200)
        self.assertFalse(adv1_res.json()["completed"])

        # 11. Live Interview - Question 2
        q2_res = self.client.get(f"/api/interview/{interview_id}/current-question", headers=headers)
        self.assertEqual(q2_res.status_code, 200)

        # 12. Submit Answer 2
        ans2_res = self.client.post(f"/api/interview/{interview_id}/submit-answer", headers=headers, json={
            "transcript": "PostgreSQL indexing uses B-trees to drastically reduce query execution time from linear to logarithmic time complexity.",
            "duration_seconds": 25
        })
        ans2_id = ans2_res.json()["id"]
        eval2_res = self.client.post(f"/api/interview/{interview_id}/answer/{ans2_id}/evaluate", headers=headers)
        self.assertEqual(eval2_res.status_code, 200)

        # 13. Advance Session (Completes Interview)
        adv2_res = self.client.post(f"/api/interview/{interview_id}/advance-question", headers=headers)
        self.assertEqual(adv2_res.status_code, 200)
        self.assertTrue(adv2_res.json()["completed"])

        # 14. View Final Interview Results
        results_res = self.client.get(f"/api/interview/{interview_id}/results", headers=headers)
        self.assertEqual(results_res.status_code, 200)
        self.assertEqual(results_res.json()["status"], "completed")

        # 15. View Interview Feedback & Weaknesses
        fb_res = self.client.get(f"/api/interview/{interview_id}/feedback", headers=headers)
        self.assertEqual(fb_res.status_code, 200)

        # 16. View Personalized Practice Recommendations
        rec_res = self.client.get(f"/api/interview/{interview_id}/recommendations", headers=headers)
        self.assertEqual(rec_res.status_code, 200)

        # 17. View Interview History Archive
        hist_res = self.client.get("/api/interview/history", headers=headers)
        self.assertEqual(hist_res.status_code, 200)
        hist_data = hist_res.json()
        self.assertGreaterEqual(hist_data["total_interviews"], 1)

        print("[PASS] Full end-to-end candidate journey verified without any dead ends!")


if __name__ == "__main__":
    unittest.main()
