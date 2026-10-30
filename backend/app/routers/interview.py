import os
import json
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    User, Resume, ResumeAnalysis, Interview, Question, Answer,
    Evaluation, JobRole, Skill, Feedback, Recommendation
)
from app.schemas import (
    InterviewCreate,
    InterviewResponse,
    QuestionResponse,
    AnswerAudioSubmit,
    AnswerResponse,
    AnswerDetailResponse,
    AnswerUpdate,
    EvaluationResponse,
    InterviewResultsResponse,
    InterviewFeedbackResponse,
    InterviewRecommendationsResponse,
    InterviewHistoryResponse,
)
from app.auth import get_current_user
from app.utils.sanitizer import sanitize_filename, sanitize_text
from app.services.question_generator import generate_interview_question
from app.services.answer_evaluator import evaluate_candidate_answer
from app.services.feedback_analyzer import analyze_interview_feedback
from app.services.recommendation_generator import generate_personalized_recommendations
from app.services.tts_service import tts_service

router = APIRouter(prefix="/api/interview", tags=["Interview"])

ALLOWED_TYPES = {"Technical", "HR / Behavioral", "Mixed"}
ALLOWED_DIFFICULTIES = {"Easy", "Medium", "Hard"}

POPULAR_ROLES = [
    "Software Developer",
    "Frontend Developer",
    "Backend Developer",
    "Full Stack Developer",
    "Data Analyst",
    "Data Scientist",
    "Machine Learning Engineer",
    "DevOps Engineer",
    "Cloud Engineer",
    "Mobile App Developer",
]

@router.get("/roles")
def get_popular_roles(db: Session = Depends(get_db)):
    """Retrieve standard suggested target job roles."""
    try:
        roles = db.query(JobRole).all()
        if roles:
            return {"roles": [r.name for r in roles]}
    except Exception:
        pass
    return {"roles": POPULAR_ROLES}

@router.get("/skills")
def get_popular_skills(db: Session = Depends(get_db)):
    """Retrieve standard suggested skills catalog."""
    try:
        skills = db.query(Skill).all()
        if skills:
            return {"skills": [{"id": s.id, "name": s.name, "category": s.category} for s in skills]}
    except Exception:
        pass
    return {"skills": []}

@router.get("/tts/voices")
def get_available_tts_voices():
    """Retrieve curated list of natural neural interviewer voices and active provider."""
    return {
        "provider": tts_service.provider,
        "default_voice": tts_service.default_voice,
        "voices": tts_service.list_curated_voices()
    }


