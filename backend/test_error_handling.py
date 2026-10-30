import sys
import unittest
from fastapi.testclient import TestClient

from app.main import app
from app.services.ai_service import AIService, GeminiAIProvider, RuleBasedNLPProvider

class TestErrorHandlingAndResilience(unittest.TestCase):
    def setUp(self):
        # raise_server_exceptions=False allows testing sanitized 500 response behavior
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_01_health_check_passes(self):
        """Sanity check that server health check works."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "healthy")

    def test_02_404_not_found_handling(self):
        """Verify 404 returns structured error response without crash."""
        res = self.client.get("/api/non-existent-endpoint-test-404")
        self.assertEqual(res.status_code, 404)
        data = res.json()
        self.assertIn("detail", data)

    def test_03_401_unauthorized_handling(self):
        """Verify protected routes reject unauthenticated requests with clean 401."""
        res = self.client.get("/api/profile", headers={"Authorization": "Bearer invalid_token_12345"})
        self.assertEqual(res.status_code, 401)
        data = res.json()
        self.assertIn("detail", data)

    def test_04_422_validation_error_handling(self):
        """Verify pydantic validation errors return structured 422."""
        res = self.client.post("/api/auth/register", json={"email": "not-an-email"})
        self.assertEqual(res.status_code, 422)
        data = res.json()
        self.assertIn("detail", data)

    def test_05_500_exception_sanitization_no_traceback(self):
        """Verify unhandled exceptions return 500 with sanitized message and ZERO traceback leak."""
        res = self.client.get("/api/test-error")
        self.assertEqual(res.status_code, 500)
        data = res.json()
        self.assertEqual(data.get("detail"), "Unable to complete request. Please try again.")
        # Ensure raw stack trace or file paths are NOT exposed to the client
        self.assertNotIn("Simulated internal server exception", str(data))
        self.assertNotIn("Traceback", str(data))
        self.assertNotIn(".py", str(data))

    def test_06_ai_service_fallback_resilience(self):
        """Verify GeminiAIProvider transparently falls back to rule-based NLP when provider API fails."""
        # Provider configured with invalid key will fail external API call and gracefully fall back
        failing_provider = GeminiAIProvider(api_key="simulated_broken_key_xyz")
        service = AIService(provider=failing_provider)

        # 1. Test Question Generation Fallback
        res = service.generate_question({
            "target_role": "Software Developer",
            "difficulty": "Medium",
            "interview_type": "Technical",
            "skills": ["Python", "FastAPI"],
            "projects": ["Web API"],
            "question_index": 1,
            "total_questions": 5
        })
        self.assertIsInstance(res, dict)
        self.assertIn("question_text", res)
        self.assertTrue(len(res["question_text"]) > 0)
        self.assertEqual(res.get("category"), "Technical")

        # 2. Test Answer Evaluation Fallback
        eval_res = service.evaluate_answer(
            question_text="Explain database indexing in PostgreSQL.",
            answer_transcript="Indexing creates a B-tree data structure to accelerate lookup queries from O(N) to O(log N).",
            target_role="Backend Developer",
            difficulty="Medium"
        )
        self.assertIsInstance(eval_res, dict)
        self.assertIn("overall_score", eval_res)
        self.assertGreaterEqual(eval_res["overall_score"], 0)
        self.assertIn("feedback", eval_res)

        # 3. Test Resume Analysis Fallback
        resume_res = service.analyze_resume(
            "Experienced Python developer with React and PostgreSQL experience."
        )
        self.assertIsInstance(resume_res, dict)
        self.assertIn("skills", resume_res)
        self.assertTrue(len(resume_res["skills"]) > 0)


if __name__ == "__main__":
    unittest.main()
