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
    "large-v3-turbo": {"detection": 1, "transcription": 7},
    "turbo": {"detection": 1, "transcription": 7},
}

VAD_THRESHOLD: float = 0.3
VAD_MIN_SPEECH_DURATION_MS: int = 100
VAD_MIN_SILENCE_DURATION_MS: int = 1000

# Anti-hallucination parameters for Whisper transcription
# condition_on_previous_text=False: break the hallucination cascade between 30-s chunks
WHISPER_CONDITION_ON_PREVIOUS_TEXT: bool = False
# repetition_penalty > 1 penalises tokens that were recently generated
WHISPER_REPETITION_PENALTY: float = 1.3
# Prevent any 3-gram from repeating (stops "นี่นี่นี่" loops)
WHISPER_NO_REPEAT_NGRAM_SIZE: int = 3
# Discard segments whose output is too compressible (i.e. highly repetitive)
WHISPER_COMPRESSION_RATIO_THRESHOLD: float = 2.4
# Minimum avg log-probability; segments below this are treated as failed/silence
WHISPER_LOG_PROB_THRESHOLD: float = -1.0
# Mark chunk as no-speech when silence probability exceeds this
WHISPER_NO_SPEECH_THRESHOLD: float = 0.6
# Warn when language detection confidence is below this threshold
WHISPER_LOW_CONFIDENCE_THRESHOLD: float = 0.5
# Any word that accounts for more than this fraction of all words = hallucination
WHISPER_HALLUCINATION_WORD_RATIO: float = 0.6

# ---------------------------------------------------------------------------
# EN-specific transcription parameters
# EN conversation speech differs from TH in key ways:
#   - Naturally repeats phrases ("yes yes", "ok ok") → ngram penalty breaks it
#   - Common words (the, and, yes) penalised by repetition_penalty → gaps in output
#   - log_prob is lower on base/small models for accented EN → segments dropped
#   - Longer pauses between turns → no_speech_threshold too aggressive
#   - Long calls benefit from carrying context across 30s chunks
# ---------------------------------------------------------------------------
# Re-enable context carry-over across 30s chunks (safe for EN, risky for TH loops)
WHISPER_EN_CONDITION_ON_PREVIOUS_TEXT: bool = True
# No repetition penalty — EN naturally repeats connectors and filler words
WHISPER_EN_REPETITION_PENALTY: float = 1.0
# Disable n-gram blocking — "yes yes", "ok ok" are valid EN speech
WHISPER_EN_NO_REPEAT_NGRAM_SIZE: int = 0
# More lenient segment threshold — base/small models score EN accents lower
WHISPER_EN_LOG_PROB_THRESHOLD: float = -2.0
# More lenient no-speech threshold — EN calls have longer pauses between turns
WHISPER_EN_NO_SPEECH_THRESHOLD: float = 0.7
# Slightly looser VAD threshold for EN — fewer false silence cuts during pauses
WHISPER_EN_VAD_THRESHOLD: float = 0.2
# Shorter min silence to avoid cutting mid-sentence pauses in EN conversation
WHISPER_EN_VAD_MIN_SILENCE_DURATION_MS: int = 500
# EN speech is naturally more repetitive (filler words, backchannel) — allow higher ratio
WHISPER_EN_COMPRESSION_RATIO_THRESHOLD: float = 3.0

# ---------------------------------------------------------------------------
# Initial prompts — seed Whisper's context window before transcription begins.
# Helps on noisy telephone audio (8kHz codec) by:
#   - Biasing vocabulary toward call-center domain terms
#   - Reducing hallucination on low-SNR segments
#   - Setting script/punctuation style expectations
# Keep under ~50 tokens (longer prompts eat into the 30s context window).
# ---------------------------------------------------------------------------
WHISPER_INITIAL_PROMPT_TH: str = (
    "บันทึกเสียงสายโทรศัพท์ศูนย์รับแจ้งเหตุฉุกเฉิน ผู้แจ้งเหตุ เจ้าหน้าที่ ชื่อ ที่อยู่ อาการ"
)
WHISPER_INITIAL_PROMPT_EN: str = (
    "Emergency call center recording. Caller reports incident. "
    "Address, name, symptoms, ambulance, police."
)

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