@router.post("/start", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
def start_interview(
    config: InterviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Configure and initialize a new interview session.
    """
    if config.interview_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid interview type '{config.interview_type}'. Allowed types: {list(ALLOWED_TYPES)}"
        )

    if config.difficulty not in ALLOWED_DIFFICULTIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid difficulty '{config.difficulty}'. Allowed: {list(ALLOWED_DIFFICULTIES)}"
        )

    # Link latest resume if candidate uploaded one
    latest_resume = db.query(Resume).filter(Resume.user_id == current_user.id).order_by(Resume.id.desc()).first()
    resume_id = latest_resume.id if latest_resume else None

    # Create interview session
    new_interview = Interview(
        user_id=current_user.id,
        resume_id=resume_id,
        target_role=config.target_role.strip(),
        interview_type=config.interview_type,
        difficulty=config.difficulty,
        num_questions=config.num_questions,
        status="in_progress",
        current_question_index=1,
    )

    db.add(new_interview)
    db.commit()
    db.refresh(new_interview)

    return new_interview

@router.get("/history", response_model=InterviewHistoryResponse)
def get_user_interview_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve the candidate's complete chronological interview history.
    """
    interviews = db.query(Interview).filter(
        Interview.user_id == current_user.id
    ).order_by(Interview.created_at.desc()).all()

    items = []
    scores = []
    for inv in interviews:
        eval_count = db.query(Evaluation).filter(Evaluation.interview_id == inv.id).count()

        strong = []
        weak = []
        if inv.strong_areas:
            try:
                strong = json.loads(inv.strong_areas)
            except Exception:
                pass
        if inv.weak_areas:
            try:
                weak = json.loads(inv.weak_areas)
            except Exception:
                pass

        if inv.overall_score is not None:
            scores.append(inv.overall_score)

        items.append({
            "id": inv.id,
            "target_role": inv.target_role,
            "interview_type": inv.interview_type,
            "difficulty": inv.difficulty,
            "overall_score": inv.overall_score,
            "status": inv.status,
            "num_questions": inv.num_questions,
            "questions_answered": eval_count,
            "created_at": inv.created_at,
            "strong_areas": strong,
            "weak_areas": weak
        })

    avg_score = round(sum(scores) / len(scores), 1) if scores else None

    return {
        "total_interviews": len(items),
        "average_score": avg_score,
        "interviews": items
    }

@router.get("/{interview_id}", response_model=InterviewResponse)
def get_interview(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve interview session details by ID.
    """
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found."
        )

    return interview

@router.get("/{interview_id}/current-question", response_model=QuestionResponse)
def get_current_question(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve or generate the active question for the current interview session.
    """
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found."
        )

    # Check if question for current index already generated
    current_q = db.query(Question).filter(
        Question.interview_id == interview.id,
        Question.question_index == interview.current_question_index
    ).first()

    if not current_q:
        # Build history of previous questions, answers, and evaluations
        prior_questions = db.query(Question).filter(
            Question.interview_id == interview.id,
            Question.question_index < interview.current_question_index
        ).order_by(Question.question_index.asc()).all()

        history = []
        asked_questions = []
        for pq in prior_questions:
            asked_questions.append(pq.question_text)
            ans = db.query(Answer).filter(
                Answer.question_id == pq.id,
                Answer.interview_id == interview.id
            ).order_by(Answer.id.desc()).first()
            eval_rec = db.query(Evaluation).filter(Evaluation.question_id == pq.id).first() if ans else None
            history.append({
                "question_index": pq.question_index,
                "question_text": pq.question_text,
                "difficulty": pq.difficulty,
                "category": pq.category,
                "transcript": ans.transcript if ans else "",
                "overall_score": eval_rec.overall_score if eval_rec else None,
                "relevance_score": eval_rec.relevance_score if eval_rec else None,
                "technical_accuracy_score": eval_rec.technical_accuracy_score if eval_rec else None,
                "completeness_score": eval_rec.completeness_score if eval_rec else None,
                "clarity_score": eval_rec.clarity_score if eval_rec else None,
                "feedback": eval_rec.feedback if eval_rec else ""
            })

        # Load resume analysis skills & projects
        skills = []
        projects = []
        if interview.resume_id:
            analysis = db.query(ResumeAnalysis).filter(ResumeAnalysis.resume_id == interview.resume_id).first()
            if analysis:
                try:
                    skills = json.loads(analysis.skills) if analysis.skills else []
                    projects = json.loads(analysis.projects) if analysis.projects else []
                except Exception:
                    pass

        generated = generate_interview_question(
            interview_type=interview.interview_type,
            difficulty=interview.difficulty,
            target_role=interview.target_role,
            question_index=interview.current_question_index,
            total_questions=interview.num_questions,
            skills=skills,
            projects=projects,
            asked_questions=asked_questions,
            history=history
        )

        current_q = Question(
            interview_id=interview.id,
            question_index=interview.current_question_index,
            question_text=generated["question_text"],
            category=generated["category"],
            difficulty=generated["difficulty"],
            is_adaptive=generated.get("is_adaptive", False),
            adaptive_reason=generated.get("adaptive_reason", "")
        )
        db.add(current_q)
        db.commit()
        db.refresh(current_q)

    return {
        "id": current_q.id,
        "interview_id": current_q.interview_id,
        "question_index": current_q.question_index,
        "total_questions": interview.num_questions,
        "question_text": current_q.question_text,
        "category": current_q.category or "Technical",
        "difficulty": current_q.difficulty or interview.difficulty,
        "is_adaptive": getattr(current_q, "is_adaptive", False),
        "adaptive_reason": getattr(current_q, "adaptive_reason", "")
    }

@router.post("/{interview_id}/submit-answer", response_model=AnswerResponse, status_code=status.HTTP_201_CREATED)
def submit_answer(
    interview_id: int,
    submission: AnswerAudioSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save the recorded answer transcript for the active question.
    """
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found."
        )

    current_q = db.query(Question).filter(
        Question.interview_id == interview.id,
        Question.question_index == interview.current_question_index
    ).first()

    if not current_q:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active question found to answer."
        )

    # Save answer record
    answer = Answer(
        interview_id=interview.id,
        question_id=current_q.id,
        user_id=current_user.id,
        transcript=submission.transcript.strip() if submission.transcript else "",
        duration_seconds=submission.duration_seconds or 0
    )
    db.add(answer)
    db.commit()
    db.refresh(answer)

    return answer

@router.post("/{interview_id}/submit-audio", response_model=AnswerResponse, status_code=status.HTTP_201_CREATED)
async def submit_audio(
    interview_id: int,
    file: Optional[UploadFile] = File(None),
    transcript: Optional[str] = Form(""),
    duration_seconds: Optional[int] = Form(0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Accept recorded audio file upload or streaming transcript for Speech-to-Text answer processing.
    """
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found."
        )

    current_q = db.query(Question).filter(
        Question.interview_id == interview.id,
        Question.question_index == interview.current_question_index
    ).first()

    if not current_q:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active question found to answer."
        )

    audio_path = None
    if file and file.filename:
        _, ext = os.path.splitext(file.filename.lower())
        allowed_audio = {".wav", ".mp3", ".webm", ".ogg", ".m4a"}
        if ext and ext not in allowed_audio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported audio format '{ext}'. Allowed: wav, mp3, webm, ogg, m4a."
            )
        content = await file.read()
        if len(content) > 25 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio file exceeds 25 MB size limit."
            )
        os.makedirs("uploads/audio", exist_ok=True)
        safe_name = sanitize_filename(file.filename)
        filename = f"ans_{interview.id}_{current_q.id}_{int(datetime.now().timestamp())}_{safe_name}"
        audio_path = os.path.join("uploads/audio", filename)
        with open(audio_path, "wb") as f:
            f.write(content)

    final_transcript = sanitize_text(transcript.strip()) if transcript else ""
    if not final_transcript and audio_path:
        final_transcript = f"Candidate provided voice response for question {current_q.question_index}."

    answer = Answer(
        interview_id=interview.id,
        question_id=current_q.id,
        user_id=current_user.id,
        transcript=final_transcript,
        audio_path=audio_path,
        duration_seconds=duration_seconds or 0
    )
    db.add(answer)
    db.commit()
    db.refresh(answer)

    return answer

