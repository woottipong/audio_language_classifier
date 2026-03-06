"""Unit tests for utils.py — file size, duration, validation, directories."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from exceptions import ConfigurationError
from utils import (
    check_file_size,
    ensure_directory_exists,
    get_google_project_id,
    get_project_id_from_credentials,
    validate_file_for_processing,
)


class TestCheckFileSize:
    def test_small_file_is_valid(self, tmp_path: Path) -> None:
        f = tmp_path / "small.wav"
        f.write_bytes(b"\x00" * 1024)  # 1 KB
        is_valid, size_mb = check_file_size(f, max_size_mb=10)
        assert is_valid is True
        assert size_mb < 1.0

    def test_large_file_is_invalid(self, tmp_path: Path) -> None:
        f = tmp_path / "large.wav"
        f.write_bytes(b"\x00" * (11 * 1024 * 1024))  # 11 MB
        is_valid, size_mb = check_file_size(f, max_size_mb=10)
        assert is_valid is False
        assert size_mb > 10.0

    def test_returns_tuple(self, tmp_path: Path) -> None:
        f = tmp_path / "f.wav"
        f.write_bytes(b"\x00" * 100)
        result = check_file_size(f)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_exact_limit_is_valid(self, tmp_path: Path) -> None:
        f = tmp_path / "exact.wav"
        f.write_bytes(b"\x00" * (10 * 1024 * 1024))  # exactly 10 MB
        is_valid, _ = check_file_size(f, max_size_mb=10)
        assert is_valid is True


class TestEnsureDirectoryExists:
    def test_creates_new_directory(self, tmp_path: Path) -> None:
        new_dir = tmp_path / "new_dir"
        assert not new_dir.exists()
        ensure_directory_exists(new_dir)
        assert new_dir.is_dir()

    def test_nested_directory(self, tmp_path: Path) -> None:
        nested = tmp_path / "a" / "b" / "c"
        ensure_directory_exists(nested)
        assert nested.is_dir()

    def test_existing_directory_no_error(self, tmp_path: Path) -> None:
        ensure_directory_exists(tmp_path)  # already exists — should not raise

    def test_idempotent(self, tmp_path: Path) -> None:
        new_dir = tmp_path / "idempotent"
        ensure_directory_exists(new_dir)
        ensure_directory_exists(new_dir)  # second call — should not raise
        assert new_dir.is_dir()


class TestValidateFileForProcessing:
    def test_no_constraints_always_passes(self, tmp_path: Path) -> None:
        f = tmp_path / "audio.wav"
        f.write_bytes(b"\x00" * 1024)
        is_valid, reason = validate_file_for_processing(f)
        assert is_valid is True
        assert reason == ""

    def test_size_constraint_passes(self, tmp_path: Path) -> None:
        f = tmp_path / "audio.wav"
        f.write_bytes(b"\x00" * 1024)  # 1 KB
        is_valid, _ = validate_file_for_processing(f, max_size_mb=10)
        assert is_valid is True

    def test_size_constraint_fails(self, tmp_path: Path) -> None:
        f = tmp_path / "big.wav"
        f.write_bytes(b"\x00" * (15 * 1024 * 1024))  # 15 MB
        is_valid, reason = validate_file_for_processing(f, max_size_mb=10)
        assert is_valid is False
        assert "exceeds" in reason

    def test_duration_constraint_passes(self, tmp_path: Path) -> None:
        f = tmp_path / "audio.wav"
        f.write_bytes(b"\x00" * 1024)
        with patch("utils.get_audio_duration", return_value=20.0):
            is_valid, _ = validate_file_for_processing(f, max_duration_seconds=30)
        assert is_valid is True

    def test_duration_constraint_fails(self, tmp_path: Path) -> None:
        f = tmp_path / "audio.wav"
        f.write_bytes(b"\x00" * 1024)
        with patch("utils.get_audio_duration", return_value=60.0):
            is_valid, reason = validate_file_for_processing(f, max_duration_seconds=30)
        assert is_valid is False
        assert "exceeds" in reason


class TestGetProjectIdFromCredentials:
    def test_reads_project_id(self, tmp_path: Path) -> None:
        creds = {"project_id": "my-project", "type": "service_account"}
        f = tmp_path / "creds.json"
        f.write_text(json.dumps(creds))
        assert get_project_id_from_credentials(str(f)) == "my-project"

    def test_raises_when_no_project_id(self, tmp_path: Path) -> None:
        f = tmp_path / "creds.json"
        f.write_text(json.dumps({"type": "service_account"}))
        with pytest.raises(ConfigurationError, match="No project_id"):
            get_project_id_from_credentials(str(f))

    def test_raises_when_file_missing(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigurationError, match="Failed to read"):
            get_project_id_from_credentials(str(tmp_path / "missing.json"))

    def test_raises_on_invalid_json(self, tmp_path: Path) -> None:
        f = tmp_path / "bad.json"
        f.write_text("not json {{{")
        with pytest.raises(ConfigurationError, match="Failed to read"):
            get_project_id_from_credentials(str(f))


class TestGetGoogleProjectId:
    def test_reads_from_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "env-project")
        monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
        assert get_google_project_id() == "env-project"

    def test_reads_from_credentials_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        creds = {"project_id": "creds-project", "type": "service_account"}
        f = tmp_path / "creds.json"
        f.write_text(json.dumps(creds))
        monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(f))
        assert get_google_project_id() == "creds-project"

    def test_raises_when_neither_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
        monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
        with pytest.raises(ConfigurationError):
            get_google_project_id()
