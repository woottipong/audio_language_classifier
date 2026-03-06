"""Shared constants for the audio language classifier."""

from __future__ import annotations

SUPPORTED_AUDIO_EXTENSIONS: list[str] = [
    ".wav",
    ".mp3",
    ".flac",
    ".ogg",
    ".m4a",
    ".wma",
    ".aac",
]

MAX_FILE_SIZE_MB: int = 10
MAX_AUDIO_DURATION_SECONDS: int = 60

GOOGLE_STT_SYNC_API_TIMEOUT: int = 300
GOOGLE_STT_BATCH_API_TIMEOUT: int = 300
GOOGLE_STT_BATCH_POLL_INTERVAL: int = 5

# Retry configuration for Google STT
GOOGLE_STT_MAX_RETRIES: int = 3
GOOGLE_STT_RETRY_DELAY: float = 1.0  # Initial delay in seconds
GOOGLE_STT_RETRY_BACKOFF: float = 2.0  # Exponential backoff multiplier

# Default model - base for speed
DEFAULT_MODEL_SIZE: str = "base"
DEFAULT_DEVICE: str = "auto"
DEFAULT_COMPUTE_TYPE: str = "int8"

# Thonburian models - fine-tuned for Thai (biodatlab), use with --use-thonburian
THONBURIAN_MODEL: str = "Vinxscribe/biodatlab-whisper-th-large-v3-faster"  # CT2 format
THONBURIAN_MEDIUM: str = "biodatlab/whisper-th-medium-combined"  # Original (not CT2)

# Standard Whisper models (can override with --model-size)
WHISPER_BASE_MODEL: str = "base"
WHISPER_SMALL_MODEL: str = "small"
WHISPER_MEDIUM_MODEL: str = "medium"
WHISPER_LARGE_MODEL: str = "large"
DEFAULT_MAX_DURATION: int = 30
DEFAULT_MAX_WORKERS: int = 4
DEFAULT_LOG_LEVEL: str = "INFO"

# Cache configuration
DEFAULT_CACHE_DIR: str = "./.cache"
DEFAULT_CACHE_TTL_HOURS: int = 24
CACHE_ENABLED_BY_DEFAULT: bool = False

WHISPER_DETECTION_BEAM_SIZE: int = 1
WHISPER_TRANSCRIPTION_BEAM_SIZE: int = 5

# Adaptive beam sizes based on model size for optimal speed/accuracy balance
ADAPTIVE_BEAM_SIZES: dict[str, dict[str, int]] = {
    "tiny": {"detection": 1, "transcription": 3},
    "base": {"detection": 1, "transcription": 3},
    "small": {"detection": 1, "transcription": 5},
    "medium": {"detection": 1, "transcription": 5},
    "large": {"detection": 1, "transcription": 7},
    "large-v2": {"detection": 1, "transcription": 7},
    "large-v3": {"detection": 1, "transcription": 7},
}

VAD_THRESHOLD: float = 0.3
VAD_MIN_SPEECH_DURATION_MS: int = 100
VAD_MIN_SILENCE_DURATION_MS: int = 1000

CSV_FIELDNAMES: list[str] = [
    "file_name",
    "detected_lang",
    "probability",
    "is_english",
    "duration",
    "transcription",
    "transcription_source",
]

CSV_FIELDNAMES_NO_TRANSCRIPTION: list[str] = [
    "file_name",
    "detected_lang",
    "probability",
    "is_english",
    "duration",
]

THAI_LANGUAGE_CODE: str = "th"
ENGLISH_LANGUAGE_CODE: str = "en"
THAI_STT_LANGUAGE_CODE: str = "th-TH"

TRANSCRIPTION_SOURCE_WHISPER: str = "whisper"
TRANSCRIPTION_SOURCE_GOOGLE_CHIRP: str = "google_chirp_2"
TRANSCRIPTION_SOURCE_WHISPER_FALLBACK: str = "whisper (fallback)"
