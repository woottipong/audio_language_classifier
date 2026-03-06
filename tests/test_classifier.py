"""Unit tests for classifier.py — DetectionResult, beam sizes, VAD, load_model."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from classifier import (
    DetectionResult,
    _get_adaptive_beam_size,
    _get_vad_parameters,
    load_model,
)
from constants import (
    ADAPTIVE_BEAM_SIZES,
    WHISPER_DETECTION_BEAM_SIZE,
    WHISPER_TRANSCRIPTION_BEAM_SIZE,
)


class TestDetectionResult:
    def test_required_fields(self) -> None:
        r = DetectionResult(
            file_name="audio.wav",
            detected_lang="en",
            probability=0.98,
            is_english=True,
            duration=5.0,
        )
        assert r.file_name == "audio.wav"
        assert r.detected_lang == "en"
        assert r.probability == 0.98
        assert r.is_english is True
        assert r.duration == 5.0

    def test_default_transcription_empty(self) -> None:
        r = DetectionResult("f.wav", "en", 0.9, True, 3.0)
        assert r.transcription == ""
        assert r.transcription_source == ""

    def test_to_dict_keys(self) -> None:
        r = DetectionResult("f.wav", "th", 0.95, False, 7.2, "สวัสดี", "google_chirp_2")
        d = r.to_dict()
        expected_keys = {
            "file_name", "detected_lang", "probability",
            "is_english", "duration", "transcription", "transcription_source",
        }
        assert set(d.keys()) == expected_keys

    def test_to_dict_values(self) -> None:
        r = DetectionResult("f.wav", "th", 0.95, False, 7.2, "สวัสดี", "google_chirp_2")
        d = r.to_dict()
        assert d["file_name"] == "f.wav"
        assert d["detected_lang"] == "th"
        assert d["probability"] == 0.95
        assert d["is_english"] is False
        assert d["duration"] == 7.2
        assert d["transcription"] == "สวัสดี"
        assert d["transcription_source"] == "google_chirp_2"

    def test_to_dict_is_dict(self) -> None:
        r = DetectionResult("f.wav", "en", 0.9, True, 1.0)
        assert isinstance(r.to_dict(), dict)


class TestGetAdaptiveBeamSize:
    @pytest.mark.parametrize("model_size", list(ADAPTIVE_BEAM_SIZES.keys()))
    def test_known_model_detection(self, model_size: str) -> None:
        import classifier
        classifier._model_size = model_size
        result = _get_adaptive_beam_size("detection")
        assert result == ADAPTIVE_BEAM_SIZES[model_size]["detection"]

    @pytest.mark.parametrize("model_size", list(ADAPTIVE_BEAM_SIZES.keys()))
    def test_known_model_transcription(self, model_size: str) -> None:
        import classifier
        classifier._model_size = model_size
        result = _get_adaptive_beam_size("transcription")
        assert result == ADAPTIVE_BEAM_SIZES[model_size]["transcription"]

    def test_unknown_model_detection_fallback(self) -> None:
        import classifier
        classifier._model_size = "unknown-model-xyz"
        result = _get_adaptive_beam_size("detection")
        assert result == WHISPER_DETECTION_BEAM_SIZE

    def test_unknown_model_transcription_fallback(self) -> None:
        import classifier
        classifier._model_size = "unknown-model-xyz"
        result = _get_adaptive_beam_size("transcription")
        assert result == WHISPER_TRANSCRIPTION_BEAM_SIZE


class TestGetVadParameters:
    def test_returns_dict(self) -> None:
        params = _get_vad_parameters()
        assert isinstance(params, dict)

    def test_required_keys(self) -> None:
        params = _get_vad_parameters()
        assert "threshold" in params
        assert "min_speech_duration_ms" in params
        assert "min_silence_duration_ms" in params

    def test_threshold_is_float(self) -> None:
        params = _get_vad_parameters()
        assert isinstance(params["threshold"], float)

    def test_duration_values_are_positive(self) -> None:
        params = _get_vad_parameters()
        assert params["min_speech_duration_ms"] > 0
        assert params["min_silence_duration_ms"] > 0


class TestLoadModel:
    def setup_method(self) -> None:
        """Reset module-level model singleton before each test."""
        import classifier
        classifier._model = None
        classifier._model_size = "base"

    def teardown_method(self) -> None:
        """Reset after each test."""
        import classifier
        classifier._model = None
        classifier._model_size = "base"

    def test_loads_model_on_first_call(self) -> None:
        mock_model = MagicMock()
        with patch("classifier.WhisperModel", return_value=mock_model) as MockModel:
            result = load_model("base", "cpu", "int8")
            MockModel.assert_called_once_with("base", device="cpu", compute_type="int8", cpu_threads=4)
            assert result is mock_model

    def test_returns_cached_model_on_second_call(self) -> None:
        mock_model = MagicMock()
        with patch("classifier.WhisperModel", return_value=mock_model) as MockModel:
            r1 = load_model("base", "cpu", "int8")
            r2 = load_model("base", "cpu", "int8")
            assert MockModel.call_count == 1
            assert r1 is r2
