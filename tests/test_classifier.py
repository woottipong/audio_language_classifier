"""Unit tests for classifier.py — DetectionResult, beam sizes, VAD, load_model, Thai model."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from classifier import (
    DetectionResult,
    _ensure_ct2_model,
    _get_adaptive_beam_size,
    _get_vad_parameters,
    load_model,
    load_thai_model,
)
from exceptions import ModelLoadError
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


class TestEnsureCt2Model:
    """Tests for _ensure_ct2_model() — format detection and auto-conversion."""

    def test_local_ct2_path_returned_unchanged(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "my_model"
        model_dir.mkdir()
        (model_dir / "model.bin").write_bytes(b"")
        result = _ensure_ct2_model(str(model_dir), "int8")
        assert result == str(model_dir)

    def test_local_path_without_model_bin_raises(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "hf_model"
        model_dir.mkdir()
        (model_dir / "pytorch_model.bin").write_bytes(b"")
        with pytest.raises(ModelLoadError, match="no model.bin"):
            _ensure_ct2_model(str(model_dir), "int8")

    def test_hf_id_returns_cached_ct2_if_exists(self, tmp_path: Path) -> None:
        ct2_dir = tmp_path / "ct2" / "org--model"
        ct2_dir.mkdir(parents=True)
        (ct2_dir / "model.bin").write_bytes(b"")
        with patch.dict("os.environ", {"HF_HOME": str(tmp_path)}, clear=False):
            result = _ensure_ct2_model("org/model", "int8")
        assert result == str(ct2_dir)

    def test_hf_id_uses_existing_ct2_snapshot(self, tmp_path: Path) -> None:
        """If the converted CT2 model doesn't exist in cache yet, the converter is called."""
        # This test just verifies the no-cache path triggers TransformersConverter
        mock_converter = MagicMock()
        with patch.dict("os.environ", {"HF_HOME": str(tmp_path)}, clear=False):
            with patch("ctranslate2.converters.TransformersConverter", return_value=mock_converter):
                _ensure_ct2_model("org/already-ct2", "int8")
        mock_converter.convert.assert_called_once()

    def test_hf_id_converts_transformers_model(self, tmp_path: Path) -> None:
        """HF model should be converted via TransformersConverter and CT2 path returned."""
        mock_converter = MagicMock()

        with patch.dict("os.environ", {"HF_HOME": str(tmp_path)}, clear=False):
            with patch("ctranslate2.converters.TransformersConverter", return_value=mock_converter) as MockConverter:
                result = _ensure_ct2_model("org/th-model", "float16")

        MockConverter.assert_called_once_with("org/th-model")
        mock_converter.convert.assert_called_once()
        convert_args, convert_kwargs = mock_converter.convert.call_args
        used_quant = convert_kwargs.get("quantization") or (convert_args[1] if len(convert_args) > 1 else None)
        assert used_quant == "float16"
        assert "ct2" in result
        assert "org--th-model" in result

    def test_conversion_exception_raises_model_load_error(self, tmp_path: Path) -> None:
        broken_converter = MagicMock()
        broken_converter.convert.side_effect = RuntimeError("Bad weights")

        with patch.dict("os.environ", {"HF_HOME": str(tmp_path)}, clear=False):
            with patch("ctranslate2.converters.TransformersConverter", return_value=broken_converter):
                with pytest.raises(ModelLoadError, match="Failed to convert"):
                    _ensure_ct2_model("org/broken", "int8")

    def test_download_failure_raises_model_load_error(self, tmp_path: Path) -> None:
        """TransformersConverter raising during convert is wrapped as ModelLoadError."""
        failing_converter = MagicMock()
        failing_converter.convert.side_effect = OSError("network")

        with patch.dict("os.environ", {"HF_HOME": str(tmp_path)}, clear=False):
            with patch("ctranslate2.converters.TransformersConverter", return_value=failing_converter):
                with pytest.raises(ModelLoadError, match="Failed to convert"):
                    _ensure_ct2_model("org/missing", "int8")

    def test_unknown_quantization_falls_back_to_int8(self, tmp_path: Path) -> None:
        mock_converter = MagicMock()

        with patch.dict("os.environ", {"HF_HOME": str(tmp_path)}, clear=False):
            with patch("ctranslate2.converters.TransformersConverter", return_value=mock_converter):
                _ensure_ct2_model("org/model", "bfloat16")  # unsupported → int8

        convert_args, convert_kwargs = mock_converter.convert.call_args
        used_quant = convert_kwargs.get("quantization") or (convert_args[1] if len(convert_args) > 1 else None)
        assert used_quant == "int8"


class TestLoadThaiModel:
    def setup_method(self) -> None:
        import classifier
        classifier._thai_model = None

    def teardown_method(self) -> None:
        import classifier
        classifier._thai_model = None

    def test_loads_from_ct2_path(self, tmp_path: Path) -> None:
        ct2_dir = tmp_path / "model"
        ct2_dir.mkdir()
        (ct2_dir / "model.bin").write_bytes(b"")

        mock_model = MagicMock()
        with patch("classifier.WhisperModel", return_value=mock_model) as MockModel:
            result = load_thai_model(str(ct2_dir), "cpu", "int8")
        MockModel.assert_called_once_with(
            str(ct2_dir), device="cpu", compute_type="int8", cpu_threads=4
        )
        assert result is mock_model

    def test_returns_cached_model_on_second_call(self, tmp_path: Path) -> None:
        ct2_dir = tmp_path / "model"
        ct2_dir.mkdir()
        (ct2_dir / "model.bin").write_bytes(b"")

        mock_model = MagicMock()
        with patch("classifier.WhisperModel", return_value=mock_model) as MockModel:
            r1 = load_thai_model(str(ct2_dir), "cpu", "int8")
            r2 = load_thai_model(str(ct2_dir), "cpu", "int8")
        assert MockModel.call_count == 1
        assert r1 is r2

    def test_hf_model_triggers_conversion(self, tmp_path: Path) -> None:
        """load_thai_model should call _ensure_ct2_model for an HF model ID."""
        fake_ct2_path = str(tmp_path / "converted")
        mock_model = MagicMock()
        with patch("classifier._ensure_ct2_model", return_value=fake_ct2_path) as mock_ensure:
            with patch("classifier.WhisperModel", return_value=mock_model):
                load_thai_model("org/th-model", "cpu", "int8")
        mock_ensure.assert_called_once_with("org/th-model", "int8")
