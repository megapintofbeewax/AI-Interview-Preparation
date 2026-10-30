from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models import JobRole, Skill
from app.routers import auth, profile, resume, resume_analysis, interview

from sqlalchemy import text

# Initialize database tables
Base.metadata.create_all(bind=engine)
with engine.connect() as conn:
    try:
        res_q = conn.execute(text("PRAGMA table_info(questions);")).fetchall()
        col_names_q = [r[1] for r in res_q]
        if "is_adaptive" not in col_names_q:
            conn.execute(text("ALTER TABLE questions ADD COLUMN is_adaptive BOOLEAN DEFAULT 0;"))
        if "adaptive_reason" not in col_names_q:
            conn.execute(text("ALTER TABLE questions ADD COLUMN adaptive_reason VARCHAR(255) DEFAULT '';"))

        res_i = conn.execute(text("PRAGMA table_info(interviews);")).fetchall()
        col_names_i = [r[1] for r in res_i]
        if "strong_areas" not in col_names_i:
            conn.execute(text("ALTER TABLE interviews ADD COLUMN strong_areas TEXT DEFAULT '';"))
        if "weak_areas" not in col_names_i:
            conn.execute(text("ALTER TABLE interviews ADD COLUMN weak_areas TEXT DEFAULT '';"))
        if "recommendations" not in col_names_i:
            conn.execute(text("ALTER TABLE interviews ADD COLUMN recommendations TEXT DEFAULT '';"))
        conn.commit()
    except Exception:
        pass

def seed_database_catalog():
    db = SessionLocal()
    try:
        if db.query(JobRole).count() == 0:
            roles = [
                JobRole(name="Software Developer", category="Engineering", description="Core software engineering and application development."),
                JobRole(name="Frontend Developer", category="Engineering", description="Modern web interfaces, component architecture, and responsive UX."),
                JobRole(name="Backend Developer", category="Engineering", description="Server-side APIs, database management, and architecture."),
                JobRole(name="Full Stack Developer", category="Engineering", description="End-to-end full stack web architecture and microservices."),
                JobRole(name="Data Analyst", category="Data", description="Business intelligence, SQL querying, and data visualization."),
                JobRole(name="Data Scientist", category="Data", description="Statistical modeling, predictive analytics, and machine learning."),
                JobRole(name="Machine Learning Engineer", category="AI/ML", description="ML models, deep learning pipelines, and inference optimization."),
                JobRole(name="DevOps Engineer", category="Infrastructure", description="CI/CD pipelines, containerization, and automation."),
                JobRole(name="Cloud Engineer", category="Infrastructure", description="Cloud infrastructure, reliability, and security."),
                JobRole(name="Mobile App Developer", category="Engineering", description="Native and cross-platform mobile client development."),
            ]
            db.add_all(roles)
            db.commit()

        if db.query(Skill).count() == 0:
            skills = [
                Skill(name="Python", category="Language"),
                Skill(name="JavaScript", category="Language"),
                Skill(name="TypeScript", category="Language"),
                Skill(name="Java", category="Language"),
                Skill(name="C++", category="Language"),
                Skill(name="React", category="Frontend"),
                Skill(name="FastAPI", category="Backend"),
                Skill(name="Node.js", category="Backend"),
                Skill(name="SQL", category="Database"),
                Skill(name="MongoDB", category="Database"),
                Skill(name="Docker", category="DevOps"),
                Skill(name="Git", category="Tools"),
                Skill(name="Data Structures & Algorithms", category="Computer Science"),
                Skill(name="System Design", category="Architecture"),
                Skill(name="REST APIs", category="Web"),
            ]
            db.add_all(skills)
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

seed_database_catalog()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Clean, modular API for the AI Interview Preparation Platform",
    version="1.0.0",
)

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Preserves clean API HTTP exceptions with standard structured responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Sanitizes unexpected server errors so stack traces and sensitive details are never leaked."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Unable to complete request. Please try again."},
    )

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(self)"
    return response

# Include routers
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(resume.router)
app.include_router(resume_analysis.router)
app.include_router(interview.router)

@app.get("/api/health")
def health_check():
    """Service health check endpoint."""
    return {"status": "healthy", "service": settings.PROJECT_NAME}

@app.get("/api/test-error")
def test_error_endpoint():
    """Diagnostic endpoint to verify 500 exception sanitization."""
    raise RuntimeError("Simulated internal server exception with sensitive trace")

