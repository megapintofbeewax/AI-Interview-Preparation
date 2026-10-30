import os
import re
import hashlib
import asyncio
import logging
from typing import Optional, Dict, Any, List
import edge_tts
from app.config import settings

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join("uploads", "tts_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# Curated high-fidelity neural voices ideal for professional English job interviews
RECOMMENDED_VOICES = [
    {
        "id": "en-US-JennyNeural",
        "name": "Jenny (US Professional Female)",
        "gender": "Female",
        "description": "Warm, natural, clear, and professional American interviewer."
    },
    {
        "id": "en-US-GuyNeural",
        "name": "Guy (US Professional Male)",
        "gender": "Male",
        "description": "Calm, confident, articulate, and natural American interviewer."
    },
    {
        "id": "en-US-AriaNeural",
        "name": "Aria (US Conversational Female)",
        "gender": "Female",
        "description": "Expressive, engaging, and clear conversational voice."
    },
    {
        "id": "en-US-ChristopherNeural",
        "name": "Christopher (US Steady Male)",
        "gender": "Male",
        "description": "Deep, authoritative, and steady professional voice."
    },
    {
        "id": "en-GB-SoniaNeural",
        "name": "Sonia (UK Professional Female)",
        "gender": "Female",
        "description": "Articulate, polite, and polished British interviewer."
    },
    {
        "id": "en-GB-RyanNeural",
        "name": "Ryan (UK Professional Male)",
        "gender": "Male",
        "description": "Clear, modern British professional interviewer."
    }
]

def normalize_interview_text(text: str) -> str:
    """
    Normalizes interview question text for natural conversational speech delivery:
    - Removes raw markdown code formatting, backticks, asterisks, bullets.
    - Expands symbols to improve speech rhythm and cadence.
    - Ensures proper sentence termination for natural question inflection.
    """
    if not text:
        return ""

    # Strip code blocks and inline backticks
    cleaned = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)

    # Strip markdown bold, italics, bullets
    cleaned = re.sub(r'[*_~#]', '', cleaned)
    cleaned = re.sub(r'^\s*[-+*]\s+', '', cleaned, flags=re.MULTILINE)

    # Normalize technical abbreviations and symbols for conversational speech
    cleaned = re.sub(r'\bCI/CD\b', 'C-I C-D', cleaned)
    cleaned = re.sub(r'\bAPI\b', 'A-P-I', cleaned)
    cleaned = re.sub(r'\bAPIs\b', 'A-P-Is', cleaned)
    cleaned = re.sub(r'\be\.g\.,?\b', 'for example,', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bi\.e\.,?\b', 'that is,', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bw/\b', 'with', cleaned)
    cleaned = re.sub(r'&', ' and ', cleaned)

    # Collapse multiple spaces and clean lines
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    # Ensure natural question termination
    if cleaned and not cleaned.endswith(('.', '?', '!')):
        cleaned += '?'

    return cleaned

class TTSService:
    """
    High-fidelity Neural Text-to-Speech Service.
    Defaults to Microsoft Edge Neural Speech (100% free, natural human-like voice, zero API key).
    Optionally supports ElevenLabs if an API key is configured.
    Includes persistent audio caching for low latency and zero duplicate generation.
    """

    def __init__(self):
        self.cache_dir = CACHE_DIR
        self.provider = settings.TTS_PROVIDER or "edge-tts"
        self.default_voice = settings.TTS_VOICE or "en-US-JennyNeural"
        self.default_rate = settings.TTS_RATE or "+0%"
        self.default_pitch = settings.TTS_PITCH or "+0Hz"

    def _get_cache_path(self, text: str, voice: str, rate: str, pitch: str) -> str:
        """Computes a deterministic hash for caching synthesized audio."""
        cache_key = hashlib.sha256(f"{voice}_{rate}_{pitch}_{text}".encode("utf-8")).hexdigest()
        return os.path.join(self.cache_dir, f"{cache_key}.mp3")

    async def _synthesize_edge_tts(self, text: str, voice: str, rate: str, pitch: str, output_path: str) -> str:
        """Generates natural human-like speech using Microsoft Edge Neural TTS with automatic retry."""
        temp_path = f"{output_path}.tmp"
        last_error = None
        for attempt in range(2):
            try:
                communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
                await communicate.save(temp_path)
                if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                    os.replace(temp_path, output_path)
                    return output_path
                raise RuntimeError("Edge-TTS generated empty audio file.")
            except Exception as e:
                last_error = e
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass
                logger.warning(f"Edge-TTS attempt {attempt + 1} failed: {e}")
                if attempt == 0:
                    await asyncio.sleep(0.5)
        
        logger.error(f"Edge-TTS synthesis error: {last_error}")
        raise last_error

    async def _synthesize_elevenlabs(self, text: str, output_path: str) -> Optional[str]:
        """Synthesizes speech via ElevenLabs API if credentials are configured."""
        api_key = settings.ELEVENLABS_API_KEY
        if not api_key:
            return None

        import aiohttp
        voice_id = settings.ELEVENLABS_VOICE_ID or "21m00Tcm4TlvDq8ikWAM"
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.65,
                "similarity_boost": 0.75
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=12) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        with open(output_path, "wb") as f:
                            f.write(audio_data)
                        return output_path
                    else:
                        err_text = await response.text()
                        logger.warning(f"ElevenLabs TTS returned HTTP {response.status}: {err_text}")
                        return None
        except Exception as e:
            logger.warning(f"ElevenLabs synthesis failed: {e}. Falling back to Edge-TTS.")
            return None

    async def generate_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        pitch: Optional[str] = None
    ) -> str:
        """
        Generates and caches natural human-like speech for the provided interview text.
        Returns the local file path to the high-quality MP3 audio.
        """
        normalized_text = normalize_interview_text(text)
        if not normalized_text:
            raise ValueError("Input text for speech synthesis cannot be empty.")

        selected_voice = voice or self.default_voice
        selected_rate = rate or self.default_rate
        selected_pitch = pitch or self.default_pitch

        cache_path = self._get_cache_path(normalized_text, selected_voice, selected_rate, selected_pitch)

        # Return cached audio if available
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
            return cache_path

        # If ElevenLabs is explicitly configured as preferred provider, attempt it first
        if settings.TTS_PROVIDER.lower() == "elevenlabs" and settings.ELEVENLABS_API_KEY:
            try:
                el_path = await self._synthesize_elevenlabs(normalized_text, cache_path)
                if el_path and os.path.exists(el_path) and os.path.getsize(el_path) > 0:
                    return el_path
            except Exception as e:
                logger.warning(f"ElevenLabs synthesis failed, falling back to neural Edge-TTS: {e}")

        # Primary natural neural speech generator: Edge-TTS
        return await self._synthesize_edge_tts(
            normalized_text,
            selected_voice,
            selected_rate,
            selected_pitch,
            cache_path
        )

    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Returns the list of recommended professional interviewer voices."""
        return RECOMMENDED_VOICES

    def list_curated_voices(self) -> List[Dict[str, Any]]:
        """Alias for get_available_voices."""
        return self.get_available_voices()


# Singleton instance
tts_service = TTSService()
