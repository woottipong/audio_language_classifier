"""Performance monitoring and metrics utilities."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Track performance metrics for audio processing."""
    
    total_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    
    total_duration_seconds: float = 0.0
    total_processing_time: float = 0.0
    
    model_load_time: float = 0.0
    
    # Per-file timing
    file_timings: dict[str, float] = field(default_factory=dict)
    
    # Google STT specific
    google_stt_calls: int = 0
    google_stt_successes: int = 0
    google_stt_failures: int = 0
    google_stt_fallbacks: int = 0
    
    # Memory tracking
    peak_memory_mb: float = 0.0
    
    def add_file_timing(self, filename: str, processing_time: float) -> None:
        """Record processing time for a file.
        
        Args:
            filename: Name of the file
            processing_time: Time taken to process in seconds
        """
        self.file_timings[filename] = processing_time
    
    def record_google_stt_call(self, success: bool, fallback: bool = False) -> None:
        """Record a Google STT API call.
        
        Args:
            success: Whether the call succeeded
            fallback: Whether this was a fallback to Whisper
        """
        self.google_stt_calls += 1
        if success:
            self.google_stt_successes += 1
        else:
            self.google_stt_failures += 1
        if fallback:
            self.google_stt_fallbacks += 1
    
    def get_throughput(self) -> float:
        """Calculate overall throughput in files per second.
        
        Returns:
            Files per second
        """
        if self.total_processing_time > 0:
            return self.total_files / self.total_processing_time
        return 0.0
    
    def get_average_file_time(self) -> float:
        """Calculate average processing time per file.
        
        Returns:
            Average seconds per file
        """
        if self.total_files > 0:
            return self.total_processing_time / self.total_files
        return 0.0
    
    def get_google_stt_success_rate(self) -> float:
        """Calculate Google STT success rate.
        
        Returns:
            Success rate as percentage (0-100)
        """
        if self.google_stt_calls > 0:
            return (self.google_stt_successes / self.google_stt_calls) * 100
        return 0.0
    
    def get_summary(self) -> dict:
        """Get performance summary as dictionary.
        
        Returns:
            Dictionary with performance metrics
        """
        return {
            "total_files": self.total_files,
            "successful_files": self.successful_files,
            "failed_files": self.failed_files,
            "total_processing_time": round(self.total_processing_time, 2),
            "throughput_files_per_sec": round(self.get_throughput(), 2),
            "average_time_per_file": round(self.get_average_file_time(), 2),
            "model_load_time": round(self.model_load_time, 2),
            "google_stt": {
                "total_calls": self.google_stt_calls,
                "successes": self.google_stt_successes,
                "failures": self.google_stt_failures,
                "fallbacks": self.google_stt_fallbacks,
                "success_rate": round(self.get_google_stt_success_rate(), 1),
            },
            "peak_memory_mb": round(self.peak_memory_mb, 2),
        }
    
    def log_summary(self) -> None:
        """Log performance summary."""
        logger.info("=== Performance Summary ===")
        logger.info("Total files: %d", self.total_files)
        logger.info("Successful: %d | Failed: %d", self.successful_files, self.failed_files)
        logger.info("Total time: %.2fs", self.total_processing_time)
        logger.info("Throughput: %.2f files/s", self.get_throughput())
        logger.info("Avg time/file: %.2fs", self.get_average_file_time())
        logger.info("Model load time: %.2fs", self.model_load_time)
        
        if self.google_stt_calls > 0:
            logger.info("Google STT calls: %d", self.google_stt_calls)
            logger.info("Success rate: %.1f%%", self.get_google_stt_success_rate())
            logger.info("Fallbacks to Whisper: %d", self.google_stt_fallbacks)
        
        if self.peak_memory_mb > 0:
            logger.info("Peak memory: %.2f MB", self.peak_memory_mb)


class PerformanceTimer:
    """Context manager for timing operations."""
    
    def __init__(self, name: str = "Operation"):
        """Initialize timer.
        
        Args:
            name: Name of the operation being timed
        """
        self.name = name
        self.start_time: float | None = None
        self.elapsed: float = 0.0
    
    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and log result."""
        if self.start_time is not None:
            self.elapsed = time.time() - self.start_time
            logger.debug("%s took %.3fs", self.name, self.elapsed)
        return False
    
    def get_elapsed(self) -> float:
        """Get elapsed time.
        
        Returns:
            Elapsed time in seconds
        """
        return self.elapsed
