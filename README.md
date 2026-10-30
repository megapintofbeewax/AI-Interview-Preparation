# AI Interview Preparation Platform

[![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/megapintofbeewax/AI-Interview-Preparation)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React_18-61DAFB?logo=react)](https://react.dev)
[![Tailwind CSS](https://img.shields.io/badge/UI-Tailwind_CSS-38B2AC?logo=tailwind-css)](https://tailwindcss.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An end-to-end, full-stack AI-powered interview preparation web platform. The system conducts realistic, voice-interactive technical and behavioral mock interviews tailored to the candidate's actual resume, evaluates responses across a 5-dimensional industrial rubric, and delivers diagnostic performance feedback with personalized study roadmaps.

**Repository URL:** [https://github.com/megapintofbeewax/AI-Interview-Preparation](https://github.com/megapintofbeewax/AI-Interview-Preparation)

---

## Table of Contents

- [Overview & Architecture](#overview--architecture)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Local Installation & Setup](#local-installation--setup)
  - [1. Clone Repository](#1-clone-repository)
  - [2. Backend Setup](#2-backend-setup)
  - [3. Frontend Setup](#3-frontend-setup)
- [Environment Configuration](#environment-configuration)
- [Database & Runtime Data Handling](#database--runtime-data-handling)
- [Running the Platform](#running-the-platform)
  - [Quick Start Scripts (Windows)](#quick-start-scripts-windows)
  - [Manual Execution (Cross-Platform)](#manual-execution-cross-platform)
  - [Service Endpoints](#service-endpoints)
- [Running Tests & Verifications](#running-tests--verifications)
- [Project Directory Structure](#project-directory-structure)
- [Security & Privacy Features](#security--privacy-features)
- [Known Limitations](#known-limitations)
- [License](#license)

---

## Overview & Architecture

Modern placement and technical interviews require verbal articulation, dynamic problem solving, and defending claims made on a resume. Traditional preparation tools focus either on silent coding puzzles or open-ended chat prompts.

This platform bridges that gap by implementing a modular full-lifecycle pipeline:

```
[Candidate Resume (PDF/DOCX)]
              │
              ▼
   [Resume Parsing Engine] ──────► [Extracted Skills, Tech Stack, & Projects]
                                                  │
                                                  ▼
                                      [Question Generator]
                                                  │
                                                  ▼
                                      [Live Voice Interview]
                                       (Neural TTS + STT HUD)
                                                  │
                                                  ▼
                                   [Candidate Verification Layer]
                                  (Inspect & Correct Transcript)
                                                  │
                                                  ▼
                                     [5-Axis Rubric Evaluator]
                                                  │
                                                  ▼
                             [Analytics & Personalized Study Roadmap]
```

---

## Key Features

- **Authentication & User Management:** User registration, bcrypt password hashing, JWT session authentication (24-hour expiration), protected React routes, and profile management.
- **Automated Resume Parsing:** Upload `.pdf` and `.docx` resumes with MIME-type and size validation. Extracts structured skills, projects, work tenure, and domain keywords using `pypdf`, `python-docx`, and NLP extraction routines.
- **Pre-Seeded Catalogs:** 10 pre-configured industry job roles (Software Developer, Frontend, Backend, Full Stack, Data Analyst, Data Scientist, ML Engineer, DevOps, Cloud Engineer, Mobile Developer) and categorized technical competencies.
- **Configurable Interview Setup:** Customizable target role, difficulty level (Easy, Medium, Hard), interview track (Technical, HR, Mixed), and question volume.
- **Multimodal Live Interview HUD:** Spoken questions using high-fidelity neural audio synthesis, audio waveform indicators, response timers, and browser-based Web Speech API capture.
- **Candidate Verification Layer (`/interview/answer`):** A human-in-the-loop agency screen displaying the transcribed answer with confidence indicators. Allows candidates to correct misheard technical acronyms (e.g., *FastAPI*, *Kubernetes*) or re-record before grading.
- **Adaptive Difficulty Escalation:** Dynamic question generator that scales difficulty up into architecture/edge cases on strong answers, or recalibrates to fundamentals when candidates struggle.
- **5-Dimensional Objective Rubric Evaluation:** Grades responses across five core industrial competencies:
  1. *Technical Accuracy* (correctness, architecture, complexity)
  2. *Relevance* (direct adherence to prompt)
  3. *Completeness* (covering edge cases and boundary conditions)
  4. *Clarity* (structural logic, STAR technique)
  5. *Communication* (articulation, terminology, cadence)
  Includes granular numerical scores, constructive critique, and reference model answers.
- **Actionable Performance Analytics:** Comprehensive session results showing composite scores (out of 100), dimensional breakdown charts, identified strengths, and priority weakness tags.
- **Personalized Remediation Roadmaps:** Automatically synthesizes topic-specific study guides, external references, and practice drills targeting identified weak areas.
- **Interview History Archive:** Track previous interview attempts, historical scores, dates, and progress over time.
- **Biometric Audio Privacy:** Built-in cleanup endpoint (`DELETE /api/interview/{id}/audio`) to purge candidate audio recordings upon session completion.

---

## Technology Stack

### Backend
- **Framework:** FastAPI (Python 3.11+) with Uvicorn ASGI server
- **Database & ORM:** SQLite with SQLAlchemy ORM (WAL mode enabled)
- **Data Validation & Settings:** Pydantic v2
- **Authentication:** PyJWT, Passlib with bcrypt
- **Document Processing:** `pypdf` (PDF extraction) and `python-docx` (DOCX extraction)
- **Speech Synthesis:** `edge-tts` (Microsoft Edge Neural Voice synthesis, free tier) with SHA-256 local audio cache
- **External AI Providers (Configurable):**
  - **Rule-Based NLP Provider:** Deterministic, zero-dependency offline provider for resume analysis, question generation, rubric grading, and roadmaps.
  - **Gemini AI Provider:** Optional cloud integration using Google Gemini 1.5 Flash REST API with graceful automated fallback to rule-based NLP on timeout or quota limit.
  - **ElevenLabs:** Optional premium voice provider with automatic fallback to Edge-TTS.

### Frontend
- **Framework:** React 18 with Vite
- **Routing:** React Router DOM v6 with route guards
- **Styling:** Tailwind CSS v3 with Lucide React icons
- **Audio & Speech:** Browser Web Speech API (`webkitSpeechRecognition`), Web Audio API, and HTML5 Audio
- **Visuals:** GPU-accelerated living background canvas with WCAG reduced-motion compliance

---

## Prerequisites

Before setting up the project locally, ensure you have:
- **Python:** Version 3.10 or higher (tested on 3.11 and 3.12)
- **Node.js:** Version 18.0.0 or higher
- **npm:** Version 9.0.0 or higher
- **Browser:** Google Chrome or Microsoft Edge (recommended for native Web Speech API microphone recognition)

---

## Local Installation & Setup

### 1. Clone Repository

```bash
git clone https://github.com/megapintofbeewax/AI-Interview-Preparation.git
cd AI-Interview-Preparation
```

---

### 2. Backend Setup

#### On Windows (PowerShell):
```powershell
# Create Python virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r backend\requirements.txt
```

#### On Linux / macOS (bash/zsh):
```bash
# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt
```

---

### 3. Frontend Setup

From the project root:

```bash
cd frontend
npm install
cd ..
```

---

## Environment Configuration

The application works out-of-the-box in local development with safe defaults (deterministic rule-based AI provider, local SQLite database, and free Edge Neural TTS).

To customize settings or enable optional cloud providers:

1. Copy the example configuration file:
   ```bash
   cp backend/.env.example backend/.env
   ```
   *(On Windows PowerShell: `Copy-Item backend\.env.example backend\.env`)*

2. Configure environment variables in `backend/.env`:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `SECRET_KEY` | *(dev fallback)* | Secret key for JWT signing. **Generate a strong random key for production:**<br>`python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | `sqlite:///./ai_interview.db` | SQLAlchemy database connection string. |
| `TTS_PROVIDER` | `edge-tts` | Text-to-speech engine (`edge-tts` or `elevenlabs`). |
| `TTS_VOICE` | `en-US-JennyNeural` | Voice identifier (`en-US-JennyNeural`, `en-US-GuyNeural`, `en-US-AriaNeural`, `en-US-ChristopherNeural`, etc.). |
| `TTS_RATE` | `+0%` | Conversational speech rate adjustment. |
| `TTS_PITCH` | `+0Hz` | Pitch adjustment. |
| `ELEVENLABS_API_KEY` | *(empty)* | Optional ElevenLabs API key. If unset or quota is exceeded, Edge-TTS is used. |
| `ELEVENLABS_VOICE_ID` | `21m00Tcm4TlvDq8ikWAM` | Optional ElevenLabs voice identifier. |
| `GEMINI_API_KEY` | *(empty)* | Optional Google Gemini API key. If empty, the platform runs offline with `RuleBasedNLPProvider`. |

---

## Database & Runtime Data Handling

- **Database Initialization:** The SQLite database (`ai_interview.db`) is automatically initialized and migrated with required columns upon backend startup.
- **Catalog Seeding:** Default job roles and skill categories are automatically populated on first run.
- **Local Runtime Data:** Uploaded candidate resumes, temporary audio recordings, and TTS speech caches are stored locally in `uploads/` and `backend/uploads/`.
- **Source Control Safety:** All database files (`*.db`, `*-wal`, `*-shm`), user uploads, audio caches, and `.env` files are strictly excluded via `.gitignore` to prevent committing private or generated data.

---

## Running the Platform

### Quick Start Scripts (Windows)

For one-click startup on Windows:

- **Start all servers:** Double-click `start.bat` (or execute `.\start.ps1` in PowerShell). This launches the backend, starts the Vite dev server, and automatically opens your browser.
- **Stop all servers:** Double-click `stop.bat` (or execute `.\stop.ps1` in PowerShell). This terminates processes on ports 8000 and 5173 cleanly.

---

### Manual Execution (Cross-Platform)

#### Terminal 1 — Start Backend Server:

Activate your virtual environment and run Uvicorn:

```bash
# Windows
.\venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload

# Linux / macOS
source venv/bin/activate
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

#### Terminal 2 — Start Frontend Dev Server:

```bash
cd frontend
npm run dev
```

---

### Service Endpoints

Once running, navigate to:

- **Frontend Application:** [http://localhost:5173](http://localhost:5173)
- **Backend API Base:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc API Documentation:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Backend Health Check:** [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

## Running Tests & Verifications

The repository includes comprehensive backend test suites covering authentication, end-to-end user journeys, and evaluations.

### Backend Automated Tests

Run tests using the project's Python virtual environment:

```bash
# Run Authentication test suite
python backend/test_auth.py

# Run Full End-to-End Platform Delivery test (19-step workflow)
python backend/test_final_delivery.py

# Run Answer Evaluation rubric test
python backend/test_evaluation.py

# Run Database Hardening & Schema test
python backend/test_database_hardening.py
```

### Frontend Build Verification

To verify that the frontend bundles without errors:

```bash
cd frontend
npm run build
```

---

## Project Directory Structure

```
AI-Interview-Preparation/
├── backend/
│   ├── .env.example              # Configuration environment template
│   ├── requirements.txt          # Python backend dependencies
│   ├── run.py                    # Direct backend execution entrypoint
│   ├── app/
│   │   ├── __init__.py
│   │   ├── auth.py               # Password hashing & JWT token issuance
│   │   ├── config.py             # App settings & fallback key management
│   │   ├── database.py           # SQLAlchemy engine & session maker
│   │   ├── main.py               # FastAPI app factory, CORS, security headers
│   │   ├── models.py             # Database ORM models (User, Interview, etc.)
│   │   ├── schemas.py            # Pydantic request/response schemas
│   │   ├── routers/
│   │   │   ├── auth.py           # Registration, login, /me routes
│   │   │   ├── profile.py        # Candidate profile routes
│   │   │   ├── resume.py         # File upload & document storage routes
│   │   │   ├── resume_analysis.py# Skills & project analysis routes
│   │   │   └── interview.py      # Session, question, answer, evaluation routes
│   │   ├── services/
│   │   │   ├── ai_service.py     # BaseAIProvider, RuleBasedNLP, GeminiProvider
│   │   │   ├── answer_evaluator.py # 5-axis objective rubric scoring engine
│   │   │   ├── feedback_analyzer.py# Strengths/weaknesses analysis
│   │   │   ├── question_generator.py# Contextual question synthesis
│   │   │   ├── recommendation_generator.py # Actionable roadmap generator
│   │   │   ├── resume_analyzer.py# Skills extraction heuristics
│   │   │   ├── resume_parser.py  # PDF and DOCX text extraction
│   │   │   └── tts_service.py    # Microsoft Edge Neural TTS voice engine
│   │   └── utils/
│   │       └── sanitizer.py      # Input sanitation & XSS defense
│   └── test_*.py                 # Automated backend test suites
├── frontend/
│   ├── index.html                # Single-page application template
│   ├── package.json              # Frontend scripts & dependencies
│   ├── package-lock.json
│   ├── postcss.config.js
│   ├── tailwind.config.js        # Design tokens & color system
│   ├── vite.config.js            # Vite build configuration
│   ├── public/                   # Static public assets (testing templates)
│   └── src/
│       ├── App.jsx               # Route declarations & page mappings
│       ├── main.jsx              # Application entry point
│       ├── index.css             # Tailwind base styles & keyframes
│       ├── components/           # Reusable UI widgets, layout, audio HUD
│       ├── context/              # AuthContext & state providers
│       ├── pages/                # 13 dedicated user flow views
│       └── utils/                # API client & audio utility helpers
├── start.bat / start.ps1         # Windows one-click server launchers
├── stop.bat / stop.ps1           # Windows one-click server termination scripts
├── .gitignore                    # Git exclusion rules for private/runtime data
└── README.md                     # Project documentation
```

---

## Security & Privacy Features

- **Password Protection:** User passwords are encrypted with bcrypt and verified using timing-attack resistant comparisons.
- **JWT Authorization:** Tokens expire after 24 hours and are validated on all protected API routes.
- **Security Headers:** FastAPI middleware enforces `nosniff`, `DENY` framing, `strict-origin-when-cross-origin` referrer policy, and strict `Permissions-Policy`.
- **Exception Sanitization:** Unhandled runtime exceptions return sanitized 500 error messages to prevent leaking stack traces or internal paths to clients.
- **Biometric Voice Privacy:** An audio purge endpoint (`DELETE /api/interview/{id}/audio`) allows candidates to wipe session audio files from storage upon test completion.
- **File Upload Safeguards:** Enforces strict MIME-type checks and file size limits (up to 5 MB) for PDF and DOCX resume uploads.

---

## Known Limitations

- **Speech Recognition Modality:** Browser speech recognition uses the Web Speech API (`webkitSpeechRecognition`), which requires microphone permissions and performs best on Chromium-based browsers (Google Chrome, Microsoft Edge). For non-supported browsers, the platform allows manual text input and transcript editing.
- **SQLite Concurrency:** SQLite is configured with Write-Ahead Logging (WAL) for smooth local multi-threading. For high-concurrency enterprise deployments, set `DATABASE_URL` to PostgreSQL.
- **External AI Providers:** Gemini AI and ElevenLabs integrations require external internet connectivity and valid API keys; when unconfigured or offline, the platform seamlessly runs with the built-in deterministic `RuleBasedNLPProvider` and `edge-tts`.

---

## License

This project is open-source software provided under the [MIT License](LICENSE).