@router.delete("/{interview_id}/audio", status_code=status.HTTP_200_OK)
def purge_interview_audio(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Audio Privacy Feature: Purges physical audio recordings from server disk for this session.
    Preserves text transcripts, evaluation metrics, and scores.
    """
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found."
        )

    answers = db.query(Answer).filter(
        Answer.interview_id == interview.id,
        Answer.user_id == current_user.id
    ).all()

    purged_count = 0
    for ans in answers:
        if ans.audio_path and os.path.exists(ans.audio_path):
            try:
                os.remove(ans.audio_path)
                purged_count += 1
            except Exception:
                pass
        ans.audio_path = None

    db.commit()
    return {
        "status": "success",
        "message": f"Purged {purged_count} audio recording(s). Transcripts and evaluations retained.",
        "purged_count": purged_count
    }

@router.get("/{interview_id}/question/{question_id}/tts-text")
def get_question_tts_text(
    interview_id: int,
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve pronunciation-optimized text for Text-to-Speech synthesis.
    """
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found."
        )

    question = db.query(Question).filter(
        Question.id == question_id,
        Question.interview_id == interview.id
    ).first()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found."
        )

    cleaned = question.question_text.replace("`", "").replace("*", "").strip()
    return {
        "question_id": question.id,
        "question_index": question.question_index,
        "tts_text": cleaned,
        "lang": "en-US",
        "pitch": 1.0,
        "rate": 0.95
    }

