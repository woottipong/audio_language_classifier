"""Shared pytest fixtures for the audio language classifier test suite."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    """Return a temporary directory (alias for tmp_path)."""
    return tmp_path


@pytest.fixture
def audio_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with dummy audio files."""
    audio = tmp_path / "audio"
    audio.mkdir()
    (audio / "english.wav").write_bytes(b"\x00" * 1024)
    (audio / "thai.mp3").write_bytes(b"\x00" * 2048)
    (audio / "ignored.txt").write_text("not audio")
    return audio


@pytest.fixture
def empty_audio_dir(tmp_path: Path) -> Path:
    """Create a temporary empty directory."""
    d = tmp_path / "empty"
    d.mkdir()
    return d


@pytest.fixture
def sample_results() -> list[dict]:
    """Return a list of sample detection result dicts."""
    return [
        {
            "file_name": "english.wav",
            "detected_lang": "en",
            "probability": 0.98,
            "is_english": True,
            "duration": 5.2,
            "transcription": "Hello world",
            "transcription_source": "whisper",
        },
        {
            "file_name": "thai.mp3",
            "detected_lang": "th",
            "probability": 0.95,
            "is_english": False,
            "duration": 8.1,
            "transcription": "สวัสดีครับ",
            "transcription_source": "google_chirp_2",
        },
    ]


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory."""
    out = tmp_path / "results"
    out.mkdir()
    return out


@pytest.fixture
def fake_credentials_file(tmp_path: Path) -> Path:
    """Write a minimal Google credentials JSON and return its path."""
    creds = {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "key-id",
        "client_email": "test@test-project.iam.gserviceaccount.com",
    }
    creds_file = tmp_path / "credentials.json"
    creds_file.write_text(json.dumps(creds))
    return creds_file
