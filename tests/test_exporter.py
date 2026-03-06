"""Unit tests for exporter.py — CSV and JSON export."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from exporter import export_csv, export_json
from exceptions import StorageError


class TestExportCsv:
    def test_creates_file(self, sample_results: list[dict], output_dir: Path) -> None:
        path = export_csv(sample_results, str(output_dir))
        assert path.exists()
        assert path.name == "summary.csv"

    def test_header_with_transcription(self, sample_results: list[dict], output_dir: Path) -> None:
        path = export_csv(sample_results, str(output_dir), include_transcription=True)
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert "transcription" in reader.fieldnames
            assert "transcription_source" in reader.fieldnames

    def test_header_without_transcription(self, sample_results: list[dict], output_dir: Path) -> None:
        path = export_csv(sample_results, str(output_dir), include_transcription=False)
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert "transcription" not in reader.fieldnames

    def test_row_count(self, sample_results: list[dict], output_dir: Path) -> None:
        path = export_csv(sample_results, str(output_dir), include_transcription=True)
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == len(sample_results)

    def test_row_values(self, sample_results: list[dict], output_dir: Path) -> None:
        path = export_csv(sample_results, str(output_dir), include_transcription=True)
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert rows[0]["file_name"] == "english.wav"
        assert rows[1]["detected_lang"] == "th"

    def test_unicode_content(self, output_dir: Path) -> None:
        results = [{"file_name": "thai.mp3", "detected_lang": "th", "probability": 0.9,
                    "is_english": False, "duration": 3.0, "transcription": "สวัสดีครับ",
                    "transcription_source": "google_chirp_2"}]
        path = export_csv(results, str(output_dir), include_transcription=True)
        content = path.read_text(encoding="utf-8")
        assert "สวัสดีครับ" in content

    def test_empty_results(self, output_dir: Path) -> None:
        path = export_csv([], str(output_dir))
        assert path.exists()
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert rows == []

    def test_creates_output_dir_if_missing(self, sample_results: list[dict], tmp_path: Path) -> None:
        new_dir = tmp_path / "new" / "nested"
        export_csv(sample_results, str(new_dir))
        assert new_dir.is_dir()

    def test_raises_storage_error_on_invalid_path(self, sample_results: list[dict]) -> None:
        with pytest.raises(StorageError):
            export_csv(sample_results, "/dev/null/impossible/path")


class TestExportJson:
    def test_creates_file(self, sample_results: list[dict], output_dir: Path) -> None:
        path = export_json(sample_results, str(output_dir))
        assert path.exists()
        assert path.name == "summary.json"

    def test_valid_json(self, sample_results: list[dict], output_dir: Path) -> None:
        path = export_json(sample_results, str(output_dir))
        data = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(data, list)
        assert len(data) == len(sample_results)

    def test_values_preserved(self, sample_results: list[dict], output_dir: Path) -> None:
        path = export_json(sample_results, str(output_dir))
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data[0]["file_name"] == "english.wav"
        assert data[1]["detected_lang"] == "th"

    def test_unicode_not_escaped(self, output_dir: Path) -> None:
        results = [{"transcription": "สวัสดีครับ"}]
        path = export_json(results, str(output_dir))
        content = path.read_text(encoding="utf-8")
        assert "สวัสดีครับ" in content

    def test_empty_results(self, output_dir: Path) -> None:
        path = export_json([], str(output_dir))
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data == []

    def test_creates_output_dir_if_missing(self, sample_results: list[dict], tmp_path: Path) -> None:
        new_dir = tmp_path / "output"
        export_json(sample_results, str(new_dir))
        assert new_dir.is_dir()

    def test_raises_storage_error_on_invalid_path(self, sample_results: list[dict]) -> None:
        with pytest.raises(StorageError):
            export_json(sample_results, "/dev/null/impossible/path")