@router.get("/{interview_id}/question/{question_id}/audio")
async def get_question_audio(
    interview_id: int,
    question_id: int,
    voice: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate or stream neural human-like speech audio (MP3) for the given interview question.
    Leverages Microsoft Edge Neural TTS (or ElevenLabs if configured) with deterministic SHA-256 caching.
    """
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found."
        )

    question = db.query(Question).filter(
        Question.id == question_id,
        Question.interview_id == interview.id
    ).first()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found."
        )

    try:
        audio_file_path = await tts_service.generate_speech(
            text=question.question_text,
            voice=voice
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech synthesis error: {str(exc)}"
        )

    if not os.path.exists(audio_file_path):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Synthesized audio file was not found on disk."
        )

    return FileResponse(
        path=audio_file_path,
        media_type="audio/mpeg",
        filename=f"interview_{interview_id}_q_{question_id}.mp3",
        headers={
            "Cache-Control": "public, max-age=86400, immutable",
            "Accept-Ranges": "bytes"
        }
    )

@router.get("/{interview_id}/answer/{answer_id}", response_model=AnswerDetailResponse)
def get_answer_detail(
    interview_id: int,
    answer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve specific transcribed answer with its associated question text.
    """
    answer = db.query(Answer).filter(
        Answer.id == answer_id,
        Answer.interview_id == interview_id,
        Answer.user_id == current_user.id
    ).first()

    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer record not found."
        )

    question = db.query(Question).filter(Question.id == answer.question_id).first()
    question_text = question.question_text if question else ""

    return {
        "id": answer.id,
        "interview_id": answer.interview_id,
        "question_id": answer.question_id,
        "question_text": question_text,
        "transcript": answer.transcript or "",
        "duration_seconds": answer.duration_seconds or 0,
        "created_at": answer.created_at
    }

@router.put("/{interview_id}/answer/{answer_id}", response_model=AnswerDetailResponse)
def update_answer_transcript(
    interview_id: int,
    answer_id: int,
    update: AnswerUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update or correct the transcribed answer text prior to AI evaluation.
    """
    answer = db.query(Answer).filter(
        Answer.id == answer_id,
        Answer.interview_id == interview_id,
        Answer.user_id == current_user.id
    ).first()

    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer record not found."
        )

    answer.transcript = sanitize_text(update.transcript.strip())
    db.commit()
    db.refresh(answer)

    question = db.query(Question).filter(Question.id == answer.question_id).first()
    question_text = question.question_text if question else ""

    return {
        "id": answer.id,
        "interview_id": answer.interview_id,
        "question_id": answer.question_id,
        "question_text": question_text,
        "transcript": answer.transcript or "",
        "duration_seconds": answer.duration_seconds or 0,
        "created_at": answer.created_at
    }

@router.post("/{interview_id}/answer/{answer_id}/evaluate", response_model=EvaluationResponse)
def evaluate_answer_endpoint(
    interview_id: int,
    answer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Run AI NLP evaluation on the candidate's answer and return scores and practice feedback.
    """
    answer = db.query(Answer).filter(
        Answer.id == answer_id,
        Answer.interview_id == interview_id,
        Answer.user_id == current_user.id
    ).first()

    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer record not found."
        )

    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    question = db.query(Question).filter(Question.id == answer.question_id).first()

    # Check if already evaluated
    evaluation = db.query(Evaluation).filter(Evaluation.answer_id == answer.id).first()

    if not evaluation:
        eval_result = evaluate_candidate_answer(
            question_text=question.question_text if question else "",
            answer_transcript=answer.transcript or "",
            target_role=interview.target_role if interview else "Software Developer",
            difficulty=interview.difficulty if interview else "Medium"
        )

        evaluation = Evaluation(
            interview_id=interview.id,
            question_id=question.id,
            answer_id=answer.id,
            relevance_score=eval_result["relevance_score"],
            technical_accuracy_score=eval_result["technical_accuracy_score"],
            completeness_score=eval_result["completeness_score"],
            clarity_score=eval_result["clarity_score"],
            overall_score=eval_result["overall_score"],
            feedback=eval_result["feedback"]
        )
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)

    return {
        "id": evaluation.id,
        "interview_id": evaluation.interview_id,
        "question_id": evaluation.question_id,
        "answer_id": evaluation.answer_id,
        "relevance_score": evaluation.relevance_score,
        "technical_accuracy_score": evaluation.technical_accuracy_score,
        "completeness_score": evaluation.completeness_score,
        "clarity_score": evaluation.clarity_score,
        "overall_score": evaluation.overall_score,
        "feedback": evaluation.feedback,
        "question_text": question.question_text if question else "",
        "question_index": question.question_index if question else 1,
        "total_questions": interview.num_questions if interview else 10,
        "transcript": answer.transcript or ""
    }

