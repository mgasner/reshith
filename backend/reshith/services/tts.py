"""Text-to-speech service with Google Cloud TTS and file-based caching."""

import asyncio
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

# MMS-TTS (Facebook) for Latin — loaded lazily on first use
_mms_model = None
_mms_tokenizer = None


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


def _synthesize_latin_mms(text: str) -> bytes | None:
    """Synthesize Latin text using Facebook MMS-TTS (neural VITS model).

    Returns raw WAV bytes, or None on failure.
    Loads the model lazily on first call (~100 MB download on first run).
    """
    global _mms_model, _mms_tokenizer

    try:
        import io

        import scipy.io.wavfile
        import torch
        from transformers import AutoTokenizer, VitsModel

        if _mms_model is None or _mms_tokenizer is None:
            logger.info("Loading facebook/mms-tts-lat model (first run may download ~100 MB)…")
            _mms_tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-lat")
            _mms_model = VitsModel.from_pretrained("facebook/mms-tts-lat")
            logger.info("MMS-TTS Latin model loaded.")

        inputs = _mms_tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            waveform = _mms_model(**inputs).waveform.squeeze().numpy()

        sampling_rate: int = _mms_model.config.sampling_rate  # type: ignore[attr-defined]
        buf = io.BytesIO()
        scipy.io.wavfile.write(buf, sampling_rate, waveform)
        return buf.getvalue()

    except Exception as e:
        logger.error(f"MMS-TTS Latin synthesis failed: {e}")
        return None


async def synthesize_speech(text: str, language: str = "he-IL") -> tuple[str, str] | None:
    """Synthesize speech for the given text.

    Args:
        text: The text to synthesize
        language: BCP-47 language code (default: he-IL for Hebrew)

    Returns:
        (base64_audio, mime_type) tuple, or None if synthesis failed.
        MIME type is "audio/wav" for Latin (MMS-TTS) and "audio/mp3" otherwise.
    """
    # Latin: use MMS-TTS neural model regardless of Google TTS availability
    if language == "la":
        # Check disk cache first
        cache_path = _get_cache_path(text, language).with_suffix(".wav")
        if cache_path.exists():
            logger.debug(f"MMS-TTS cache hit for: {text[:20]}...")
            return base64.b64encode(cache_path.read_bytes()).decode("utf-8"), "audio/wav"
        # Run blocking inference in a thread so we don't stall the event loop
        wav_bytes = await asyncio.to_thread(_synthesize_latin_mms, text)
        if wav_bytes is None:
            return None
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(wav_bytes)
        return base64.b64encode(wav_bytes).decode("utf-8"), "audio/wav"

    if not _google_tts_available or _google_client is None:
        return None

    cleaned_text = _prepare_hebrew_for_tts(text) if language.startswith("he") else text

    cache_path = _get_cache_path(cleaned_text, language)
    if cache_path.exists():
        logger.debug(f"TTS cache hit for: {text[:20]}...")
        audio_content = cache_path.read_bytes()
        return base64.b64encode(audio_content).decode("utf-8"), "audio/mp3"

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

        return base64.b64encode(response.audio_content).decode("utf-8"), "audio/mp3"

    except Exception as e:
        logger.error(f"TTS synthesis failed: {e}")
        return None
