import re
from typing import Dict, Any

def evaluate_answer_rule_based(
    question_text: str,
    answer_transcript: str,
    target_role: str = "Software Developer",
    difficulty: str = "Medium"
) -> Dict[str, Any]:
    """
    Evaluate candidate voice answer across Relevance, Technical Accuracy, Completeness, and Clarity.
    Returns scores out of 10 and concise practice feedback.
    """
    clean_ans = answer_transcript.strip()
    words = clean_ans.split()
    word_count = len(words)

    # Extract primary topic from question
    topic_match = re.search(r'\b(Flask|Python|Java|SQL|React|Docker|Django|FastAPI|PostgreSQL|MongoDB|REST|APIs?|Database|System Design|Git|Machine Learning)\b', question_text, re.IGNORECASE)
    primary_topic = topic_match.group(1).capitalize() if topic_match else "the technical topic"

    # If answer is practically empty (under 6 words)
    if word_count < 6:
        return {
            "relevance_score": 3,
            "technical_accuracy_score": 4,
            "completeness_score": 2,
            "clarity_score": 4,
            "overall_score": 3.3,
            "feedback": f"Your response was too brief to evaluate thoroughly. Try explaining how you applied {primary_topic} step-by-step with practical examples from your projects."
        }

    q_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', question_text.lower()))
    a_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', clean_ans.lower()))
    common_words = q_words.intersection(a_words)

    tech_keywords = {"framework", "library", "backend", "frontend", "database", "routing", "api", "rest", "model", "query", "request", "server", "architecture", "component", "function", "service"}
    tech_hits = [w for w in a_words if w in tech_keywords]

    # If answer is brief and lacks technical keywords
    if word_count < 12 and len(tech_hits) == 0 and primary_topic.lower() not in clean_ans.lower():
        return {
            "relevance_score": 4,
            "technical_accuracy_score": 4,
            "completeness_score": 3,
            "clarity_score": 5,
            "overall_score": 4.0,
            "feedback": f"Your answer was brief and lacked core technical depth regarding {primary_topic}. Try walking through specific implementation details and architecture."
        }

    # 1. Relevance Score (Did they answer what was asked?)
    relevance_score = 7
    if primary_topic.lower() in clean_ans.lower():
        relevance_score += 2
    if len(common_words) >= 3:
        relevance_score += 1
    relevance_score = min(10, max(4, relevance_score))

    # 2. Technical Accuracy
    if len(tech_hits) >= 3:
        technical_accuracy_score = 9
    elif len(tech_hits) >= 1:
        technical_accuracy_score = 8
    else:
        technical_accuracy_score = 6

    # 3. Completeness Score (Did they provide enough details?)
    if word_count < 15:
        completeness_score = 6
    elif word_count < 35:
        completeness_score = 7
    elif word_count < 65:
        completeness_score = 8
    else:
        completeness_score = 9

    # 4. Clarity Score (Understandable & well-structured)
    clarity_score = 8
    sentences = re.split(r'[.!?]+', clean_ans)
    if len(sentences) >= 2 and word_count >= 15:
        clarity_score = 8
    if word_count >= 25 and not re.search(r'\b(um|uh|like|you know)\b', clean_ans.lower()):
        clarity_score = 9

    # 5. Overall Score
    overall_score = round((relevance_score + technical_accuracy_score + completeness_score + clarity_score) / 4.0, 1)

    # 6. Concise Practice Feedback Generation
    if completeness_score <= 7:
        improvement = f"However, you could improve the answer by explaining how {primary_topic} handled requests in your project and citing specific implementation challenges."
    elif technical_accuracy_score <= 8:
        improvement = f"To strengthen your answer further, detail the architectural trade-offs and performance considerations associated with {primary_topic}."
    else:
        improvement = f"To make your response even more compelling, highlight measurable results or optimizations achieved in your project with {primary_topic}."

    feedback = f"Your answer correctly explains {primary_topic} and its purpose. {improvement}"

    return {
        "relevance_score": relevance_score,
        "technical_accuracy_score": technical_accuracy_score,
        "completeness_score": completeness_score,
        "clarity_score": clarity_score,
        "overall_score": overall_score,
        "feedback": feedback
    }


def evaluate_candidate_answer(
    question_text: str,
    answer_transcript: str,
    target_role: str = "Software Developer",
    difficulty: str = "Medium"
) -> Dict[str, Any]:
    """
    Evaluates candidate answer using the active AI service provider.
    """
    from app.services.ai_service import ai_service
    return ai_service.evaluate_answer(
        question_text=question_text,
        answer_transcript=answer_transcript,
        target_role=target_role,
        difficulty=difficulty
    )
