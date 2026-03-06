"""Language detection using faster-whisper."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from faster_whisper import WhisperModel

from constants import (
    ADAPTIVE_BEAM_SIZES,
    ENGLISH_LANGUAGE_CODE,
    THAI_LANGUAGE_CODE,
    TRANSCRIPTION_SOURCE_GOOGLE_CHIRP,
    TRANSCRIPTION_SOURCE_WHISPER,
    TRANSCRIPTION_SOURCE_WHISPER_FALLBACK,
    VAD_MIN_SILENCE_DURATION_MS,
    VAD_MIN_SPEECH_DURATION_MS,
    VAD_THRESHOLD,
    WHISPER_DETECTION_BEAM_SIZE,
    WHISPER_TRANSCRIPTION_BEAM_SIZE,
)
from exceptions import AudioProcessingError
from google_stt import transcribe_with_chirp

logger = logging.getLogger(__name__)

_model: WhisperModel | None = None
_model_size: str = "base"  # Track model size for adaptive beam size


@dataclass
class DetectionResult:
    """Result of language detection and optional transcription."""
    file_name: str
    detected_lang: str
    probability: float
    is_english: bool
    duration: float
    transcription: str = ""
    transcription_source: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary for export."""
        return {
            "file_name": self.file_name,
            "detected_lang": self.detected_lang,
            "probability": self.probability,
            "is_english": self.is_english,
            "duration": self.duration,
            "transcription": self.transcription,
            "transcription_source": self.transcription_source,
        }


def load_model(model_size: str, device: str, compute_type: str) -> WhisperModel:
    """Load the faster-whisper model (cached after first call).
    
    Args:
        model_size: Size of the Whisper model (tiny/base/small/medium/large)
        device: Device to run on (auto/cpu/cuda)
        compute_type: Compute type (int8/float16/float32)
        
    Returns:
        Loaded WhisperModel instance
    """
    global _model, _model_size
    if _model is None:
        logger.info(
            "Loading faster-whisper model: size=%s, device=%s, compute_type=%s",
            model_size,
            device,
            compute_type,
        )
        _model = WhisperModel(model_size, device=device, compute_type=compute_type)
        _model_size = model_size
        logger.info("Model loaded successfully.")
    return _model


def _get_adaptive_beam_size(mode: str) -> int:
    """Get adaptive beam size based on model size and mode.
    
    Args:
        mode: Either 'detection' or 'transcription'
        
    Returns:
        Optimal beam size for the current model and mode
    """
    if _model_size in ADAPTIVE_BEAM_SIZES:
        return ADAPTIVE_BEAM_SIZES[_model_size][mode]
    
    # Fallback to defaults if model size not in mapping
    if mode == "detection":
        return WHISPER_DETECTION_BEAM_SIZE
    else:
        return WHISPER_TRANSCRIPTION_BEAM_SIZE


def _get_vad_parameters() -> dict:
    """Get VAD (Voice Activity Detection) parameters.
    
    Returns:
        Dictionary of VAD parameters
    """
    return {
        "threshold": VAD_THRESHOLD,
        "min_speech_duration_ms": VAD_MIN_SPEECH_DURATION_MS,
        "min_silence_duration_ms": VAD_MIN_SILENCE_DURATION_MS,
    }


def _detect_language_only(file_path: Path, model: WhisperModel) -> tuple:
    """Perform quick language detection without full transcription.
    
    Args:
        file_path: Path to audio file
        model: Loaded WhisperModel instance
        
    Returns:
        Tuple of (detected_lang, probability, duration)
    """
    beam_size = _get_adaptive_beam_size("detection")
    segments, info = model.transcribe(
        str(file_path),
        beam_size=beam_size,
        best_of=1,
        vad_filter=True,
        vad_parameters=_get_vad_parameters(),
    )
    
    return info.language, round(info.language_probability, 4), round(info.duration, 2) if hasattr(info, 'duration') else 0.0