@router.get("/{interview_id}/answer/{answer_id}/evaluation", response_model=EvaluationResponse)
def get_answer_evaluation(
    interview_id: int,
    answer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve or compute evaluation for the specific answer.
    """
    return evaluate_answer_endpoint(interview_id=interview_id, answer_id=answer_id, current_user=current_user, db=db)

@router.post("/{interview_id}/advance-question")
def advance_to_next_question(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Advance interview to the next question index or complete the interview if at the end.
    """
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found."
        )

    if interview.current_question_index < interview.num_questions:
        interview.current_question_index += 1
    else:
        interview.status = "completed"

    db.commit()
    db.refresh(interview)

    return {
        "current_question_index": interview.current_question_index,
        "total_questions": interview.num_questions,
        "status": interview.status,
        "completed": interview.status == "completed"
    }

@router.get("/{interview_id}/results", response_model=InterviewResultsResponse)
def get_interview_results(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve the aggregated performance results and summary for a completed interview.
    """
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found."
        )

    # Fetch all questions and evaluations
    questions = db.query(Question).filter(
        Question.interview_id == interview.id
    ).order_by(Question.question_index.asc()).all()

    evaluations = db.query(Evaluation).filter(
        Evaluation.interview_id == interview.id
    ).all()

    questions_summary = []
    for q in questions:
        ans = db.query(Answer).filter(
            Answer.question_id == q.id,
            Answer.interview_id == interview.id
        ).order_by(Answer.id.desc()).first()
        ev = db.query(Evaluation).filter(Evaluation.question_id == q.id).first() if ans else None
        questions_summary.append({
            "question_index": q.question_index,
            "question_text": q.question_text,
            "difficulty": q.difficulty or "Medium",
            "category": q.category or "Technical",
            "transcript": ans.transcript if ans else "",
            "overall_score": ev.overall_score if ev else None
        })

    num_evals = len(evaluations)
    if num_evals > 0:
        avg_relevance = round(sum(e.relevance_score for e in evaluations) / num_evals, 1)
        avg_technical = round(sum(e.technical_accuracy_score for e in evaluations) / num_evals, 1)
        avg_completeness = round(sum(e.completeness_score for e in evaluations) / num_evals, 1)
        avg_clarity = round(sum(e.clarity_score for e in evaluations) / num_evals, 1)
        avg_overall = sum(e.overall_score for e in evaluations) / num_evals
        overall_100 = int(round(avg_overall * 10))
    else:
        avg_relevance = 0.0
        avg_technical = 0.0
        avg_completeness = 0.0
        avg_clarity = 0.0
        overall_100 = 0

    # Persist overall score and mark status as completed
    interview.overall_score = overall_100
    interview.status = "completed"
    db.commit()
    db.refresh(interview)

    return {
        "interview_id": interview.id,
        "target_role": interview.target_role,
        "interview_type": interview.interview_type,
        "difficulty": interview.difficulty,
        "overall_score": overall_100,
        "performance": {
            "technical_accuracy": avg_technical,
            "relevance": avg_relevance,
            "completeness": avg_completeness,
            "clarity": avg_clarity
        },
        "questions_answered": num_evals,
        "total_questions": interview.num_questions,
        "status": interview.status,
        "questions": questions_summary,
        "created_at": interview.created_at
    }

@router.get("/{interview_id}/feedback", response_model=InterviewFeedbackResponse)
def get_interview_feedback(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve detailed strong areas, weak areas, cross-interview recurring weaknesses,
    and question-by-question feedback.
    """
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found."
        )

    analysis = analyze_interview_feedback(
        interview_id=interview.id,
        user_id=current_user.id,
        db=db
    )

    return {
        "interview_id": interview.id,
        "target_role": interview.target_role,
        "interview_type": interview.interview_type,
        "overall_score": interview.overall_score or 75,
        "strong_areas": analysis["strong_areas"],
        "weak_areas": analysis["weak_areas"],
        "recurring_weaknesses": analysis["recurring_weaknesses"],
        "summary_notes": analysis["summary_notes"],
        "question_feedbacks": analysis["question_feedbacks"]
    }

@router.get("/{interview_id}/recommendations", response_model=InterviewRecommendationsResponse)
def get_interview_recommendations(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve personalized practice recommendations and suggested next interview setup.
    """
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found."
        )

    rec_data = generate_personalized_recommendations(
        interview_id=interview.id,
        user_id=current_user.id,
        db=db
    )

    return {
        "interview_id": interview.id,
        "target_role": interview.target_role,
        "overall_score": interview.overall_score or 75,
        "recommendations": rec_data["recommendations"],
        "suggested_setup": rec_data["suggested_setup"],
        "summary_message": rec_data["summary_message"]
    }
