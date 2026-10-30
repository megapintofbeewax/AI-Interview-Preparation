from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Profile
from app.schemas import ProfileResponse, ProfileUpdate
from app.auth import get_current_user

router = APIRouter(prefix="/api/profile", tags=["Profile"])

@router.get("", response_model=ProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve profile for currently authenticated user."""
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return {
        "name": current_user.name,
        "email": current_user.email,
        "education": profile.education or "",
        "target_role": profile.target_role or "",
        "skills": profile.skills or "",
    }

from app.utils.sanitizer import sanitize_text

@router.put("", response_model=ProfileResponse)
def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update profile information for currently authenticated user with sanitization."""
    # Update name if provided
    if profile_data.name is not None and profile_data.name.strip():
        current_user.name = sanitize_text(profile_data.name.strip())

    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)

    if profile_data.education is not None:
        profile.education = sanitize_text(profile_data.education.strip())
    if profile_data.target_role is not None:
        profile.target_role = sanitize_text(profile_data.target_role.strip())
    if profile_data.skills is not None:
        profile.skills = sanitize_text(profile_data.skills.strip())

    db.commit()
    db.refresh(current_user)
    db.refresh(profile)

    return {
        "name": current_user.name,
        "email": current_user.email,
        "education": profile.education or "",
        "target_role": profile.target_role or "",
        "skills": profile.skills or "",
    }
