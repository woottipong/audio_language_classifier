"""Custom exceptions for the audio language classifier."""


class AudioClassifierError(Exception):
    """Base exception for audio classifier errors."""
    pass


class ConfigurationError(AudioClassifierError):
    """Raised when configuration is invalid or missing."""
    pass


class StorageError(AudioClassifierError):
    """Raised when storage operations fail."""
    pass


class TranscriptionError(AudioClassifierError):
    """Raised when transcription fails."""
    pass


class GoogleSTTError(TranscriptionError):
    """Raised when Google STT API fails."""
    pass


class FileSizeError(AudioClassifierError):
    """Raised when file size exceeds limits."""
    pass


class AudioProcessingError(AudioClassifierError):
    """Raised when audio processing fails."""
    pass
