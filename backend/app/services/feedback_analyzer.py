import re
import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models import Interview, Question, Answer, Evaluation, Feedback

TOPIC_PATTERNS = [
    (r'\b(python|django|flask|fastapi)\b', "Python"),
    (r'\b(sql|database|postgres|mysql|sqlite|normalization|queries?)\b', "SQL & Databases"),
    (r'\b(rest|apis?|endpoints?|routing|http)\b', "REST APIs & Architecture"),
    (r'\b(concurrency|threading|multithreading|async|event loop)\b', "Concurrency & Async Models"),
    (r'\b(scaling|scale|distributed|caching|redis|load balancer?)\b', "System Design & Scalability"),
    (r'\b(testing|unit test|integration test|mock|coverage)\b', "Testing & Code Quality"),
    (r'\b(oop|object oriented|classes?|inheritance|polymorphism)\b', "OOP & Software Design"),
    (r'\b(docker|kubernetes|container|ci/cd|deployment)\b', "DevOps & Deployment"),
    (r'\b(error handling|exceptions?|validation|debugging)\b', "Error Handling & Robustness"),
    (r'\b(communication|feedback|collaboration|teamwork)\b', "Communication & Collaboration")
]

def extract_topics(text: str) -> List[str]:
    found = []
    text_lower = text.lower()
    for pattern, label in TOPIC_PATTERNS:
        if re.search(pattern, text_lower):
            found.append(label)
    return found

def analyze_interview_feedback(
    interview_id: int,
    user_id: int,
    db: Session
) -> Dict[str, Any]:
    """
    Analyze current interview performance and identify:
    - Strong Areas (high scores, solid technical depth)
    - Areas to Improve (low scores, missed technical depth)
    - Recurring Weaknesses across past user interviews
    """
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == user_id
    ).first()

    if not interview:
        return {
            "strong_areas": [],
            "weak_areas": [],
            "recurring_weaknesses": [],
            "summary_notes": "",
            "question_feedbacks": []
        }

    # Fetch questions and evaluations for this interview
    questions = db.query(Question).filter(
        Question.interview_id == interview.id
    ).order_by(Question.question_index.asc()).all()

    evaluations = db.query(Evaluation).filter(
        Evaluation.interview_id == interview.id
    ).all()

    eval_by_qid = {e.question_id: e for e in evaluations}

    current_strong = []
    current_weak = []
    question_feedbacks = []

    for q in questions:
        ev = eval_by_qid.get(q.id)
        ans = db.query(Answer).filter(
            Answer.question_id == q.id,
            Answer.interview_id == interview.id
        ).order_by(Answer.id.desc()).first()

        transcript = ans.transcript if ans else ""
        score = ev.overall_score if ev else 0.0
        feedback_text = ev.feedback if ev else "No evaluation recorded."

        topics = extract_topics(q.question_text + " " + transcript)
        if not topics:
            topics = [q.category or "General Problem Solving"]

        for t in topics:
            if score >= 8.0:
                if t not in current_strong:
                    current_strong.append(t)
            elif score < 7.5:
                if t not in current_weak:
                    current_weak.append(t)

        question_feedbacks.append({
            "question_index": q.question_index,
            "question_text": q.question_text,
            "category": q.category or "Technical",
            "difficulty": q.difficulty or "Medium",
            "overall_score": score,
            "transcript": transcript,
            "feedback": feedback_text
        })

    # Fallbacks if none detected
    if not current_strong:
        current_strong = ["Python", "Problem Solving"]
    if not current_weak:
        current_weak = ["System Design", "Database Normalization"]

    # Deduplicate weak areas from strong areas
    filtered_weak = [w for w in current_weak if w not in current_strong or current_weak.count(w) > 1]
    if not filtered_weak:
        filtered_weak = current_weak

    # Cross-Interview Analysis: Identify Recurring Weaknesses
    past_interviews = db.query(Interview).filter(
        Interview.user_id == user_id,
        Interview.id != interview.id
    ).all()

    weakness_frequency = {}

    for ui in past_interviews:
        # Check stored weak areas or analyze past evaluations
        if ui.weak_areas:
            try:
                past_weaks = json.loads(ui.weak_areas)
                for pw in past_weaks:
                    weakness_frequency[pw] = weakness_frequency.get(pw, 0) + 1
            except Exception:
                pass
        else:
            # Inspect evaluations of past interview
            past_evals = db.query(Evaluation).filter(Evaluation.interview_id == ui.id).all()
            for pe in past_evals:
                if pe.overall_score < 7.5:
                    pq = db.query(Question).filter(Question.id == pe.question_id).first()
                    if pq:
                        top_list = extract_topics(pq.question_text)
                        for top in top_list:
                            weakness_frequency[top] = weakness_frequency.get(top, 0) + 1

    # Add current session's weak areas into total frequency count
    for cw in filtered_weak:
        weakness_frequency[cw] = weakness_frequency.get(cw, 0) + 1

    recurring_weaknesses = []
    for topic, count in weakness_frequency.items():
        if count >= 2:
            recurring_weaknesses.append({
                "topic": topic,
                "frequency": count,
                "note": f"Identified in {count} interview sessions. Needs focused revision."
            })

    # Save weak_areas and strong_areas on interview object
    interview.strong_areas = json.dumps(current_strong)
    interview.weak_areas = json.dumps(filtered_weak)

    # Generate concise summary notes
    summary = (
        f"You demonstrated solid proficiency in {', '.join(current_strong[:2])}. "
        f"Prioritize practicing {', '.join(filtered_weak[:2])} to strengthen your overall technical interview profile."
    )

    # Synchronize relational Feedback entity
    try:
        fb_entity = db.query(Feedback).filter(Feedback.interview_id == interview.id).first()
        if not fb_entity:
            fb_entity = Feedback(
                interview_id=interview.id,
                overall_score=interview.overall_score or 75,
                strong_areas=json.dumps(current_strong),
                weak_areas=json.dumps(filtered_weak),
                summary=summary
            )
            db.add(fb_entity)
        else:
            fb_entity.overall_score = interview.overall_score or 75
            fb_entity.strong_areas = json.dumps(current_strong)
            fb_entity.weak_areas = json.dumps(filtered_weak)
            fb_entity.summary = summary
    except Exception:
        pass

    db.commit()

    return {
        "strong_areas": current_strong,
        "weak_areas": filtered_weak,
        "recurring_weaknesses": recurring_weaknesses,
        "summary_notes": summary,
        "question_feedbacks": question_feedbacks
    }
