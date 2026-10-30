import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Resume, ResumeAnalysis, Profile
from app.schemas import ResumeAnalysisResponse, ResumeAnalysisUpdate
from app.auth import get_current_user
from app.services.resume_analyzer import analyze_resume_text
from app.utils.sanitizer import sanitize_text

router = APIRouter(prefix="/api/resume-analysis", tags=["Resume Analysis"])

def serialize_analysis(record: ResumeAnalysis) -> dict:
    """Helper to convert db record to schema dict."""
    def parse_list(val):
        if not val:
            return []
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
        return [item.strip() for item in val.split(",") if item.strip()]

    return {
        "id": record.id,
        "resume_id": record.resume_id,
        "skills": parse_list(record.skills),
        "projects": parse_list(record.projects),
        "education": record.education or "",
        "experience": record.experience or "",
        "certifications": record.certifications or "",
        "technologies": parse_list(record.technologies),
        "keywords": parse_list(record.keywords),
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }

@router.post("/analyze", response_model=ResumeAnalysisResponse)
def trigger_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Run NLP extraction on current user's latest resume and persist results.
    """
    latest_resume = db.query(Resume).filter(Resume.user_id == current_user.id).order_by(Resume.id.desc()).first()
    if not latest_resume:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No resume found. Please upload a resume first."
        )

    # Perform NLP analysis
    extracted = analyze_resume_text(latest_resume.raw_text or "")

    analysis_record = db.query(ResumeAnalysis).filter(ResumeAnalysis.resume_id == latest_resume.id).first()
    if not analysis_record:
        analysis_record = ResumeAnalysis(
            resume_id=latest_resume.id,
            user_id=current_user.id
        )
        db.add(analysis_record)

    analysis_record.skills = json.dumps(extracted["skills"])
    analysis_record.projects = json.dumps(extracted["projects"])
    analysis_record.education = extracted["education"]
    analysis_record.experience = extracted["experience"]
    analysis_record.certifications = extracted["certifications"]
    analysis_record.technologies = json.dumps(extracted["technologies"])
    analysis_record.keywords = json.dumps(extracted["keywords"])

    # Synchronize with profile if profile fields are empty
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if profile:
        if not profile.skills and extracted["skills"]:
            profile.skills = ", ".join(extracted["skills"][:6])
        if not profile.education and extracted["education"]:
            profile.education = extracted["education"]

    db.commit()
    db.refresh(analysis_record)

    return serialize_analysis(analysis_record)

@router.get("", response_model=ResumeAnalysisResponse)
def get_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get latest resume analysis for current user, auto-analyzing if not yet performed.
    """
    latest_resume = db.query(Resume).filter(Resume.user_id == current_user.id).order_by(Resume.id.desc()).first()
    if not latest_resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume found. Please upload a resume first."
        )

    analysis_record = db.query(ResumeAnalysis).filter(ResumeAnalysis.resume_id == latest_resume.id).first()
    if not analysis_record:
        # Auto-trigger analysis
        return trigger_analysis(current_user=current_user, db=db)

    return serialize_analysis(analysis_record)

@router.put("", response_model=ResumeAnalysisResponse)
def update_analysis(
    update_data: ResumeAnalysisUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Allow user to review and correct any extracted information.
    """
    latest_resume = db.query(Resume).filter(Resume.user_id == current_user.id).order_by(Resume.id.desc()).first()
    if not latest_resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume found to update."
        )

    analysis_record = db.query(ResumeAnalysis).filter(ResumeAnalysis.resume_id == latest_resume.id).first()
    if not analysis_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analysis found to update."
        )

    if update_data.skills is not None:
        analysis_record.skills = json.dumps([sanitize_text(s) for s in update_data.skills])
    if update_data.projects is not None:
        analysis_record.projects = json.dumps([sanitize_text(p) for p in update_data.projects])
    if update_data.education is not None:
        analysis_record.education = sanitize_text(update_data.education.strip())
    if update_data.experience is not None:
        analysis_record.experience = sanitize_text(update_data.experience.strip())
    if update_data.certifications is not None:
        analysis_record.certifications = sanitize_text(update_data.certifications.strip())
    if update_data.technologies is not None:
        analysis_record.technologies = json.dumps([sanitize_text(t) for t in update_data.technologies])
    if update_data.keywords is not None:
        analysis_record.keywords = json.dumps([sanitize_text(k) for k in update_data.keywords])

    db.commit()
    db.refresh(analysis_record)

    return serialize_analysis(analysis_record)
