import io
import os
import sys
import datetime
import unittest
from fastapi.testclient import TestClient

from app.main import app
from app.auth import hash_password, verify_password, create_access_token
from app.config import settings
from app.database import SessionLocal
from app.models import User, Profile, Resume, Interview, Answer

class TestSecurityAndPrivacy(unittest.TestCase):
    """
    Phase 19 Test Suite: Security & Privacy Hardening Verification.
    Verifies password hashing, JWT expiration, user data isolation,
    file upload whitelist & 5MB size limit, input sanitization, audio privacy,
    and HTTP security headers.
    """

    def setUp(self):
        self.client = TestClient(app)
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_01_bcrypt_password_hashing(self):
        """Verify passwords are never stored plain text and bcrypt salt is unique."""
        plain = "MySecretPass_2026!"
        h1 = hash_password(plain)
        h2 = hash_password(plain)

        # Hashed format verification
        self.assertTrue(h1.startswith("$2b$") or h1.startswith("$2a$"))
        self.assertNotEqual(plain, h1)
        self.assertNotEqual(h1, h2, "Bcrypt must use unique salt for each hash")

        # Verification function tests
        self.assertTrue(verify_password(plain, h1))
        self.assertFalse(verify_password("WrongPassword!", h1))

    def test_02_jwt_expiration_and_tampering(self):
        """Verify expired and tampered JWT tokens are rejected with 401."""
        user_id = 9999

        # Expired token (expired 5 minutes ago)
        expired_token = create_access_token(
            data={"sub": str(user_id)},
            expires_delta=datetime.timedelta(minutes=-5)
        )
        res_exp = self.client.get("/api/profile", headers={"Authorization": f"Bearer {expired_token}"})
        self.assertEqual(res_exp.status_code, 401)
        self.assertIn("Could not validate credentials", res_exp.json()["detail"])

        # Tampered token (invalid signature)
        tampered_token = expired_token[:-4] + "abcd"
        res_tamp = self.client.get("/api/profile", headers={"Authorization": f"Bearer {tampered_token}"})
        self.assertEqual(res_tamp.status_code, 401)

    def test_03_protected_endpoints_require_jwt(self):
        """Verify all core endpoints block unauthenticated access with 401."""
        endpoints = [
            ("GET", "/api/profile"),
            ("PUT", "/api/profile"),
            ("GET", "/api/resume-analysis"),
            ("POST", "/api/interview/start"),
            ("GET", "/api/interview/history"),
            ("GET", "/api/interview/1/results"),
        ]
        for method, ep in endpoints:
            if method == "GET":
                res = self.client.get(ep)
            elif method == "PUT":
                res = self.client.put(ep, json={})
            else:
                res = self.client.post(ep, json={})
            self.assertEqual(res.status_code, 401, f"Endpoint {ep} must require authentication")

    def test_04_user_data_isolation_and_cross_tenant_privacy(self):
        """Verify User A cannot access User B's profile, interview, or results."""
        # 1. Register User A
        u1_email = f"user_a_{os.urandom(3).hex()}@test.com"
        r1 = self.client.post("/api/auth/register", json={
            "name": "User A", "email": u1_email, "password": "Password123", "confirm_password": "Password123"
        })
        token_a = r1.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # User A creates interview
        sess_a = self.client.post("/api/interview/start", headers=headers_a, json={
            "target_role": "Backend Developer",
            "interview_type": "Technical",
            "difficulty": "Medium",
            "num_questions": 1
        })
        interview_a_id = sess_a.json()["id"]

        # 2. Register User B
        u2_email = f"user_b_{os.urandom(3).hex()}@test.com"
        r2 = self.client.post("/api/auth/register", json={
            "name": "User B", "email": u2_email, "password": "Password123", "confirm_password": "Password123"
        })
        token_b = r2.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # 3. User B attempts to access User A's interview
        cross_res = self.client.get(f"/api/interview/{interview_a_id}", headers=headers_b)
        self.assertEqual(cross_res.status_code, 404, "User B must not access User A's interview")

        # 4. User B attempts to submit answer to User A's interview
        cross_submit = self.client.post(f"/api/interview/{interview_a_id}/submit-answer", headers=headers_b, json={
            "transcript": "Hacking session"
        })
        self.assertEqual(cross_submit.status_code, 404)

        # 5. User B attempts to access User A's results
        cross_results = self.client.get(f"/api/interview/{interview_a_id}/results", headers=headers_b)
        self.assertEqual(cross_results.status_code, 404)

    def test_05_file_upload_whitelist_and_5mb_limit(self):
        """Verify upload type whitelist (.pdf, .docx only) and strict 5MB size limit."""
        # Register user
        reg = self.client.post("/api/auth/register", json={
            "name": "Upload Tester", "email": f"uploader_{os.urandom(3).hex()}@test.com",
            "password": "Password123", "confirm_password": "Password123"
        })
        headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

        # 1. Unsupported extensions rejected
        for bad_ext in ["evil.exe", "script.sh", "notes.txt", "page.html", "payload.py"]:
            res = self.client.post(
                "/api/resume/upload",
                headers=headers,
                files={"file": (bad_ext, b"Fake content", "application/octet-stream")}
            )
            self.assertEqual(res.status_code, 400)
            self.assertIn("Unsupported file format", res.json()["detail"])

        # 2. Exceeding 5MB rejected
        oversized_content = b"0" * (5 * 1024 * 1024 + 100)  # > 5MB
        res_oversized = self.client.post(
            "/api/resume/upload",
            headers=headers,
            files={"file": ("large_resume.pdf", oversized_content, "application/pdf")}
        )
        self.assertEqual(res_oversized.status_code, 400)
        self.assertIn("5 MB", res_oversized.json()["detail"])

    def test_06_input_sanitization_xss_protection(self):
        """Verify malicious HTML / script tags are stripped from candidate profile & answer inputs."""
        reg = self.client.post("/api/auth/register", json={
            "name": "XSS Tester", "email": f"xss_{os.urandom(3).hex()}@test.com",
            "password": "Password123", "confirm_password": "Password123"
        })
        headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

        # Profile update with XSS payload
        xss_payload = "<script>alert('XSS Attack')</script>Senior Engineer"
        prof_res = self.client.put("/api/profile", headers=headers, json={
            "target_role": xss_payload,
            "skills": "<b>Python</b>, <img src=x onerror=alert(1)>SQL"
        })
        self.assertEqual(prof_res.status_code, 200)
        data = prof_res.json()
        self.assertNotIn("<script>", data["target_role"])
        self.assertNotIn("<img", data["skills"])
        self.assertEqual(data["target_role"], "Senior Engineer")

    def test_07_audio_privacy_purge(self):
        """Verify audio recordings can be purged while retaining transcripts for candidate privacy."""
        reg = self.client.post("/api/auth/register", json={
            "name": "Audio Privacy Tester", "email": f"audio_priv_{os.urandom(3).hex()}@test.com",
            "password": "Password123", "confirm_password": "Password123"
        })
        headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

        # Start interview
        sess = self.client.post("/api/interview/start", headers=headers, json={
            "target_role": "Backend Developer", "interview_type": "Technical",
            "difficulty": "Easy", "num_questions": 1
        })
        interview_id = sess.json()["id"]

        # Fetch current question
        self.client.get(f"/api/interview/{interview_id}/current-question", headers=headers)

        # Upload audio recording
        dummy_wav = io.BytesIO(b"RIFF....WAVEfmt ....data....")
        sub_res = self.client.post(
            f"/api/interview/{interview_id}/submit-audio",
            headers=headers,
            files={"file": ("recording.wav", dummy_wav, "audio/wav")},
            data={"transcript": "Candidate response explaining REST APIs", "duration_seconds": 12}
        )
        self.assertEqual(sub_res.status_code, 201)
        answer_data = sub_res.json()
        self.assertIsNotNone(answer_data.get("audio_path"))
        audio_file_path = answer_data["audio_path"]
        self.assertTrue(os.path.exists(audio_file_path))

        # Purge audio via DELETE /api/interview/{id}/audio
        purge_res = self.client.delete(f"/api/interview/{interview_id}/audio", headers=headers)
        self.assertEqual(purge_res.status_code, 200)
        self.assertGreaterEqual(purge_res.json()["purged_count"], 1)

        # Verify physical audio file is deleted from server disk
        self.assertFalse(os.path.exists(audio_file_path))

        # Verify text transcript is retained
        ans_verify = self.client.get(f"/api/interview/{interview_id}/answer/{answer_data['id']}", headers=headers)
        self.assertEqual(ans_verify.status_code, 200)
        self.assertEqual(ans_verify.json()["transcript"], "Candidate response explaining REST APIs")

    def test_08_security_headers_present(self):
        """Verify HTTPS-ready security headers are injected into HTTP responses."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        headers = res.headers
        self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(headers.get("X-XSS-Protection"), "1; mode=block")
        self.assertEqual(headers.get("Referrer-Policy"), "strict-origin-when-cross-origin")
        self.assertIn("microphone=(self)", headers.get("Permissions-Policy", ""))


if __name__ == "__main__":
    unittest.main()
