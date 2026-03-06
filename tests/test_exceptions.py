"""Unit tests for exceptions.py — hierarchy and message propagation."""

from __future__ import annotations

import pytest

from exceptions import (
    AudioClassifierError,
    AudioProcessingError,
    ConfigurationError,
    FileSizeError,
    GoogleSTTError,
    StorageError,
    TranscriptionError,
)


class TestExceptionHierarchy:
    def test_configuration_error_is_base(self) -> None:
        assert issubclass(ConfigurationError, AudioClassifierError)

    def test_storage_error_is_base(self) -> None:
        assert issubclass(StorageError, AudioClassifierError)

    def test_transcription_error_is_base(self) -> None:
        assert issubclass(TranscriptionError, AudioClassifierError)

    def test_google_stt_error_is_transcription(self) -> None:
        assert issubclass(GoogleSTTError, TranscriptionError)

    def test_google_stt_error_is_base(self) -> None:
        assert issubclass(GoogleSTTError, AudioClassifierError)

    def test_file_size_error_is_base(self) -> None:
        assert issubclass(FileSizeError, AudioClassifierError)

    def test_audio_processing_error_is_base(self) -> None:
        assert issubclass(AudioProcessingError, AudioClassifierError)

    def test_base_is_exception(self) -> None:
        assert issubclass(AudioClassifierError, Exception)


class TestExceptionMessages:
    def test_message_preserved(self) -> None:
        err = ConfigurationError("bad config")
        assert str(err) == "bad config"

    def test_catch_as_base(self) -> None:
        with pytest.raises(AudioClassifierError):
            raise StorageError("disk full")

    def test_catch_as_transcription(self) -> None:
        with pytest.raises(TranscriptionError):
            raise GoogleSTTError("API failed")

    def test_catch_exact_type(self) -> None:
        with pytest.raises(FileSizeError, match="too large"):
            raise FileSizeError("too large")
