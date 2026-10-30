import abc
import os
import json
import re
import logging
from typing import Dict, Any, List, Optional
import requests

from app.config import settings

logger = logging.getLogger(__name__)

class BaseAIProvider(abc.ABC):
    """
    Abstract interface for AI/NLP service providers.
    Enables swapping underlying AI engines (Rule-based NLP, Gemini, OpenAI, etc.)
    without modifying application or router logic.
    """

    @abc.abstractmethod
    def analyze_resume(self, raw_text: str) -> Dict[str, Any]:
        """
        Input: Resume Text
        Output: Skills, Projects, Education, Experience, Keywords
        """
        pass

    @abc.abstractmethod
    def generate_question(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Input: Resume Information + Target Role + Interview Type + Difficulty + Previous Performance
        Output: Interview Question
        """
        pass

    @abc.abstractmethod
    def evaluate_answer(
        self,
        question_text: str,
        answer_transcript: str,
        target_role: str = "Software Developer",
        difficulty: str = "Medium"
    ) -> Dict[str, Any]:
        """
        Input: Question + User Answer
        Output: Relevance, Technical Accuracy, Completeness, Clarity, Overall Score, Feedback
        """
        pass

    @abc.abstractmethod
    def generate_recommendations(
        self,
        weak_areas: List[str],
        target_role: str = "Software Developer",
        overall_score: int = 75,
        difficulty: str = "Medium",
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Input: Interview History + Weak Areas + Target Role
        Output: Practice Recommendations
        """
        pass


class RuleBasedNLPProvider(BaseAIProvider):
    """
    Deterministic, reliable rule-based NLP and algorithmic provider.
    Guarantees 100% offline uptime, zero network latency, and deterministic reproducibility.
    """

    def analyze_resume(self, raw_text: str) -> Dict[str, Any]:
        from app.services.resume_analyzer import extract_resume_nlp
        return extract_resume_nlp(raw_text)

    def generate_question(self, context: Dict[str, Any]) -> Dict[str, Any]:
        from app.services.question_generator import generate_rule_based_question
        return generate_rule_based_question(
            interview_type=context.get("interview_type", "Technical"),
            difficulty=context.get("difficulty", "Medium"),
            target_role=context.get("target_role", "Software Developer"),
            question_index=context.get("question_index", 1),
            total_questions=context.get("total_questions", 10),
            skills=context.get("skills", []),
            projects=context.get("projects", []),
            education=context.get("education", ""),
            experience=context.get("experience", ""),
            asked_questions=context.get("asked_questions", []),
            history=context.get("history", [])
        )

    def evaluate_answer(
        self,
        question_text: str,
        answer_transcript: str,
        target_role: str = "Software Developer",
        difficulty: str = "Medium"
    ) -> Dict[str, Any]:
        from app.services.answer_evaluator import evaluate_answer_rule_based
        return evaluate_answer_rule_based(
            question_text=question_text,
            answer_transcript=answer_transcript,
            target_role=target_role,
            difficulty=difficulty
        )

    def generate_recommendations(
        self,
        weak_areas: List[str],
        target_role: str = "Software Developer",
        overall_score: int = 75,
        difficulty: str = "Medium",
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        from app.services.recommendation_generator import generate_rule_based_recommendation_items
        return generate_rule_based_recommendation_items(
            weak_areas=weak_areas,
            target_role=target_role,
            overall_score=overall_score,
            difficulty=difficulty,
            history=history
        )


class GeminiAIProvider(BaseAIProvider):
    """
    Cloud AI provider powered by Google Gemini REST API.
    Gracefully falls back to RuleBasedNLPProvider upon any network failure, timeout, or rate-limit.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.fallback = RuleBasedNLPProvider()
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"

    def _call_gemini_json(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call Gemini API requesting JSON output with graceful exception handling."""
        try:
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
            }
            resp = requests.post(self.endpoint, json=payload, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                text_content = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text_content)
        except Exception as e:
            logger.warning(f"Gemini API invocation failed ({e}), falling back to RuleBasedNLPProvider.")
        return None

    def analyze_resume(self, raw_text: str) -> Dict[str, Any]:
        prompt = (
            "Extract structured resume information from the following text as JSON with keys: "
            "skills (list of str), projects (list of str), education (str), experience (str), keywords (list of str).\n\n"
            f"Resume Text:\n{raw_text[:4000]}"
        )
        res = self._call_gemini_json(prompt)
        if res and isinstance(res, dict) and "skills" in res:
            res.setdefault("certifications", "None listed")
            res.setdefault("technologies", res.get("skills", []))
            return res
        return self.fallback.analyze_resume(raw_text)

    def generate_question(self, context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = (
            f"You are an interviewer conducting a {context.get('interview_type')} interview for a {context.get('target_role')} position. "
            f"Question {context.get('question_index')} of {context.get('total_questions')}. Difficulty: {context.get('difficulty')}. "
            f"Skills: {', '.join(context.get('skills', []))}. Projects: {', '.join(context.get('projects', []))}.\n"
            "Return JSON with keys: question_text (str), category (str), difficulty (str), is_adaptive (bool), adaptive_reason (str)."
        )
        res = self._call_gemini_json(prompt)
        if res and isinstance(res, dict) and "question_text" in res:
            return res
        return self.fallback.generate_question(context)

    def evaluate_answer(
        self,
        question_text: str,
        answer_transcript: str,
        target_role: str = "Software Developer",
        difficulty: str = "Medium"
    ) -> Dict[str, Any]:
        prompt = (
            f"Evaluate this interview answer for a {target_role} role at {difficulty} difficulty.\n"
            f"Question: {question_text}\nAnswer: {answer_transcript}\n\n"
            "Return JSON with keys: relevance_score (int 1-10), technical_accuracy_score (int 1-10), "
            "completeness_score (int 1-10), clarity_score (int 1-10), overall_score (float 1.0-10.0), feedback (str)."
        )
        res = self._call_gemini_json(prompt)
        if res and isinstance(res, dict) and "overall_score" in res:
            return res
        return self.fallback.evaluate_answer(question_text, answer_transcript, target_role, difficulty)

    def generate_recommendations(
        self,
        weak_areas: List[str],
        target_role: str = "Software Developer",
        overall_score: int = 75,
        difficulty: str = "Medium",
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        prompt = (
            f"Generate 3 actionable practice recommendations for a candidate who scored {overall_score}/100 "
            f"for a {target_role} interview, with weak areas: {', '.join(weak_areas)}.\n\n"
            "Return JSON with keys:\n"
            "- recommendations: list of objects with step_number (int), title (str), description (str), category (str)\n"
            "- suggested_setup: object with target_role (str), interview_type (str), difficulty (str), focus_topics (list of str)\n"
            "- summary_message: str"
        )
        res = self._call_gemini_json(prompt)
        if res and isinstance(res, dict) and "recommendations" in res:
            return res
        return self.fallback.generate_recommendations(weak_areas, target_role, overall_score, difficulty, history)


class AIService:
    """
    Central AI/NLP Service Façade.
    Exposes unified methods across all platform capabilities and supports hot-swapping providers.
    """

    def __init__(self, provider: Optional[BaseAIProvider] = None):
        self._provider = provider or self._resolve_default_provider()

    def _resolve_default_provider(self) -> BaseAIProvider:
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
            return GeminiAIProvider(api_key=settings.GEMINI_API_KEY.strip())
        return RuleBasedNLPProvider()

    def set_provider(self, provider: BaseAIProvider):
        """Allows injecting or mocking the AI provider at runtime."""
        self._provider = provider

    def reset_provider(self):
        """Resets to default environment provider configuration."""
        self._provider = self._resolve_default_provider()

    @property
    def provider(self) -> BaseAIProvider:
        return self._provider

    def analyze_resume(self, raw_text: str) -> Dict[str, Any]:
        return self._provider.analyze_resume(raw_text)

    def generate_question(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return self._provider.generate_question(context)

    def evaluate_answer(
        self,
        question_text: str,
        answer_transcript: str,
        target_role: str = "Software Developer",
        difficulty: str = "Medium"
    ) -> Dict[str, Any]:
        return self._provider.evaluate_answer(
            question_text=question_text,
            answer_transcript=answer_transcript,
            target_role=target_role,
            difficulty=difficulty
        )

    def generate_recommendations(
        self,
        weak_areas: List[str],
        target_role: str = "Software Developer",
        overall_score: int = 75,
        difficulty: str = "Medium",
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        return self._provider.generate_recommendations(
            weak_areas=weak_areas,
            target_role=target_role,
            overall_score=overall_score,
            difficulty=difficulty,
            history=history
        )


# Global default instance
ai_service = AIService()
