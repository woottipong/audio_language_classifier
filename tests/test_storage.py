"""Unit tests for storage/local.py — LocalStorage file listing."""

from __future__ import annotations

from pathlib import Path

import pytest

from storage.local import LocalStorage


AUDIO_EXTS = [".wav", ".mp3", ".flac", ".ogg", ".m4a"]


@pytest.fixture
def populated_dir(tmp_path: Path) -> Path:
    """Directory with a mix of audio and non-audio files."""
    (tmp_path / "a.wav").write_bytes(b"\x00" * 100)
    (tmp_path / "b.mp3").write_bytes(b"\x00" * 200)
    (tmp_path / "c.flac").write_bytes(b"\x00" * 300)
    (tmp_path / "notes.txt").write_text("ignore me")
    (tmp_path / "image.png").write_bytes(b"\x89PNG")
    return tmp_path


@pytest.fixture
def nested_dir(tmp_path: Path) -> Path:
    """Directory with audio files in subdirectories."""
    sub = tmp_path / "sub"
    sub.mkdir()
    (tmp_path / "root.wav").write_bytes(b"\x00" * 100)
    (sub / "nested.mp3").write_bytes(b"\x00" * 100)
    return tmp_path


class TestLocalStorageInit:
    def test_raises_for_missing_path(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            LocalStorage(str(tmp_path / "missing"), AUDIO_EXTS)

    def test_raises_for_file_not_dir(self, tmp_path: Path) -> None:
        f = tmp_path / "file.txt"
        f.write_text("hi")
        with pytest.raises(NotADirectoryError):
            LocalStorage(str(f), AUDIO_EXTS)

    def test_valid_dir_ok(self, tmp_path: Path) -> None:
        storage = LocalStorage(str(tmp_path), AUDIO_EXTS)
        assert storage.base_path == tmp_path


class TestLocalStorageListFiles:
    def test_lists_audio_files(self, populated_dir: Path) -> None:
        storage = LocalStorage(str(populated_dir), AUDIO_EXTS)
        files = storage.list_audio_files()
        names = {Path(f).name for f in files}
        assert "a.wav" in names
        assert "b.mp3" in names
        assert "c.flac" in names

    def test_excludes_non_audio(self, populated_dir: Path) -> None:
        storage = LocalStorage(str(populated_dir), AUDIO_EXTS)
        files = storage.list_audio_files()
        names = {Path(f).name for f in files}
        assert "notes.txt" not in names
        assert "image.png" not in names

    def test_empty_directory(self, tmp_path: Path) -> None:
        storage = LocalStorage(str(tmp_path), AUDIO_EXTS)
        assert storage.list_audio_files() == []

    def test_recursive_search(self, nested_dir: Path) -> None:
        storage = LocalStorage(str(nested_dir), AUDIO_EXTS)
        files = storage.list_audio_files()
        names = {Path(f).name for f in files}
        assert "root.wav" in names
        assert "nested.mp3" in names

    def test_returns_strings(self, populated_dir: Path) -> None:
        storage = LocalStorage(str(populated_dir), AUDIO_EXTS)
        for f in storage.list_audio_files():
            assert isinstance(f, str)

    def test_extension_case_insensitive(self, tmp_path: Path) -> None:
        (tmp_path / "UPPER.WAV").write_bytes(b"\x00" * 100)
        (tmp_path / "Mixed.Mp3").write_bytes(b"\x00" * 100)
        storage = LocalStorage(str(tmp_path), AUDIO_EXTS)
        files = storage.list_audio_files()
        names = {Path(f).name for f in files}
        assert "UPPER.WAV" in names
        assert "Mixed.Mp3" in names

    def test_custom_extensions_only(self, tmp_path: Path) -> None:
        (tmp_path / "a.wav").write_bytes(b"\x00" * 100)
        (tmp_path / "b.mp3").write_bytes(b"\x00" * 100)
        storage = LocalStorage(str(tmp_path), [".wav"])
        files = storage.list_audio_files()
        names = {Path(f).name for f in files}
        assert "a.wav" in names
        assert "b.mp3" not in names


class TestLocalStorageGetLocalPath:
    def test_returns_path_object(self, tmp_path: Path) -> None:
        storage = LocalStorage(str(tmp_path), AUDIO_EXTS)
        result = storage.get_local_path("/some/path/audio.wav")
        assert isinstance(result, Path)

    def test_path_matches_input(self, tmp_path: Path) -> None:
        storage = LocalStorage(str(tmp_path), AUDIO_EXTS)
        result = storage.get_local_path("/data/audio.wav")
        assert str(result) == "/data/audio.wav"
