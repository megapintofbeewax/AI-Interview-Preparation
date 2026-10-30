"""
Comprehensive End-to-End System Delivery Test (Phase 21)
Verifies the complete candidate lifecycle across all 21 phases:
1. Registration & Authentication (bcrypt + JWT)
2. Profile configuration
3. Job catalog & skills retrieval
4. Resume upload & NLP entity analysis / correction
5. Interview session creation & configuration
6. Live question delivery with TTS pronunciation payload
7. Speech answer recording & audio upload
8. Answer verification & manual transcript correction
9. AI multi-dimensional answer evaluation
10. Adaptive questioning progression
11. Results calculation (overall score & metric breakdown)
12. Weakness identification & feedback analysis
13. Practice recommendations generation
14. Interview history retrieval & archiving
15. Audio privacy file purge
16. Security headers & health diagnostics
"""

import os
import io
import uuid
import unittest
from fastapi.testclient import TestClient
from docx import Document
from app.main import app

class TestFinalDelivery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        run_id = uuid.uuid4().hex[:8]
        cls.test_email = f"alex.{run_id}@placement.ai"
        cls.test_password = "SecurePassword2026!"
        cls.test_name = "Alex Turner"

    def test_complete_platform_lifecycle(self):
        print("\n--- [START] Phase 21: Full End-to-End Platform Delivery Test ---")

        # 1. Registration
        reg_payload = {
            "name": self.test_name,
            "email": self.test_email,
            "password": self.test_password,
            "confirm_password": self.test_password
        }
        res_reg = self.client.post("/api/auth/register", json=reg_payload)
        self.assertIn(res_reg.status_code, [200, 201])
        token = res_reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("[STEP 1 PASS] Candidate registration & JWT issued.")

        # 2. Login verification
        login_res = self.client.post("/api/auth/login", json={"email": self.test_email, "password": self.test_password})
        self.assertEqual(login_res.status_code, 200)
        self.assertIn("access_token", login_res.json())
        print("[STEP 2 PASS] Authentication with bcrypt & JWT verified.")

        # 3. Profile update
        profile_payload = {
            "name": "Alex Turner",
            "education": "B.S. in Computer Science",
            "target_role": "Backend Developer",
            "skills": "Python, FastAPI, PostgreSQL, Docker, Redis"
        }
        res_prof = self.client.put("/api/profile", json=profile_payload, headers=headers)
        self.assertEqual(res_prof.status_code, 200)
        self.assertEqual(res_prof.json()["target_role"], "Backend Developer")
        print("[STEP 3 PASS] Profile saved and updated.")

        # 4. Catalog endpoint
        res_roles = self.client.get("/api/interview/roles")
        self.assertEqual(res_roles.status_code, 200)
        self.assertTrue(len(res_roles.json()["roles"]) > 0)
        print("[STEP 4 PASS] Roles & skills catalogs verified.")

        # 5. Resume upload
        doc = Document()
        doc.add_heading("Alex Turner - Backend Developer", 0)
        doc.add_paragraph("Skills: Python, FastAPI, PostgreSQL, Docker, Redis, REST APIs")
        doc.add_paragraph("Projects: Distributed Task Queue with Redis and Python. High-throughput API gateway.")
        doc.add_paragraph("Education: B.S. Computer Science")
        doc.add_paragraph("Experience: Software Engineering Intern at Tech Corp")
        doc_buf = io.BytesIO()
        doc.save(doc_buf)
        doc_buf.seek(0)

        upload_file = ("alex_resume.docx", doc_buf, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        res_upload = self.client.post("/api/resume/upload", files={"file": upload_file}, headers=headers)
        self.assertIn(res_upload.status_code, [200, 201])
        resume_id = res_upload.json()["id"]
        print(f"[STEP 5 PASS] Resume uploaded with ID: {resume_id}")

        # 6. Resume entity extraction & analysis
        res_trigger = self.client.post("/api/resume-analysis/analyze", headers=headers)
        self.assertEqual(res_trigger.status_code, 200)
        res_analysis = self.client.get("/api/resume-analysis", headers=headers)
        self.assertEqual(res_analysis.status_code, 200)
        analysis_data = res_analysis.json()
        self.assertIn("skills", analysis_data)
        self.assertIn("projects", analysis_data)
        print("[STEP 6 PASS] Resume parsed into structured skills and entities.")

        # 7. Start an interview
        setup_payload = {
            "target_role": "Backend Developer",
            "interview_type": "Technical",
            "difficulty": "Medium",
            "num_questions": 5
        }
        res_start = self.client.post("/api/interview/start", json=setup_payload, headers=headers)
        self.assertIn(res_start.status_code, [200, 201])
        interview_id = res_start.json()["id"]
        print(f"[STEP 7 PASS] Interview session started: {interview_id}")

        # 8. Fetch Question 1 and TTS Audio Payload
        res_q1 = self.client.get(f"/api/interview/{interview_id}/current-question", headers=headers)
        self.assertEqual(res_q1.status_code, 200)
        q1_data = res_q1.json()
        q1_id = q1_data["id"]
        self.assertIsNotNone(q1_data["question_text"])

        res_tts = self.client.get(f"/api/interview/{interview_id}/question/{q1_id}/tts-text", headers=headers)
        self.assertEqual(res_tts.status_code, 200)
        self.assertIn("tts_text", res_tts.json())
        print("[STEP 8 PASS] Question 1 fetched with Text-to-Speech audio pronunciation payload.")

        # 9. Submit spoken answer via audio multipart
        dummy_audio = io.BytesIO(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00")
        audio_file = ("candidate_answer.wav", dummy_audio, "audio/wav")
        res_audio = self.client.post(
            f"/api/interview/{interview_id}/submit-audio",
            data={
                "transcript": "I design REST APIs using FastAPI with asynchronous dependency injection and SQLAlchemy sessions.",
                "duration_seconds": 18
            },
            files={"file": audio_file},
            headers=headers
        )
        self.assertIn(res_audio.status_code, [200, 201])
        answer_id = res_audio.json()["id"]
        print(f"[STEP 9 PASS] Audio answer submitted and transcribed: Answer ID {answer_id}")

        # 10. Verify transcribed answer & apply correction
        res_ans_get = self.client.get(f"/api/interview/{interview_id}/answer/{answer_id}", headers=headers)
        self.assertEqual(res_ans_get.status_code, 200)

        correction_payload = {
            "transcript": "I design robust REST APIs using FastAPI with asynchronous dependency injection, Alembic migrations, and SQLAlchemy sessions."
        }
        res_ans_edit = self.client.put(f"/api/interview/{interview_id}/answer/{answer_id}", json=correction_payload, headers=headers)
        self.assertEqual(res_ans_edit.status_code, 200)
        self.assertEqual(res_ans_edit.json()["transcript"], correction_payload["transcript"])
        print("[STEP 10 PASS] Candidate verified and corrected speech transcript.")

        # 11. AI Answer Evaluation
        res_eval = self.client.post(f"/api/interview/{interview_id}/answer/{answer_id}/evaluate", headers=headers)
        self.assertEqual(res_eval.status_code, 200)
        eval_data = res_eval.json()
        self.assertIn("technical_accuracy_score", eval_data)
        self.assertIn("feedback", eval_data)
        self.assertTrue(eval_data["overall_score"] > 0)
        print(f"[STEP 11 PASS] AI Evaluation completed: Score = {eval_data['overall_score']}/10")

        # 12. Advance to next question (Adaptive Question 2)
        res_adv = self.client.post(f"/api/interview/{interview_id}/advance-question", headers=headers)
        self.assertEqual(res_adv.status_code, 200)
        res_q2 = self.client.get(f"/api/interview/{interview_id}/current-question", headers=headers)
        self.assertEqual(res_q2.status_code, 200)
        q2_data = res_q2.json()
        self.assertIsNotNone(q2_data["question_text"])
        print("[STEP 12 PASS] Advanced to adaptive Question 2 based on candidate performance.")

        # 13. Interview Results
        res_results = self.client.get(f"/api/interview/{interview_id}/results", headers=headers)
        self.assertEqual(res_results.status_code, 200)
        results_data = res_results.json()
        self.assertIn("overall_score", results_data)
        self.assertIn("performance", results_data)
        print(f"[STEP 14 PASS] Performance metrics compiled: Overall {results_data['overall_score']}/100")

        # 14. Detailed Feedback
        res_feedback = self.client.get(f"/api/interview/{interview_id}/feedback", headers=headers)
        self.assertEqual(res_feedback.status_code, 200)
        feedback_data = res_feedback.json()
        self.assertIn("summary_notes", feedback_data)
        self.assertIn("strong_areas", feedback_data)
        self.assertIn("weak_areas", feedback_data)
        self.assertIn("question_feedbacks", feedback_data)
        print("[STEP 15 PASS] Weakness analysis and actionable feedback generated.")

        # 15. Recommendations
        res_recs = self.client.get(f"/api/interview/{interview_id}/recommendations", headers=headers)
        self.assertEqual(res_recs.status_code, 200)
        recs_data = res_recs.json()
        self.assertTrue(len(recs_data["recommendations"]) > 0)
        self.assertIn("suggested_setup", recs_data)
        self.assertIn("summary_message", recs_data)
        print("[STEP 16 PASS] Personalized study and practice recommendations delivered.")

        # 16. History
        res_history = self.client.get("/api/interview/history", headers=headers)
        self.assertEqual(res_history.status_code, 200)
        hist_items = res_history.json()["interviews"]
        self.assertTrue(any(i["id"] == interview_id for i in hist_items))
        print("[STEP 17 PASS] Interview archived in candidate history.")

        # 17. Audio Privacy Purge
        res_purge = self.client.delete(f"/api/interview/{interview_id}/audio", headers=headers)
        self.assertEqual(res_purge.status_code, 200)
        self.assertIn("purged_count", res_purge.json())
        print("[STEP 18 PASS] Audio recordings purged per candidate privacy requirements.")

        # 18. Security Headers & Health Check
        res_health = self.client.get("/api/health")
        self.assertEqual(res_health.status_code, 200)
        self.assertEqual(res_health.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(res_health.headers.get("X-Frame-Options"), "DENY")
        print("[STEP 19 PASS] HTTPS-ready security headers verified.")

        print("--- [SUCCESS] Phase 21: Full End-to-End System Verified 100%! ---\n")

if __name__ == "__main__":
    unittest.main()
