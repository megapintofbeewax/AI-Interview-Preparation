import os
import random
from typing import List, Dict, Any, Optional
from app.config import settings

def generate_rule_based_question(
    interview_type: str,
    difficulty: str,
    target_role: str,
    question_index: int,
    total_questions: int,
    skills: List[str] = None,
    projects: List[str] = None,
    education: str = "",
    experience: str = "",
    asked_questions: List[str] = None,
    history: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate contextual and adaptive interview question based on:
    - Resume information (skills, projects, education, experience)
    - Target job role
    - Interview type (Technical, HR / Behavioral, Mixed)
    - Base difficulty & previous adapted difficulty
    - Previous questions asked (prevents repetitions)
    - Previous answers given by the candidate
    - Previous evaluation scores (increases difficulty if strong, clarifies if weak)
    """
    skills = [s for s in (skills or []) if s.strip()] or ["Python", "Flask", "SQL", "Git"]
    projects = [p for p in (projects or []) if p.strip()] or ["AI Placement Platform", "Web Service"]
    asked_questions = asked_questions or []
    history = history or []

    # Select candidate anchors based on rotation
    primary_skill = skills[(question_index - 1) % len(skills)]
    secondary_skill = skills[question_index % len(skills)]
    primary_project = projects[(question_index - 1) % len(projects)]

    is_technical = interview_type == "Technical" or (interview_type == "Mixed" and question_index % 2 == 1)
    category = "Technical" if is_technical else "Behavioral"

    is_adaptive = False
    adaptive_reason = "Initial session question based on target role and resume profile."
    current_difficulty = difficulty
    candidate_questions = []

    # Optional: If Gemini API key is configured, attempt intelligent model generation
    if settings.GEMINI_API_KEY and history:
        try:
            import requests
            prompt_content = f"""
You are an expert interviewer conducting a {interview_type} interview for a {target_role} role.
Candidate Resume Skills: {', '.join(skills)}
Candidate Projects: {', '.join(projects)}
Current Question Index: {question_index} of {total_questions}
Base Difficulty: {difficulty}

Previous History:
"""
            for h in history:
                prompt_content += f"- Q: {h.get('question_text')} | Answer: {h.get('transcript')} | Score: {h.get('overall_score')}/10 | Feedback: {h.get('feedback')}\n"

            prompt_content += """
Generate the next single interview question adaptively:
- If previous score >= 8.0: Increase difficulty with an advanced technical/architectural or trade-off challenge.
- If previous score < 6.0: Ask a simpler or clarifying follow-up question directly addressing the previous topic.
- Otherwise: Ask a solid progression question.
Respond with ONLY the exact question text.
"""
            resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}",
                json={"contents": [{"parts": [{"text": prompt_content}]}]},
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                if text:
                    last_entry = history[-1]
                    last_score = last_entry.get("overall_score", 7.0)
                    if last_score and last_score >= 8.0:
                        adapted_diff = "Hard" if difficulty in ["Medium", "Hard"] else "Medium"
                        reason = f"Increased difficulty to {adapted_diff} following strong answer ({last_score:.1f}/10)."
                    elif last_score and last_score < 6.0:
                        adapted_diff = "Easy" if difficulty in ["Easy", "Medium"] else "Medium"
                        reason = f"Adjusted difficulty to {adapted_diff} with a clarifying follow-up after low score ({last_score:.1f}/10)."
                    else:
                        adapted_diff = difficulty
                        reason = f"Maintained {adapted_diff} difficulty based on steady performance."
                    return {
                        "question_text": text.strip('"\''),
                        "category": category,
                        "difficulty": adapted_diff,
                        "is_adaptive": True,
                        "adaptive_reason": reason
                    }
        except Exception:
            # Fallback to local adaptive engine
            pass

    # Algorithmic Adaptive Engine
    if history and question_index > 1:
        last_entry = history[-1]
        last_score = last_entry.get("overall_score")
        last_transcript = last_entry.get("transcript", "").strip()
        last_q_text = last_entry.get("question_text", "")
        last_diff = last_entry.get("difficulty", difficulty)
        is_adaptive = True

        # Find topic/skill referenced in last interaction
        discussed_skill = primary_skill
        for s in skills:
            if s.lower() in last_q_text.lower() or s.lower() in last_transcript.lower():
                discussed_skill = s
                break

        # Case 1: High Performance (Score >= 8.0) -> Increase Difficulty
        if last_score is not None and last_score >= 8.0:
            if last_diff == "Easy":
                current_difficulty = "Medium"
            elif last_diff in ["Medium", "Hard"]:
                current_difficulty = "Hard"

            adaptive_reason = f"Difficulty increased to {current_difficulty} following strong answer ({last_score:.1f}/10) on previous question."

            if is_technical:
                candidate_questions = [
                    f"Building on your strong explanation of {discussed_skill}, how would you architect this solution to handle distributed concurrency and fault tolerance at scale?",
                    f"In your project '{primary_project}', what are the critical latency and performance bottlenecks when scaling {discussed_skill}, and how would you optimize them?",
                    f"How would you design a caching and data consistency strategy if multiple microservices concurrently read and write data in your {discussed_skill} pipeline?",
                    f"Explain the internal memory and threading model of {discussed_skill}, and how you would diagnose a silent production deadlock or memory leak.",
                    f"Walk me through a zero-downtime deployment and failover strategy for a {target_role} service relying on {discussed_skill} and {secondary_skill}."
                ]
            else:
                candidate_questions = [
                    f"Building on your previous project experience, describe a high-pressure situation where a production deployment failed and how you led the post-mortem and mitigation.",
                    f"As a {target_role}, how do you resolve significant technical disagreements with senior architects regarding {discussed_skill} architecture?",
                    f"Tell me about a time you mentored a junior engineer who was struggling with {discussed_skill} concepts in '{primary_project}'."
                ]

        # Case 2: Low Performance (Score < 6.0) -> Simpler or Clarifying Follow-Up
        elif last_score is not None and last_score < 6.0:
            if last_diff == "Hard":
                current_difficulty = "Medium"
            elif last_diff in ["Medium", "Easy"]:
                current_difficulty = "Easy"

            adaptive_reason = f"Adjusted difficulty to {current_difficulty} with a clarifying follow-up after low score ({last_score:.1f}/10) on previous question."

            if is_technical:
                candidate_questions = [
                    f"In your previous response about {discussed_skill}, you gave a brief overview. Could you clarify in simpler terms how {discussed_skill} actually works under the hood, with a basic code or workflow example?",
                    f"Let's break that down into simpler fundamentals: what is the core responsibility of {discussed_skill}, and why did you choose it for '{primary_project}'?",
                    f"To clarify your previous answer: how would you explain the fundamental purpose and basic request flow of {discussed_skill} to a junior developer?",
                    f"Can you clarify the step-by-step process you followed when setting up basic error handling and data validation in {discussed_skill}?",
                    f"Let's simplify: what are the three most essential built-in features of {discussed_skill} that you used in your project?"
                ]
            else:
                candidate_questions = [
                    f"To clarify and expand on your previous answer: could you give a simpler, specific example of a day-to-day challenge you resolved while working on '{primary_project}'?",
                    f"What was the simplest task you completed on '{primary_project}', and what did you learn from doing it?"
                ]

        # Case 3: Moderate Performance (6.0 <= Score < 8.0) -> Maintain Difficulty & Complementary Probe
        else:
            current_difficulty = last_diff
            score_disp = f"({last_score:.1f}/10)" if last_score is not None else "(baseline)"
            adaptive_reason = f"Maintained {current_difficulty} difficulty based on solid performance {score_disp}."

            if is_technical:
                candidate_questions = [
                    f"In your project '{primary_project}', walk me through how you connected {primary_skill} with {secondary_skill} to fulfill client requests.",
                    f"How did you structure tests and verify code quality for your {primary_skill} modules in '{primary_project}'?",
                    f"What approach did you take for state management and database consistency when building '{primary_project}'?"
                ]
            else:
                candidate_questions = [
                    f"Describe a technical roadblock you encountered while building '{primary_project}' and how you solved it.",
                    f"Tell me about a time you had to make a trade-off between writing perfect code and meeting a project deadline."
                ]

    # Initial or Fallback Question Bank
    if not candidate_questions:
        if is_technical:
            if current_difficulty == "Easy":
                candidate_questions.extend([
                    f"Explain how you used {primary_skill} in your project and what core concepts you applied.",
                    f"What are the main advantages of using {primary_skill} compared to other alternatives you considered?",
                    f"In your project '{primary_project}', how did you organize your codebase and manage dependencies?",
                    f"How do you handle basic error handling and debugging when working with {primary_skill}?",
                    f"Explain the purpose and usage of RESTful APIs in modern web applications."
                ])
            elif current_difficulty == "Medium":
                candidate_questions.extend([
                    f"Explain how you used {primary_skill} in your project.",
                    f"In your project '{primary_project}', walk me through how you implemented {primary_skill} and handled client requests.",
                    f"How did you design the data flow between {primary_skill} and {secondary_skill} in your architecture?",
                    f"What approach did you take for state management and database consistency when building '{primary_project}'?",
                    f"Explain how you ensure security and input validation when exposing APIs in {primary_skill}."
                ])
            else: # Hard
                candidate_questions.extend([
                    f"In your project '{primary_project}', how would you redesign the architecture to handle a 100x increase in concurrent traffic?",
                    f"Explain the internal concurrency and threading model of {primary_skill}, and how it impacts high-throughput systems.",
                    f"How would you diagnose and resolve a severe performance bottleneck or memory leak in a {primary_skill} backend?",
                    f"Discuss how you would implement distributed caching and database replication for an enterprise {target_role} service.",
                    f"Walk me through a zero-downtime deployment strategy for a service built using {primary_skill} and {secondary_skill}."
                ])
        else: # HR / Behavioral
            if current_difficulty == "Easy":
                candidate_questions.extend([
                    f"Tell me about yourself and what motivated you to pursue a career as a {target_role}.",
                    f"What was your personal favorite part of building your project '{primary_project}'?",
                    f"How do you usually approach learning a new tool or framework like {primary_skill} from scratch?",
                    f"Describe a time when you received constructive feedback on your code and how you addressed it."
                ])
            elif current_difficulty == "Medium":
                candidate_questions.extend([
                    f"Describe a significant technical roadblock you encountered while building '{primary_project}' and how you solved it.",
                    f"Tell me about a time you had to make a trade-off between writing perfect code and meeting a project deadline.",
                    f"How do you resolve differences in technical opinion when collaborating with peers on project architecture?",
                    f"Can you share an experience where a project requirement changed unexpectedly and how you adapted?"
                ])
            else: # Hard
                candidate_questions.extend([
                    f"Tell me about a project failure or technical mistake you made in '{primary_project}', and what fundamental lesson you learned from it.",
                    f"As a {target_role}, describe how you would prioritize technical debt versus urgent feature requests from stakeholders.",
                    f"Give an example of a high-pressure situation where a production or submission deadline was at risk, and how you led the solution.",
                    f"How do you evaluate and introduce new technologies into an existing team while minimizing risk?"
                ])

    # Filter out already asked questions to guarantee no repetitions
    unasked = [q for q in candidate_questions if q not in asked_questions]
    selected_question = unasked[0] if unasked else candidate_questions[0]

    return {
        "question_text": selected_question,
        "category": category,
        "difficulty": current_difficulty,
        "is_adaptive": is_adaptive,
        "adaptive_reason": adaptive_reason
    }


def generate_interview_question(
    interview_type: str,
    difficulty: str,
    target_role: str,
    question_index: int,
    total_questions: int,
    skills: List[str] = None,
    projects: List[str] = None,
    education: str = "",
    experience: str = "",
    asked_questions: List[str] = None,
    history: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generates interview question using the active AI service provider.
    """
    from app.services.ai_service import ai_service
    context = {
        "interview_type": interview_type,
        "difficulty": difficulty,
        "target_role": target_role,
        "question_index": question_index,
        "total_questions": total_questions,
        "skills": skills,
        "projects": projects,
        "education": education,
        "experience": experience,
        "asked_questions": asked_questions,
        "history": history
    }
    return ai_service.generate_question(context)
