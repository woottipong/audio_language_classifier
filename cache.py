"""Caching layer for audio classification results."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class ResultCache:
    """Cache for audio classification results based on file hash."""
    
    def __init__(self, cache_dir: Path, ttl_hours: int = 24):
        """Initialize result cache.
        
        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time-to-live for cache entries in hours
        """
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_hours * 3600
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Cache initialized at %s (TTL: %dh)", self.cache_dir, ttl_hours)
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Hex digest of file hash
        """
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    def _get_cache_path(self, file_hash: str) -> Path:
        """Get cache file path for a given hash.
        
        Args:
            file_hash: File hash
            
        Returns:
            Path to cache file
        """
        return self.cache_dir / f"{file_hash}.json"
    
    def get(self, file_path: Path) -> dict | None:
        """Get cached result for a file.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Cached result dictionary or None if not found/expired
        """
        try:
            file_hash = self._get_file_hash(file_path)
            cache_path = self._get_cache_path(file_hash)
            
            if not cache_path.exists():
                logger.debug("Cache miss: %s", file_path.name)
                return None
            
            # Check if cache is expired
            cache_age = time.time() - cache_path.stat().st_mtime
            if cache_age > self.ttl_seconds:
                logger.debug("Cache expired: %s (age: %.1fh)", file_path.name, cache_age / 3600)
                cache_path.unlink()  # Delete expired cache
                return None
            
            # Load cached result
            with open(cache_path, "r", encoding="utf-8") as f:
                result = json.load(f)
            
            logger.info("Cache hit: %s (age: %.1fm)", file_path.name, cache_age / 60)
            return result
            
        except Exception as e:
            logger.warning("Error reading cache for %s: %s", file_path.name, e)
            return None
    
    def set(self, file_path: Path, result: dict) -> None:
        """Cache result for a file.
        
        Args:
            file_path: Path to the audio file
            result: Result dictionary to cache
        """
        try:
            file_hash = self._get_file_hash(file_path)
            cache_path = self._get_cache_path(file_hash)
            
            # Add metadata
            cache_entry = {
                "file_name": file_path.name,
                "cached_at": time.time(),
                "result": result
            }
            
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_entry, f, indent=2, ensure_ascii=False)
            
            logger.debug("Cached result: %s", file_path.name)
            
        except Exception as e:
            logger.warning("Error caching result for %s: %s", file_path.name, e)
    
    def clear_expired(self) -> int:
        """Clear expired cache entries.
        
        Returns:
            Number of entries cleared
        """
        cleared = 0
        current_time = time.time()
        
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_age = current_time - cache_file.stat().st_mtime
                if cache_age > self.ttl_seconds:
                    cache_file.unlink()
                    cleared += 1
            
            if cleared > 0:
                logger.info("Cleared %d expired cache entries", cleared)
                
        except Exception as e:
            logger.warning("Error clearing expired cache: %s", e)
        
        return cleared
    
    def clear_all(self) -> int:
        """Clear all cache entries.
        
        Returns:
            Number of entries cleared
        """
        cleared = 0
        
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
                cleared += 1
            
            logger.info("Cleared all cache (%d entries)", cleared)
            
        except Exception as e:
            logger.warning("Error clearing cache: %s", e)
        
        return cleared
    
    def get_stats(self) -> dict:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            total_entries = len(cache_files)
            
            if total_entries == 0:
                return {
                    "total_entries": 0,
                    "total_size_mb": 0.0,
                    "oldest_entry_hours": 0.0,
                    "newest_entry_hours": 0.0,
                }
            
            total_size = sum(f.stat().st_size for f in cache_files)
            current_time = time.time()
            
            ages = [(current_time - f.stat().st_mtime) / 3600 for f in cache_files]
            
            return {
                "total_entries": total_entries,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "oldest_entry_hours": round(max(ages), 1),
                "newest_entry_hours": round(min(ages), 1),
            }
            
        except Exception as e:
            logger.warning("Error getting cache stats: %s", e)
            return {
                "total_entries": 0,
                "total_size_mb": 0.0,
                "oldest_entry_hours": 0.0,
                "newest_entry_hours": 0.0,
            }
