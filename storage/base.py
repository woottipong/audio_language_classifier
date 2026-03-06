"""Abstract base class for storage backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class StorageBackend(ABC):
    """Interface that all storage backends must implement."""

    @abstractmethod
    def list_audio_files(self) -> list[str]:
        """Return a list of audio file references (paths or URIs)."""
        ...

    @abstractmethod
    def get_local_path(self, file_ref: str) -> Path:
        """Return a local filesystem path for the given file reference.

        For cloud backends this may involve downloading to a temp directory.
        """
        ...
