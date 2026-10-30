import os
import sys
import io
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

class SpeechFeaturesTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

        # Register User A
        reg_a = cls.client.post("/api/auth/register", json={
            "name": "Speech Candidate A",
            "email": "speech_candidate_a@example.com",
            "password": "SpeechPass123",
            "confirm_password": "SpeechPass123"
        })
        if reg_a.status_code == 400:
            reg_a = cls.client.post("/api/auth/login", json={
                "email": "speech_candidate_a@example.com",
                "password": "SpeechPass123"
            })
        cls.token_a = reg_a.json()["access_token"]
        cls.headers_a = {"Authorization": f"Bearer {cls.token_a}"}

        # Register User B (for cross-user isolation testing)
        reg_b = cls.client.post("/api/auth/register", json={
            "name": "Speech Candidate B",
            "email": "speech_candidate_b@example.com",
            "password": "SpeechPass123",
            "confirm_password": "SpeechPass123"
        })
        if reg_b.status_code == 400:
            reg_b = cls.client.post("/api/auth/login", json={
                "email": "speech_candidate_b@example.com",
                "password": "SpeechPass123"
            })
        cls.token_b = reg_b.json()["access_token"]
        cls.headers_b = {"Authorization": f"Bearer {cls.token_b}"}

        # Create interview session for User A
        res_i = cls.client.post("/api/interview/start", json={
            "target_role": "Backend Engineer",
            "interview_type": "Technical",
            "difficulty": "Medium",
            "num_questions": 5
        }, headers=cls.headers_a)
        cls.interview_id = res_i.json()["id"]

        # Fetch Question 1
        res_q = cls.client.get(f"/api/interview/{cls.interview_id}/current-question", headers=cls.headers_a)
        cls.question = res_q.json()
        cls.question_id = cls.question["id"]

    def test_01_text_to_speech_payload(self):
        """Verify Text-to-Speech endpoint delivers pronunciation-sanitized question payload."""
        res = self.client.get(
            f"/api/interview/{self.interview_id}/question/{self.question_id}/tts-text",
            headers=self.headers_a
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("tts_text", data)
        self.assertIn("lang", data)
        self.assertIn("rate", data)
        self.assertIn("pitch", data)
        self.assertEqual(data["question_id"], self.question_id)
        self.assertNotIn("`", data["tts_text"], "TTS text must strip formatting backticks for clean speech synthesis")
        print("[PASS] test_01_text_to_speech_payload: TTS pronunciation text endpoint verified.")

    def test_02_speech_to_text_transcript_submission(self):
        """Verify Speech-to-Text transcript submission with duration metadata."""
        transcript_text = "In my previous project, I designed a RESTful API using FastAPI and PostgreSQL, implementing JWT authentication."
        res = self.client.post(
            f"/api/interview/{self.interview_id}/submit-answer",
            json={
                "transcript": transcript_text,
                "duration_seconds": 22
            },
            headers=self.headers_a
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertIn("id", data)
        self.assertEqual(data["transcript"], transcript_text)
        self.assertEqual(data["duration_seconds"], 22)
        SpeechFeaturesTestCase.answer_id_transcript = data["id"]
        print("[PASS] test_02_speech_to_text_transcript_submission: STT transcript submitted and recorded.")

    def test_03_speech_to_text_audio_file_upload(self):
        """Verify Speech-to-Text multipart audio recording file upload."""
        dummy_audio = io.BytesIO(b"RIFFdummy_webm_or_wav_audio_content_test_bytes_here")
        res = self.client.post(
            f"/api/interview/{self.interview_id}/submit-audio",
            data={
                "transcript": "Audio stream recorded answer with microsecond timing.",
                "duration_seconds": 18
            },
            files={"file": ("candidate_answer.webm", dummy_audio, "audio/webm")},
            headers=self.headers_a
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertIn("id", data)
        self.assertIsNotNone(data.get("audio_path"))
        self.assertTrue(os.path.exists(data["audio_path"]), "Uploaded audio file must be safely persisted on disk")
        SpeechFeaturesTestCase.answer_id_audio = data["id"]
        print("[PASS] test_03_speech_to_text_audio_file_upload: Multipart audio upload and server disk persistence verified.")

    def test_04_speech_to_text_answer_verification(self):
        """Verify candidate can fetch the transcribed answer with question text for review."""
        res = self.client.get(
            f"/api/interview/{self.interview_id}/answer/{self.answer_id_transcript}",
            headers=self.headers_a
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("question_text", data)
        self.assertIn("transcript", data)
        self.assertEqual(data["id"], self.answer_id_transcript)
        print("[PASS] test_04_speech_to_text_answer_verification: STT verification detail successfully retrieved.")

    def test_05_speech_to_text_manual_correction(self):
        """Verify candidate can refine/edit their transcribed answer before AI evaluation."""
        revised_text = "In my previous project, I designed a high-throughput RESTful API using FastAPI, PostgreSQL, and Redis caching."
        res = self.client.put(
            f"/api/interview/{self.interview_id}/answer/{self.answer_id_transcript}",
            json={"transcript": revised_text},
            headers=self.headers_a
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["transcript"], revised_text)

        # Confirm persistence
        fetch_res = self.client.get(
            f"/api/interview/{self.interview_id}/answer/{self.answer_id_transcript}",
            headers=self.headers_a
        )
        self.assertEqual(fetch_res.json()["transcript"], revised_text)
        print("[PASS] test_05_speech_to_text_manual_correction: Manual transcript edit correctly persisted.")

    def test_06_speech_security_and_isolation(self):
        """Verify unauthorized access blocked and cross-user isolation strictly enforced."""
        # Unauthenticated access
        unauth_tts = self.client.get(f"/api/interview/{self.interview_id}/question/{self.question_id}/tts-text")
        self.assertEqual(unauth_tts.status_code, 401)

        unauth_stt = self.client.get(f"/api/interview/{self.interview_id}/answer/{self.answer_id_transcript}")
        self.assertEqual(unauth_stt.status_code, 401)

        # Cross-user isolation: User B cannot access User A's answer
        cross_ans = self.client.get(
            f"/api/interview/{self.interview_id}/answer/{self.answer_id_transcript}",
            headers=self.headers_b
        )
        self.assertEqual(cross_ans.status_code, 404)

        # Cross-user isolation: User B cannot edit User A's answer
        cross_edit = self.client.put(
            f"/api/interview/{self.interview_id}/answer/{self.answer_id_transcript}",
            json={"transcript": "Hacked transcript"},
            headers=self.headers_b
        )
        self.assertEqual(cross_edit.status_code, 404)
        print("[PASS] test_06_speech_security_and_isolation: 401 unauthenticated & 404 cross-user security confirmed.")

    def test_07_voices_catalog_endpoint(self):
        """Verify voices catalog endpoint returns available neural voices and provider."""
        res = self.client.get("/api/interview/tts/voices")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("provider", data)
        self.assertIn("default_voice", data)
        self.assertIn("voices", data)
        self.assertGreaterEqual(len(data["voices"]), 4)
        print("[PASS] test_07_voices_catalog_endpoint: Curated voices catalog verified.")

    def test_08_neural_question_audio_stream(self):
        """Verify neural interviewer voice generation and audio/mpeg streaming."""
        res = self.client.get(
            f"/api/interview/{self.interview_id}/question/{self.question_id}/audio",
            headers=self.headers_a
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers["content-type"], "audio/mpeg")
        self.assertGreater(len(res.content), 1000, "Audio response should contain MP3 byte data")
        self.assertIn("Cache-Control", res.headers)
        print(f"[PASS] test_08_neural_question_audio_stream: Audio stream received ({len(res.content)} bytes).")

    def test_09_question_audio_security_and_isolation(self):
        """Verify audio stream enforces authentication and cross-user isolation."""
        # Unauthenticated access
        unauth_audio = self.client.get(f"/api/interview/{self.interview_id}/question/{self.question_id}/audio")
        self.assertEqual(unauth_audio.status_code, 401)

        # Cross-user isolation: User B cannot request User A's interview audio
        cross_audio = self.client.get(
            f"/api/interview/{self.interview_id}/question/{self.question_id}/audio",
            headers=self.headers_b
        )
        self.assertEqual(cross_audio.status_code, 404)
        print("[PASS] test_09_question_audio_security_and_isolation: 401 & 404 security confirmed.")

if __name__ == "__main__":
    unittest.main()

