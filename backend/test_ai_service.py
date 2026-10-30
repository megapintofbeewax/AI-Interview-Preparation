import os
import sys
import unittest
from typing import Dict, Any, List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.ai_service import (
    BaseAIProvider,
    RuleBasedNLPProvider,
    GeminiAIProvider,
    AIService,
    ai_service
)
from app.services.resume_analyzer import analyze_resume_text
from app.services.question_generator import generate_interview_question
from app.services.answer_evaluator import evaluate_candidate_answer
from app.services.recommendation_generator import generate_rule_based_recommendation_items

class MockCustomAIProvider(BaseAIProvider):
    """Custom mock provider to test hot-swapping AI providers at runtime."""

    def analyze_resume(self, raw_text: str) -> Dict[str, Any]:
        return {
            "skills": ["CustomLanguage", "CustomFramework"],
            "projects": ["Custom Project A"],
            "education": "Custom University",
            "experience": "Custom Software Engineer",
            "keywords": ["CustomKeyword"],
            "technologies": ["CustomTech"]
        }

    def generate_question(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "question_text": "Custom Mock Generated Question: Explain custom design patterns?",
            "category": "CustomCategory",
            "difficulty": context.get("difficulty", "Medium"),
            "is_adaptive": True,
            "adaptive_reason": "Custom mock adaptive reason"
        }

    def evaluate_answer(
        self,
        question_text: str,
        answer_transcript: str,
        target_role: str = "Software Developer",
        difficulty: str = "Medium"
    ) -> Dict[str, Any]:
        return {
            "relevance_score": 10,
            "technical_accuracy_score": 10,
            "completeness_score": 10,
            "clarity_score": 10,
            "overall_score": 10.0,
            "feedback": "Custom mock flawless answer feedback."
        }

    def generate_recommendations(
        self,
        weak_areas: List[str],
        target_role: str = "Software Developer",
        overall_score: int = 75,
        difficulty: str = "Medium",
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        return {
            "recommendations": [
                {
                    "step_number": 1,
                    "title": "Custom Step",
                    "description": "Custom Description",
                    "category": "Custom"
                }
            ],
            "suggested_setup": {
                "target_role": target_role,
                "interview_type": "Technical",
                "difficulty": difficulty,
                "focus_topics": weak_areas
            },
            "summary_message": "Custom mock recommendations summary."
        }


class AIServiceLayerTestCase(unittest.TestCase):
    def tearDown(self):
        # Guarantee default provider is restored after each test
        ai_service.reset_provider()

    def test_01_default_provider_and_interface(self):
        """Verify default AI provider adheres to BaseAIProvider interface."""
        provider = ai_service.provider
        self.assertIsInstance(provider, BaseAIProvider)
        self.assertTrue(hasattr(provider, "analyze_resume"))
        self.assertTrue(hasattr(provider, "generate_question"))
        self.assertTrue(hasattr(provider, "evaluate_answer"))
        self.assertTrue(hasattr(provider, "generate_recommendations"))
        print("[PASS] test_01_default_provider_and_interface: AIService correctly initialized with BaseAIProvider.")

    def test_02_resume_analysis_capability(self):
        """Verify Resume Analysis handling (Skills, Projects, Education, Experience, Keywords)."""
        sample_resume = """
        John Doe
        Email: john@example.com
        
        EDUCATION
        B.Tech in Computer Science from National Institute of Technology, 2024
        
        SKILLS
        Python, FastAPI, React, PostgreSQL, Docker, Git, REST APIs
        
        PROJECTS
        AI Placement Platform: Built full stack preparation web application with FastAPI and React.
        Microservices Pipeline: Scaled backend services with Docker and Redis.
        
        EXPERIENCE
        Software Engineering Intern at Tech Corp: Worked on backend database optimization and API routes.
        """
        result = ai_service.analyze_resume(sample_resume)
        self.assertIn("skills", result)
        self.assertIn("projects", result)
        self.assertIn("education", result)
        self.assertIn("experience", result)
        self.assertIn("keywords", result)

        self.assertIn("Python", result["skills"])
        self.assertIn("FastAPI", result["skills"])
        self.assertIn("B.Tech in Computer Science", result["education"])
        self.assertTrue(len(result["projects"]) >= 1)

        # Also test via wrapper in resume_analyzer
        wrapped_result = analyze_resume_text(sample_resume)
        self.assertEqual(wrapped_result["skills"], result["skills"])
        print("[PASS] test_02_resume_analysis_capability: Resume Analysis extracted all required dimensions.")

    def test_03_question_generation_capability(self):
        """Verify Question Generation handling (Resume Info + Role + Type + Difficulty + Performance)."""
        context = {
            "interview_type": "Technical",
            "difficulty": "Medium",
            "target_role": "Backend Engineer",
            "question_index": 1,
            "total_questions": 5,
            "skills": ["Python", "SQL", "Docker"],
            "projects": ["Distributed Cache"],
            "education": "B.Tech",
            "experience": "Intern",
            "asked_questions": [],
            "history": []
        }
        result = ai_service.generate_question(context)
        self.assertIn("question_text", result)
        self.assertIn("category", result)
        self.assertIn("difficulty", result)
        self.assertIn("is_adaptive", result)
        self.assertIn("adaptive_reason", result)

        self.assertTrue(len(result["question_text"]) > 10)
        self.assertEqual(result["category"], "Technical")

        # Test adaptive follow-up when previous performance was low (< 5.0)
        context_adaptive = {
            "interview_type": "Technical",
            "difficulty": "Medium",
            "target_role": "Backend Engineer",
            "question_index": 2,
            "total_questions": 5,
            "skills": ["Python", "SQL"],
            "projects": ["Distributed Cache"],
            "asked_questions": [result["question_text"]],
            "history": [
                {
                    "question_text": result["question_text"],
                    "answer_transcript": "I am not sure.",
                    "overall_score": 3.0,
                    "difficulty": "Medium"
                }
            ]
        }
        res_adaptive = ai_service.generate_question(context_adaptive)
        self.assertTrue(res_adaptive["is_adaptive"])
        self.assertEqual(res_adaptive["difficulty"], "Easy")
        print("[PASS] test_03_question_generation_capability: Question Generation handles contextual & adaptive requirements.")

    def test_04_answer_evaluation_capability(self):
        """Verify Answer Evaluation handling (Relevance, Technical Accuracy, Completeness, Clarity, Overall Score, Feedback)."""
        question = "Explain how database indexing works and why B-trees are commonly used."
        good_answer = "Database indexes use balanced B-tree data structures to provide O(log n) search, insertion, and deletion times instead of scanning the full table sequentially. This drastically reduces disk I/O operations for queries."
        
        eval_result = ai_service.evaluate_answer(
            question_text=question,
            answer_transcript=good_answer,
            target_role="Backend Developer",
            difficulty="Medium"
        )
        self.assertIn("relevance_score", eval_result)
        self.assertIn("technical_accuracy_score", eval_result)
        self.assertIn("completeness_score", eval_result)
        self.assertIn("clarity_score", eval_result)
        self.assertIn("overall_score", eval_result)
        self.assertIn("feedback", eval_result)

        self.assertGreaterEqual(eval_result["overall_score"], 7.0)
        self.assertTrue(len(eval_result["feedback"]) > 15)

        # Test poor/brief answer
        poor_result = ai_service.evaluate_answer(
            question_text=question,
            answer_transcript="Indexes make things faster.",
            target_role="Backend Developer",
            difficulty="Medium"
        )
        self.assertLessEqual(poor_result["overall_score"], 5.0)
        print("[PASS] test_04_answer_evaluation_capability: Answer Evaluation scored all 4 metrics + overall + feedback.")

    def test_05_recommendations_capability(self):
        """Verify Recommendations handling (History + Weak Areas + Target Role)."""
        weak_areas = ["SQL & Databases", "System Design & Scalability"]
        history = [
            {"weak_areas": ["SQL & Databases"]},
            {"weak_areas": ["System Design & Scalability"]}
        ]
        rec_result = ai_service.generate_recommendations(
            weak_areas=weak_areas,
            target_role="Backend Developer",
            overall_score=72,
            difficulty="Medium",
            history=history
        )
        self.assertIn("recommendations", rec_result)
        self.assertIn("suggested_setup", rec_result)
        self.assertIn("summary_message", rec_result)

        self.assertGreaterEqual(len(rec_result["recommendations"]), 3)
        first_step = rec_result["recommendations"][0]
        self.assertIn("step_number", first_step)
        self.assertIn("title", first_step)
        self.assertIn("description", first_step)
        self.assertIn("category", first_step)

        self.assertEqual(rec_result["suggested_setup"]["target_role"], "Backend Developer")
        print("[PASS] test_05_recommendations_capability: Practice Recommendations generated actionable steps & setup.")

    def test_06_provider_hot_swapping(self):
        """Verify modular AI provider hot-swapping using MockCustomAIProvider."""
        mock_provider = MockCustomAIProvider()
        ai_service.set_provider(mock_provider)

        # Verify swapped behavior
        resume_res = ai_service.analyze_resume("Any raw text")
        self.assertEqual(resume_res["skills"], ["CustomLanguage", "CustomFramework"])

        q_res = ai_service.generate_question({"difficulty": "Hard"})
        self.assertEqual(q_res["question_text"], "Custom Mock Generated Question: Explain custom design patterns?")

        eval_res = ai_service.evaluate_answer("q", "a")
        self.assertEqual(eval_res["overall_score"], 10.0)
        self.assertEqual(eval_res["feedback"], "Custom mock flawless answer feedback.")

        rec_res = ai_service.generate_recommendations(["weak"], "Role", 80, "Hard")
        self.assertEqual(rec_res["summary_message"], "Custom mock recommendations summary.")

        # Reset to default
        ai_service.reset_provider()
        self.assertNotEqual(ai_service.provider, mock_provider)
        print("[PASS] test_06_provider_hot_swapping: Provider hot-swapping and resetting verified.")

    def test_07_gemini_fallback_resiliency(self):
        """Verify GeminiAIProvider falls back to RuleBasedNLPProvider upon network or authentication failure."""
        gemini_provider = GeminiAIProvider(api_key="invalid_dummy_key_to_test_fallback")
        
        # Test fallback on resume analysis
        resume_fallback = gemini_provider.analyze_resume("Python and SQL developer with B.Tech degree.")
        self.assertIn("skills", resume_fallback)
        self.assertIn("Python", resume_fallback["skills"])

        # Test fallback on question generation
        q_fallback = gemini_provider.generate_question({
            "interview_type": "Technical",
            "difficulty": "Easy",
            "target_role": "Python Developer",
            "question_index": 1,
            "total_questions": 5,
            "skills": ["Python"]
        })
        self.assertIn("question_text", q_fallback)
        self.assertIn("category", q_fallback)

        # Test fallback on answer evaluation
        eval_fallback = gemini_provider.evaluate_answer(
            question_text="What is Python?",
            answer_transcript="Python is a high-level interpreted programming language with clean syntax.",
            target_role="Python Developer",
            difficulty="Easy"
        )
        self.assertIn("overall_score", eval_fallback)
        self.assertGreaterEqual(eval_fallback["overall_score"], 6.0)

        print("[PASS] test_07_gemini_fallback_resiliency: Gemini provider gracefully falls back to RuleBasedNLPProvider on API errors.")

if __name__ == "__main__":
    unittest.main()
