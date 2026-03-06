"""Unit tests for cache.py — ResultCache get/set/expire/stats."""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from cache import ResultCache


@pytest.fixture
def cache(tmp_path: Path) -> ResultCache:
    return ResultCache(cache_dir=tmp_path / "cache", ttl_hours=1)


@pytest.fixture
def small_file(tmp_path: Path) -> Path:
    f = tmp_path / "audio.wav"
    f.write_bytes(b"\x00" * 512)
    return f


class TestResultCacheInit:
    def test_creates_cache_dir(self, tmp_path: Path) -> None:
        cache_dir = tmp_path / "new_cache"
        assert not cache_dir.exists()
        ResultCache(cache_dir=cache_dir, ttl_hours=1)
        assert cache_dir.is_dir()

    def test_ttl_converted_to_seconds(self, tmp_path: Path) -> None:
        rc = ResultCache(cache_dir=tmp_path, ttl_hours=2)
        assert rc.ttl_seconds == 7200


class TestResultCacheGetSet:
    def test_get_returns_none_for_missing(self, cache: ResultCache, small_file: Path) -> None:
        assert cache.get(small_file) is None

    def test_set_and_get_round_trip(self, cache: ResultCache, small_file: Path) -> None:
        result = {"detected_lang": "en", "probability": 0.99}
        cache.set(small_file, result)
        cached = cache.get(small_file)
        assert cached is not None
        assert cached["result"] == result

    def test_cache_entry_contains_metadata(self, cache: ResultCache, small_file: Path) -> None:
        cache.set(small_file, {"lang": "th"})
        cached = cache.get(small_file)
        assert "file_name" in cached
        assert "cached_at" in cached
        assert cached["file_name"] == small_file.name

    def test_same_file_same_hash(self, cache: ResultCache, small_file: Path) -> None:
        result = {"lang": "en"}
        cache.set(small_file, result)
        assert cache.get(small_file) is not None


class TestResultCacheExpiry:
    def test_expired_entry_returns_none(self, tmp_path: Path, small_file: Path) -> None:
        rc = ResultCache(cache_dir=tmp_path / "cache", ttl_hours=1)
        rc.set(small_file, {"lang": "en"})

        # Advance time past TTL
        with patch("cache.time") as mock_time:
            mock_time.time.return_value = time.time() + 3601
            result = rc.get(small_file)

        assert result is None

    def test_expired_entry_file_deleted(self, tmp_path: Path, small_file: Path) -> None:
        rc = ResultCache(cache_dir=tmp_path / "cache", ttl_hours=1)
        rc.set(small_file, {"lang": "en"})

        cache_files_before = list(rc.cache_dir.glob("*.json"))
        assert len(cache_files_before) == 1

        with patch("cache.time") as mock_time:
            mock_time.time.return_value = time.time() + 3601
            rc.get(small_file)

        cache_files_after = list(rc.cache_dir.glob("*.json"))
        assert len(cache_files_after) == 0


class TestResultCacheClear:
    def test_clear_expired_removes_old_entries(self, tmp_path: Path, small_file: Path) -> None:
        rc = ResultCache(cache_dir=tmp_path / "cache", ttl_hours=1)
        rc.set(small_file, {"lang": "en"})

        # Manually age the cache file
        cache_file = list(rc.cache_dir.glob("*.json"))[0]
        old_mtime = time.time() - 7200  # 2 hours ago
        import os
        os.utime(cache_file, (old_mtime, old_mtime))

        cleared = rc.clear_expired()
        assert cleared == 1
        assert len(list(rc.cache_dir.glob("*.json"))) == 0

    def test_clear_expired_keeps_fresh_entries(self, cache: ResultCache, small_file: Path) -> None:
        cache.set(small_file, {"lang": "en"})
        cleared = cache.clear_expired()
        assert cleared == 0
        assert len(list(cache.cache_dir.glob("*.json"))) == 1

    def test_clear_all_removes_everything(self, cache: ResultCache, tmp_path: Path) -> None:
        for i in range(3):
            f = tmp_path / f"audio{i}.wav"
            f.write_bytes(bytes([i] * 100))
            cache.set(f, {"index": i})

        cleared = cache.clear_all()
        assert cleared == 3
        assert len(list(cache.cache_dir.glob("*.json"))) == 0

    def test_clear_all_empty_cache_returns_zero(self, cache: ResultCache) -> None:
        assert cache.clear_all() == 0


class TestResultCacheStats:
    def test_empty_cache_stats(self, cache: ResultCache) -> None:
        stats = cache.get_stats()
        assert stats["total_entries"] == 0
        assert stats["total_size_mb"] == 0.0

    def test_stats_count_entries(self, cache: ResultCache, tmp_path: Path) -> None:
        for i in range(2):
            f = tmp_path / f"audio{i}.wav"
            f.write_bytes(bytes([i] * 200))
            cache.set(f, {"index": i})

        stats = cache.get_stats()
        assert stats["total_entries"] == 2
        assert stats["total_size_mb"] >= 0.0
        assert "oldest_entry_hours" in stats
        assert "newest_entry_hours" in stats
