import os
import time
import re
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Resume
from app.schemas import ResumeResponse
from app.auth import get_current_user
from app.services.resume_parser import extract_text_from_file

router = APIRouter(prefix="/api/resume", tags=["Resume"])

# Dedicated uploads directory
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB max per Master Prompt specification

from app.utils.sanitizer import sanitize_filename

@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and securely store resume file (PDF or DOCX), extracting readable text content.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file selected."
        )

    _, ext = os.path.splitext(file.filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Only PDF and DOCX files are supported."
        )

    file_type = "pdf" if ext == ".pdf" else "docx"
    clean_name = sanitize_filename(file.filename)
    unique_filename = f"user_{current_user.id}_{int(time.time())}_{clean_name}"
    saved_file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Read and validate file size
    contents = await file.read()
    file_size = len(contents)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty."
        )

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 5 MB maximum limit."
        )

    # Save to disk
    with open(saved_file_path, "wb") as f:
        f.write(contents)

    # Extract text content
    extracted_text = extract_text_from_file(saved_file_path, file_type)

    # Find existing or create new resume record
    resume_record = db.query(Resume).filter(Resume.user_id == current_user.id).order_by(Resume.id.desc()).first()
    if not resume_record:
        resume_record = Resume(user_id=current_user.id)
        db.add(resume_record)

    resume_record.filename = file.filename
    resume_record.file_path = saved_file_path
    resume_record.file_type = file_type
    resume_record.file_size = file_size
    resume_record.raw_text = extracted_text

    db.commit()
    db.refresh(resume_record)

    preview = (extracted_text[:300] + "...") if len(extracted_text) > 300 else extracted_text

    return {
        "id": resume_record.id,
        "filename": resume_record.filename,
        "file_type": resume_record.file_type,
        "file_size": resume_record.file_size,
        "created_at": resume_record.created_at,
        "preview_text": preview,
        "message": "Resume uploaded successfully."
    }

@router.get("/latest", response_model=ResumeResponse)
def get_latest_resume(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve the latest uploaded resume for the current user."""
    resume_record = db.query(Resume).filter(Resume.user_id == current_user.id).order_by(Resume.id.desc()).first()
    if not resume_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume has been uploaded yet."
        )

    preview = (resume_record.raw_text[:300] + "...") if resume_record.raw_text and len(resume_record.raw_text) > 300 else (resume_record.raw_text or "")

    return {
        "id": resume_record.id,
        "filename": resume_record.filename,
        "file_type": resume_record.file_type,
        "file_size": resume_record.file_size,
        "created_at": resume_record.created_at,
        "preview_text": preview,
        "message": "Resume found."
    }
