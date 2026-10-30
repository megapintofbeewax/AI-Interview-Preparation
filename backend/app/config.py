import os
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class Settings(BaseModel):
    PROJECT_NAME: str = "AI Interview Preparation Platform"
    # Development fallback key. In production, set a strong, unique SECRET_KEY environment variable.
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-insecure-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./ai_interview.db")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Natural Human-Like Text-to-Speech Configuration
    TTS_PROVIDER: str = os.getenv("TTS_PROVIDER", "edge-tts")  # 'edge-tts' (default, free neural) or 'elevenlabs'
    TTS_VOICE: str = os.getenv("TTS_VOICE", "en-US-JennyNeural")  # Recommended: en-US-JennyNeural (female) or en-US-GuyNeural (male)
    TTS_RATE: str = os.getenv("TTS_RATE", "+0%")  # Conversational speech rate
    TTS_PITCH: str = os.getenv("TTS_PITCH", "+0Hz")
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel

settings = Settings()

if settings.SECRET_KEY.startswith("dev-insecure"):
    logger.warning("Running with insecure default development SECRET_KEY. Set a unique SECRET_KEY in production.")

