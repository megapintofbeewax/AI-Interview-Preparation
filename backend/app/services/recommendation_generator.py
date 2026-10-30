import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models import Interview, Evaluation, Question, Recommendation
from app.services.feedback_analyzer import analyze_interview_feedback

def generate_rule_based_recommendation_items(
    weak_areas: List[str],
    target_role: str = "Software Developer",
    overall_score: int = 75,
    difficulty: str = "Medium",
    history: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Algorithmic generator for actionable practice recommendations.
    """
    recurring = []
    if history:
        for h in history:
            for w in h.get("weak_areas", []):
                if w:
                    recurring.append({"topic": w})

    recommendations = []
    step = 1

    weak_str = " ".join(weak_areas).lower()
    rec_str = " ".join([r.get("topic", "") for r in recurring]).lower()
    combined_weak = weak_str + " " + rec_str

    if "sql" in combined_weak or "database" in combined_weak:
        recommendations.append({
            "step_number": step,
            "title": "Practice SQL JOIN questions",
            "description": "Drill complex multi-table JOINs, GROUP BY aggregations, and subquery performance tuning.",
            "category": "Databases"
        })
        step += 1
        recommendations.append({
            "step_number": step,
            "title": "Revise database normalization",
            "description": "Review 1NF through 3NF schema design rules and ACID consistency guarantees.",
            "category": "Databases"
        })
        step += 1

    if "system design" in combined_weak or "scaling" in combined_weak:
        recommendations.append({
            "step_number": step,
            "title": "Practice backend architecture questions",
            "description": "Focus on horizontal scaling, distributed caching with Redis, and database read-replicas.",
            "category": "Architecture"
        })
        step += 1

    if "concurrency" in combined_weak or "async" in combined_weak:
        recommendations.append({
            "step_number": step,
            "title": "Master asynchronous processing & concurrency",
            "description": "Understand thread safety, async event loops, and background job queues.",
            "category": "Concurrency"
        })
        step += 1

    if "rest" in combined_weak or "api" in combined_weak:
        recommendations.append({
            "step_number": step,
            "title": "Refine RESTful API design patterns",
            "description": "Study idempotent operations, pagination, authentication headers, and error payload standards.",
            "category": "APIs"
        })
        step += 1

    if len(recommendations) < 3:
        recommendations.append({
            "step_number": step,
            "title": f"Review core {target_role} fundamentals",
            "description": f"Solidify key technical concepts and clean coding practices expected of a {target_role}.",
            "category": "Core Knowledge"
        })
        step += 1
        recommendations.append({
            "step_number": step,
            "title": "Prepare concrete project examples",
            "description": "Structure your answers using STAR (Situation, Task, Action, Result) with measurable metrics.",
            "category": "Technique"
        })
        step += 1

    if overall_score < 70:
        recommended_difficulty = "Easy" if difficulty == "Easy" else "Medium"
        next_step_title = f"Attempt {recommended_difficulty.lower()}-level technical interviews"
        next_step_desc = f"Build confidence and fluency by practicing {recommended_difficulty}-level questions before scaling up."
    elif overall_score < 85:
        recommended_difficulty = "Medium"
        next_step_title = "Attempt medium-level technical interviews"
        next_step_desc = "Consolidate your knowledge and refine technical accuracy across end-to-end questions."
    else:
        recommended_difficulty = "Hard"
        next_step_title = "Attempt hard-level technical interviews"
        next_step_desc = "Challenge yourself with senior-level architecture, distributed trade-offs, and failure recovery."

    recommendations.append({
        "step_number": step,
        "title": next_step_title,
        "description": next_step_desc,
        "category": "Next Session"
    })

    suggested_setup = {
        "target_role": target_role,
        "interview_type": "Technical",
        "difficulty": recommended_difficulty,
        "focus_topics": weak_areas[:3]
    }

    summary = (
        f"Based on your score of {overall_score}/100 in the {target_role} interview, "
        f"focusing on {', '.join([r['title'] for r in recommendations[:2]])} "
        f"will yield the fastest improvement for your upcoming interviews."
    )

    return {
        "recommendations": recommendations,
        "suggested_setup": suggested_setup,
        "summary_message": summary
    }


def generate_personalized_recommendations(
    interview_id: int,
    user_id: int,
    db: Session
) -> Dict[str, Any]:
    """
    Generate actionable personalized practice recommendations based on:
    - Weak areas (current session & recurring weaknesses)
    - Previous scores
    - Target job role
    - Interview history
    """
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == user_id
    ).first()

    if not interview:
        return {
            "recommendations": [],
            "suggested_setup": {
                "target_role": "Software Developer",
                "interview_type": "Technical",
                "difficulty": "Medium",
                "focus_topics": []
            },
            "summary_message": ""
        }

    # Extract feedback analysis for weak areas and recurring gaps
    feedback = analyze_interview_feedback(interview_id=interview.id, user_id=user_id, db=db)
    weak_areas = feedback.get("weak_areas", [])
    recurring = feedback.get("recurring_weaknesses", [])
    overall_score = interview.overall_score or 75
    target_role = interview.target_role or "Software Developer"
    interview_type = interview.interview_type or "Technical"
    difficulty = interview.difficulty or "Medium"

    from app.services.ai_service import ai_service
    rec_data = ai_service.generate_recommendations(
        weak_areas=weak_areas,
        target_role=target_role,
        overall_score=overall_score,
        difficulty=difficulty,
        history=[{"weak_areas": [r.get("topic")]} for r in recurring]
    )
    recommendations = rec_data.get("recommendations", [])
    suggested_setup = rec_data.get("suggested_setup", {})
    suggested_setup["interview_type"] = interview_type
    summary = rec_data.get("summary_message", "")

    # Persist in interview model and relational Recommendation entities
    try:
        interview.recommendations = json.dumps(recommendations)
        db.query(Recommendation).filter(Recommendation.interview_id == interview.id).delete()
        for r in recommendations:
            rec_entity = Recommendation(
                interview_id=interview.id,
                step_number=r.get("step_number", 1),
                title=r.get("title", ""),
                description=r.get("description", ""),
                category=r.get("category", "General")
            )
            db.add(rec_entity)
        db.commit()
    except Exception:
        pass

    return {
        "recommendations": recommendations,
        "suggested_setup": suggested_setup,
        "summary_message": summary
    }
