"""Local filesystem storage backend."""

from __future__ import annotations

import logging
from pathlib import Path

from storage.base import StorageBackend

logger = logging.getLogger(__name__)


class LocalStorage(StorageBackend):
    """Reads audio files from a local directory."""

    def __init__(self, base_path: str, audio_extensions: list[str]) -> None:
        self.base_path = Path(base_path)
        self.audio_extensions = {ext.lower() for ext in audio_extensions}

        if not self.base_path.exists():
            raise FileNotFoundError(f"Input path does not exist: {self.base_path}")
        if not self.base_path.is_dir():
            raise NotADirectoryError(f"Input path is not a directory: {self.base_path}")

    def list_audio_files(self) -> list[str]:
        """Recursively find all audio files under base_path."""
        files: list[str] = []
        for p in sorted(self.base_path.rglob("*")):
            if p.is_file() and p.suffix.lower() in self.audio_extensions:
                files.append(str(p))
        logger.info("Found %d audio files in %s", len(files), self.base_path)
        return files

    def get_local_path(self, file_ref: str) -> Path:
        """For local storage the file_ref is already a local path."""
        return Path(file_ref)
