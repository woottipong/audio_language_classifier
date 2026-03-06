"""Unit tests for config.py — AppConfig validation."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from config import AppConfig
from constants import DEFAULT_MAX_WORKERS
from exceptions import ConfigurationError


class TestAppConfigDefaults:
    def test_default_model_size(self) -> None:
        cfg = AppConfig()
        assert cfg.model_size == "base"

    def test_default_device(self) -> None:
        assert AppConfig().device == "auto"

    def test_default_compute_type(self) -> None:
        assert AppConfig().compute_type == "int8"

    def test_default_workers(self) -> None:
        assert AppConfig().max_workers == DEFAULT_MAX_WORKERS

    def test_default_cache_disabled(self) -> None:
        assert AppConfig().enable_cache is False

    def test_audio_extensions_are_list(self) -> None:
        cfg = AppConfig()
        assert isinstance(cfg.audio_extensions, list)
        assert ".wav" in cfg.audio_extensions


class TestAppConfigValidation:
    def test_valid_config(self, audio_dir: Path) -> None:
        cfg = AppConfig(input_path=str(audio_dir))
        cfg.validate()  # should not raise

    def test_nonexistent_input_path(self, tmp_path: Path) -> None:
        cfg = AppConfig(input_path=str(tmp_path / "missing"))
        with pytest.raises(ConfigurationError, match="does not exist"):
            cfg.validate()

    def test_input_path_is_file_not_dir(self, tmp_path: Path) -> None:
        f = tmp_path / "file.wav"
        f.write_bytes(b"")
        cfg = AppConfig(input_path=str(f))
        with pytest.raises(ConfigurationError, match="not a directory"):
            cfg.validate()

    def test_max_workers_zero(self, audio_dir: Path) -> None:
        cfg = AppConfig(input_path=str(audio_dir), max_workers=0)
        with pytest.raises(ConfigurationError, match="max_workers"):
            cfg.validate()

    def test_max_workers_negative(self, audio_dir: Path) -> None:
        cfg = AppConfig(input_path=str(audio_dir), max_workers=-1)
        with pytest.raises(ConfigurationError, match="max_workers"):
            cfg.validate()

    def test_max_duration_zero(self, audio_dir: Path) -> None:
        cfg = AppConfig(input_path=str(audio_dir), max_duration=0)
        with pytest.raises(ConfigurationError, match="max_duration"):
            cfg.validate()

    def test_invalid_device(self, audio_dir: Path) -> None:
        cfg = AppConfig(input_path=str(audio_dir), device="gpu")
        with pytest.raises(ConfigurationError, match="device"):
            cfg.validate()

    def test_valid_devices(self, audio_dir: Path) -> None:
        for device in ("auto", "cpu", "cuda"):
            cfg = AppConfig(input_path=str(audio_dir), device=device)
            cfg.validate()  # should not raise

    def test_invalid_compute_type(self, audio_dir: Path) -> None:
        cfg = AppConfig(input_path=str(audio_dir), compute_type="fp16")
        with pytest.raises(ConfigurationError, match="compute_type"):
            cfg.validate()

    def test_valid_compute_types(self, audio_dir: Path) -> None:
        for ct in ("int8", "float16", "float32"):
            cfg = AppConfig(input_path=str(audio_dir), compute_type=ct)
            cfg.validate()  # should not raise

    def test_google_thai_without_credentials(self, audio_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
        cfg = AppConfig(input_path=str(audio_dir), use_google_for_thai=True)
        with pytest.raises(ConfigurationError, match="GOOGLE_APPLICATION_CREDENTIALS"):
            cfg.validate()

    def test_google_thai_with_credentials(
        self, audio_dir: Path, fake_credentials_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(fake_credentials_file))
        cfg = AppConfig(input_path=str(audio_dir), use_google_for_thai=True)
        cfg.validate()  # should not raise
