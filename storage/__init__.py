"""Storage backends for audio file access."""

from storage.base import StorageBackend
from storage.local import LocalStorage

__all__ = ["StorageBackend", "LocalStorage"]