def _transcribe_with_whisper(file_path: Path, model: WhisperModel) -> tuple:
    """Perform full transcription with Whisper.

    Two-pass strategy:
    1. Quick detection pass (beam_size=1) to identify the language reliably.
    2. Full transcription pass with the detected language as an explicit hint,
       so Whisper never has to guess and produces complete, accurate output for
       every language — especially important for English clips that are short or
       start with silence.

    Args:
        file_path: Path to audio file
        model: Loaded WhisperModel instance

    Returns:
        Tuple of (detected_lang, probability, duration, transcription_text, segments_list)
    """
    # --- Pass 1: detect language only (fast) ---
    detected_lang, probability, duration = _detect_language_only(file_path, model)

    logger.debug(
        "Language detected for transcription: %s (prob=%.4f) — %s",
        detected_lang,
        probability,
        file_path.name,
    )

    # --- Pass 2: transcribe with confirmed language hint ---
    beam_size = _get_adaptive_beam_size("transcription")
    segments, info = model.transcribe(
        str(file_path),
        language=detected_lang,
        beam_size=beam_size,
        vad_filter=True,
        vad_parameters=_get_vad_parameters(),
    )

    # Use detection-pass values (more reliable; info here may differ slightly)
    duration = duration or (round(info.duration, 2) if hasattr(info, "duration") else 0.0)

    segments_list = list(segments)
    transcription = " ".join(segment.text for segment in segments_list).strip()

    return detected_lang, probability, duration, transcription, segments_list


def _transcribe_thai_with_google(file_path: Path, whisper_transcription: str, segments_list: list, duration: float = 0.0) -> tuple[str, str]:
    """Transcribe Thai audio using Google Chirp 2 with fallback to Whisper.
    
    Args:
        file_path: Path to audio file
        whisper_transcription: Pre-computed Whisper transcription for fallback
        segments_list: Whisper segments list (unused, kept for compatibility)
        duration: Audio duration in seconds (from Whisper, avoids ffprobe call)
        
    Returns:
        Tuple of (transcription_text, source)
    """
    logger.info("Using Google Chirp 2 for Thai transcription: %s", file_path.name)
    # Pass duration to avoid ffprobe subprocess call
    transcription_text = transcribe_with_chirp(file_path, duration if duration > 0 else None)
    
    if transcription_text is None:
        logger.warning("Google Chirp 2 failed, falling back to Whisper")
        # Use pre-computed Whisper transcription instead of re-transcribing
        return whisper_transcription, TRANSCRIPTION_SOURCE_WHISPER_FALLBACK
    
    return transcription_text, TRANSCRIPTION_SOURCE_GOOGLE_CHIRP


def detect_language(
    file_path: Path,
    max_duration: int,
    model: WhisperModel,
    enable_transcription: bool = False,
    use_google_for_thai: bool = False
) -> dict:
    """Detect the language of an audio file and optionally transcribe it.

    Args:
        file_path: Path to the audio file
        max_duration: Maximum duration to read (ignored if enable_transcription=True)
        model: Loaded WhisperModel instance
        enable_transcription: If True, transcribe entire audio; if False, quick detection only
        use_google_for_thai: If True, use Google Chirp 2 for Thai transcription

    Returns:
        Dictionary with detection/transcription results
    """
    file_name = file_path.name

    try:
        if enable_transcription:
            detected_lang, probability, duration, transcription, segments_list = _transcribe_with_whisper(
                file_path, model
            )
            
            if detected_lang == THAI_LANGUAGE_CODE and use_google_for_thai:
                # Use cached transcription and segments - no need to transcribe again!
                # Pass duration to avoid ffprobe subprocess call
                transcription, source = _transcribe_thai_with_google(
                    file_path, transcription, segments_list, duration
                )
            else:
                source = TRANSCRIPTION_SOURCE_WHISPER
            
            result = DetectionResult(
                file_name=file_name,
                detected_lang=detected_lang,
                probability=probability,
                is_english=(detected_lang == ENGLISH_LANGUAGE_CODE),
                duration=duration,
                transcription=transcription,
                transcription_source=source,
            )
            
            logger.debug(
                "File: %s | lang=%s | prob=%.4f | english=%s | source=%s | text=%s",
                file_name,
                detected_lang,
                probability,
                result.is_english,
                source,
                transcription[:50] + "..." if len(transcription) > 50 else transcription,
            )
        else:
            detected_lang, probability, duration = _detect_language_only(file_path, model)
            
            result = DetectionResult(
                file_name=file_name,
                detected_lang=detected_lang,
                probability=probability,
                is_english=(detected_lang == ENGLISH_LANGUAGE_CODE),
                duration=duration,
            )
            
            logger.debug(
                "File: %s | lang=%s | prob=%.4f | english=%s",
                file_name,
                detected_lang,
                probability,
                result.is_english,
            )

        return result.to_dict()

    except Exception as exc:
        logger.error("Error processing %s: %s", file_name, exc)
        return DetectionResult(
            file_name=file_name,
            detected_lang="error",
            probability=0.0,
            is_english=False,
            duration=0.0,
        ).to_dict()
