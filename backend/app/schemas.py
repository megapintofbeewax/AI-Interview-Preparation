from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, model_validator

class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="User full name")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=6, description="Password (at least 6 characters)")
    confirm_password: str = Field(..., description="Password confirmation")

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    education: Optional[str] = Field("", max_length=255)
    target_role: Optional[str] = Field("", max_length=255)
    skills: Optional[str] = Field("")


class ProfileResponse(BaseModel):
    name: str
    email: str
    education: str
    target_role: str
    skills: str

    class Config:
        from_attributes = True


class ResumeResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    created_at: Optional[datetime] = None
    preview_text: Optional[str] = None
    message: Optional[str] = "Resume uploaded successfully."

    class Config:
        from_attributes = True


class ResumeAnalysisResponse(BaseModel):
    id: int
    resume_id: int
    skills: list[str]
    projects: list[str]
    education: str
    experience: str
    certifications: str
    technologies: list[str]
    keywords: list[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ResumeAnalysisUpdate(BaseModel):
    skills: Optional[list[str]] = None
    projects: Optional[list[str]] = None
    education: Optional[str] = None
    experience: Optional[str] = None
    certifications: Optional[str] = None
    technologies: Optional[list[str]] = None
    keywords: Optional[list[str]] = None


class InterviewCreate(BaseModel):
    target_role: str = Field(..., min_length=2, max_length=100)
    interview_type: str = Field(..., description="Technical, HR / Behavioral, or Mixed")
    difficulty: str = Field(..., description="Easy, Medium, or Hard")
    num_questions: int = Field(default=10, ge=1, le=20)


class InterviewResponse(BaseModel):
    id: int
    target_role: str
    interview_type: str
    difficulty: str
    num_questions: int
    status: str
    current_question_index: int
    overall_score: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class QuestionResponse(BaseModel):
    id: int
    interview_id: int
    question_index: int
    total_questions: int
    question_text: str
    category: str
    difficulty: str
    is_adaptive: Optional[bool] = False
    adaptive_reason: Optional[str] = ""

    class Config:
        from_attributes = True


class AnswerAudioSubmit(BaseModel):
    transcript: Optional[str] = ""
    duration_seconds: Optional[int] = 0


class AnswerResponse(BaseModel):
    id: int
    interview_id: int
    question_id: int
    transcript: str
    duration_seconds: int
    audio_path: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnswerDetailResponse(BaseModel):
    id: int
    interview_id: int
    question_id: int
    question_text: str
    transcript: str
    duration_seconds: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnswerUpdate(BaseModel):
    transcript: str = Field(..., min_length=1)


class EvaluationResponse(BaseModel):
    id: int
    interview_id: int
    question_id: int
    answer_id: int
    relevance_score: int
    technical_accuracy_score: int
    completeness_score: int
    clarity_score: int
    overall_score: float
    feedback: str
    question_text: Optional[str] = None
    question_index: Optional[int] = None
    total_questions: Optional[int] = None
    transcript: Optional[str] = None

    class Config:
        from_attributes = True


class PerformanceBreakdown(BaseModel):
    technical_accuracy: float
    relevance: float
    completeness: float
    clarity: float


class QuestionSummary(BaseModel):
    question_index: int
    question_text: str
    difficulty: str
    category: str
    transcript: Optional[str] = ""
    overall_score: Optional[float] = None


class InterviewResultsResponse(BaseModel):
    interview_id: int
    target_role: str
    interview_type: str
    difficulty: str
    overall_score: int
    performance: PerformanceBreakdown
    questions_answered: int
    total_questions: int
    status: str
    questions: Optional[List[QuestionSummary]] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RecurringWeakness(BaseModel):
    topic: str
    frequency: int
    note: str


class QuestionFeedbackItem(BaseModel):
    question_index: int
    question_text: str
    category: str
    difficulty: str
    overall_score: float
    transcript: str
    feedback: str


class InterviewFeedbackResponse(BaseModel):
    interview_id: int
    target_role: str
    interview_type: str
    overall_score: int
    strong_areas: List[str]
    weak_areas: List[str]
    recurring_weaknesses: List[RecurringWeakness]
    summary_notes: str
    question_feedbacks: List[QuestionFeedbackItem]

    class Config:
        from_attributes = True


class RecommendedSetup(BaseModel):
    target_role: str
    interview_type: str
    difficulty: str
    focus_topics: List[str]


class RecommendationItem(BaseModel):
    step_number: int
    title: str
    description: str
    category: str


class InterviewRecommendationsResponse(BaseModel):
    interview_id: int
    target_role: str
    overall_score: int
    recommendations: List[RecommendationItem]
    suggested_setup: RecommendedSetup
    summary_message: str

    class Config:
        from_attributes = True


class InterviewHistoryItem(BaseModel):
    id: int
    target_role: str
    interview_type: str
    difficulty: str
    overall_score: Optional[int] = None
    status: str
    num_questions: int
    questions_answered: int
    created_at: Optional[datetime] = None
    strong_areas: Optional[List[str]] = []
    weak_areas: Optional[List[str]] = []

    class Config:
        from_attributes = True


class InterviewHistoryResponse(BaseModel):
    total_interviews: int
    average_score: Optional[float] = None
    interviews: List[InterviewHistoryItem]

    class Config:
        from_attributes = True


class JobRoleResponse(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class SkillResponse(BaseModel):
    id: int
    name: str
    category: Optional[str] = None

    class Config:
        from_attributes = True
