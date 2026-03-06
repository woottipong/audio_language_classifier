"""Integration tests — pipeline without a real Whisper model.

These tests exercise the combination of LocalStorage → (mocked detection) → Exporter
and verify that components wire together correctly end-to-end.

Deliberately avoiding real model inference (no download required):
  - Use pytest-mock to stub classifier.detect_language
  - Use real LocalStorage, real ResultCache, real Exporter
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from cache import ResultCache
from classifier import DetectionResult
from exporter import export_csv, export_json
from storage.local import LocalStorage


AUDIO_EXTS = [".wav", ".mp3", ".flac", ".ogg", ".m4a"]

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def audio_dir(tmp_path: Path) -> Path:
    """Temp directory with two minimal audio stub files."""
    (tmp_path / "english.wav").write_bytes(b"\x00" * 1024)
    (tmp_path / "thai.mp3").write_bytes(b"\x00" * 1024)
    return tmp_path


@pytest.fixture
def out_dir(tmp_path: Path) -> Path:
    d = tmp_path / "output"
    d.mkdir()
    return d


# ---------------------------------------------------------------------------
# Storage → Exporter
# ---------------------------------------------------------------------------


class TestStorageToExporter:
    """LocalStorage discovers files, results flow straight to Exporter."""

    def test_csv_output_contains_discovered_files(
        self, audio_dir: Path, out_dir: Path
    ) -> None:
        storage = LocalStorage(str(audio_dir), AUDIO_EXTS)
        audio_files = storage.list_audio_files()

        # export_csv keys must match CSV_FIELDNAMES in constants.py
        results: list[dict[str, Any]] = [
            {
                "file_name": Path(f).name,
                "detected_lang": "en",
                "probability": 0.99,
                "is_english": True,
                "duration": 5.0,
            }
            for f in audio_files
        ]

        csv_path = export_csv(results, str(out_dir))

        with open(csv_path, encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))

        assert len(rows) == len(audio_files)
        discovered = {Path(f).name for f in audio_files}
        exported = {r["file_name"] for r in rows}
        assert discovered == exported

    def test_json_output_contains_discovered_files(
        self, audio_dir: Path, out_dir: Path
    ) -> None:
        storage = LocalStorage(str(audio_dir), AUDIO_EXTS)
        audio_files = storage.list_audio_files()

        results: list[dict[str, Any]] = [
            {
                "file_name": Path(f).name,
                "detected_lang": "th",
                "probability": 0.95,
                "is_english": False,
                "duration": 10.0,
                "transcription": "สวัสดี",
                "transcription_source": "whisper",
            }
            for f in audio_files
        ]

        json_path = export_json(results, str(out_dir))

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert len(data) == len(audio_files)


# ---------------------------------------------------------------------------
# Storage → (mock detection) → Exporter
# ---------------------------------------------------------------------------


class TestDetectionPipeline:
    """Wires storage, mocked detect_language, and export together."""

    def test_pipeline_processes_all_files(
        self, audio_dir: Path, out_dir: Path
    ) -> None:
        storage = LocalStorage(str(audio_dir), AUDIO_EXTS)
        audio_files = storage.list_audio_files()

        fake_result = DetectionResult(
            file_name="stub.wav",
            detected_lang="en",
            probability=0.98,
            is_english=True,
            duration=3.0,
        )

        with patch("classifier.detect_language", return_value=fake_result):
            import classifier  # noqa: PLC0415

            processed: list[dict[str, Any]] = []
            for file_path in audio_files:
                r = classifier.detect_language(
                    file_path=file_path,
                    model=MagicMock(),
                    transcribe=False,
                )
                processed.append(r.to_dict())

        csv_path = export_csv(processed, str(out_dir))

        with open(csv_path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        assert len(rows) == len(audio_files)
        assert all(r["detected_lang"] == "en" for r in rows)

    def test_empty_directory_produces_empty_outputs(
        self, tmp_path: Path, out_dir: Path
    ) -> None:
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        storage = LocalStorage(str(empty_dir), AUDIO_EXTS)
        audio_files = storage.list_audio_files()
        assert audio_files == []

        export_csv([], str(out_dir))
        json_path = export_json([], str(out_dir))

        with open(json_path, encoding="utf-8") as f:
            assert json.load(f) == []


# ---------------------------------------------------------------------------
# Caching integration
# ---------------------------------------------------------------------------


class TestCachingIntegration:
    """ResultCache integrates with mocked detection: second call is a cache hit."""

    def test_cache_hit_on_second_call(self, tmp_path: Path) -> None:
        cache_dir = tmp_path / ".cache"
        audio_file = tmp_path / "sample.wav"
        audio_file.write_bytes(b"\x00" * 2048)

        cache = ResultCache(cache_dir=cache_dir, ttl_hours=1)

        stored_result: dict[str, Any] = {
            "detected_lang": "en",
            "probability": 0.99,
            "duration": 5.0,
        }

        # First call — no cache entry
        assert cache.get(audio_file) is None

        # Store result
        cache.set(audio_file, stored_result)

        # Second call — should hit cache
        cached = cache.get(audio_file)
        assert cached is not None
        assert cached["result"]["detected_lang"] == "en"
        assert cached["result"]["probability"] == pytest.approx(0.99)

    def test_cache_miss_after_file_modification(self, tmp_path: Path) -> None:
        cache_dir = tmp_path / ".cache"
        audio_file = tmp_path / "sample.wav"
        audio_file.write_bytes(b"\x00" * 2048)

        cache = ResultCache(cache_dir=cache_dir, ttl_hours=1)
        cache.set(audio_file, {"detected_lang": "en"})

        # Modify the file — SHA256 changes, so cache miss
        audio_file.write_bytes(b"\xFF" * 2048)
        assert cache.get(audio_file) is None

    def test_clear_all_invalidates_cache(self, tmp_path: Path) -> None:
        cache_dir = tmp_path / ".cache"
        audio_file = tmp_path / "sample.wav"
        audio_file.write_bytes(b"\x00" * 512)

        cache = ResultCache(cache_dir=cache_dir, ttl_hours=1)
        cache.set(audio_file, {"detected_lang": "th"})

        assert cache.get(audio_file) is not None

        cache.clear_all()

        assert cache.get(audio_file) is None
