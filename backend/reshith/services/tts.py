"""Text-to-speech service with Google Cloud TTS and file-based caching."""

import base64
import hashlib
import logging
from pathlib import Path

from reshith.core.config import get_settings
from reshith.languages.hebrew import biblical_hebrew

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent.parent / "tts_cache"
_google_tts_available = False
_google_client = None


def init_tts() -> bool:
    """Initialize TTS service. Returns True if Google Cloud TTS is available."""
    global _google_tts_available, _google_client

    settings = get_settings()

    if not settings.google_cloud_api_key:
        logger.warning(
            "GOOGLE_CLOUD_API_KEY not set. "
            "Speech synthesis will fall back to browser Web Speech API."
        )
        return False

    try:
        from google.api_core.client_options import ClientOptions
        from google.cloud import texttospeech

        client_options = ClientOptions(
            api_key=settings.google_cloud_api_key
        )
        _google_client = texttospeech.TextToSpeechClient(
            client_options=client_options
        )
        _google_tts_available = True
        logger.info("Google Cloud TTS initialized successfully.")
        return True
    except ImportError:
        logger.warning(
            "google-cloud-texttospeech not installed. "
            "Speech synthesis will fall back to browser Web Speech API."
        )
        return False
    except Exception as e:
        logger.warning(
            f"Failed to initialize Google Cloud TTS: {e}. "
            "Speech synthesis will fall back to browser Web Speech API."
        )
        return False


def is_available() -> bool:
    """Check if Google Cloud TTS is available."""
    return _google_tts_available


def _get_cache_path(text: str, language: str) -> Path:
    """Generate cache file path for given text and language."""
    cache_key = hashlib.sha256(f"{language}:{text}".encode()).hexdigest()[:16]
    return CACHE_DIR / f"{cache_key}.mp3"


def _prepare_hebrew_for_tts(text: str) -> str:
    """Strip vowel points and cantillation marks for TTS processing.

    Most TTS engines ignore niqqud anyway, but stripping ensures consistent
    cache keys and avoids any potential issues.
    """
    return biblical_hebrew.strip_vowels(text)


async def synthesize_speech(text: str, language: str = "he-IL") -> str | None:
    """Synthesize speech for the given text.

    Args:
        text: The text to synthesize (can include Hebrew vowel points)
        language: BCP-47 language code (default: he-IL for Hebrew)

    Returns:
        Base64-encoded MP3 audio data, or None if synthesis failed
    """
    if not _google_tts_available or _google_client is None:
        return None

    cleaned_text = _prepare_hebrew_for_tts(text) if language.startswith("he") else text

    cache_path = _get_cache_path(cleaned_text, language)
    if cache_path.exists():
        logger.debug(f"TTS cache hit for: {text[:20]}...")
        audio_content = cache_path.read_bytes()
        return base64.b64encode(audio_content).decode("utf-8")

    try:
        from google.cloud import texttospeech

        settings = get_settings()

        synthesis_input = texttospeech.SynthesisInput(text=cleaned_text)

        voice = texttospeech.VoiceSelectionParams(
            language_code=language,
            name=settings.google_tts_voice,
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.85,
        )

        response = _google_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
        )

        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(response.audio_content)
        logger.debug(f"TTS synthesized and cached: {text[:20]}...")

        return base64.b64encode(response.audio_content).decode("utf-8")

    except Exception as e:
        logger.error(f"TTS synthesis failed: {e}")
        return None
