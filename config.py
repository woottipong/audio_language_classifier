"""Configuration for Audio Language Classifier & Summarizer."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from constants import (
    CACHE_ENABLED_BY_DEFAULT,
    DEFAULT_CACHE_DIR,
    DEFAULT_CACHE_TTL_HOURS,
    DEFAULT_COMPUTE_TYPE,
    DEFAULT_DEVICE,
    DEFAULT_LOG_LEVEL,
    DEFAULT_MAX_WORKERS,
    DEFAULT_MODEL_SIZE,
    SUPPORTED_AUDIO_EXTENSIONS,
)
from exceptions import ConfigurationError


@dataclass
class AppConfig:
    """Application configuration with sensible defaults."""

    input_path: str = "./audio_files"
    output_dir: str = "./results"
    storage_type: str = "local"
    
    model_size: str = DEFAULT_MODEL_SIZE
    device: str = DEFAULT_DEVICE
    compute_type: str = DEFAULT_COMPUTE_TYPE
    
    max_workers: int = DEFAULT_MAX_WORKERS
    enable_transcription: bool = False
    use_google_for_thai: bool = False
    preprocess_audio: bool = False
    
    audio_extensions: list[str] = field(
        default_factory=lambda: SUPPORTED_AUDIO_EXTENSIONS.copy()
    )
    
    log_level: str = DEFAULT_LOG_LEVEL
    log_file: str = ""
    
    # Cache options
    enable_cache: bool = CACHE_ENABLED_BY_DEFAULT
    cache_dir: str = DEFAULT_CACHE_DIR
    cache_ttl_hours: int = DEFAULT_CACHE_TTL_HOURS
    
    # Performance options
    show_timing: bool = False
    
    def validate(self) -> None:
        """Validate configuration settings.
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not Path(self.input_path).exists():
            raise ConfigurationError(f"Input path does not exist: {self.input_path}")
        
        if not Path(self.input_path).is_dir():
            raise ConfigurationError(f"Input path is not a directory: {self.input_path}")
        
        if self.max_workers < 1:
            raise ConfigurationError(f"max_workers must be >= 1, got {self.max_workers}")
        
        valid_devices = ["auto", "cpu", "cuda"]
        if self.device not in valid_devices:
            raise ConfigurationError(
                f"device must be one of {valid_devices}, got {self.device}"
            )
        
        valid_compute_types = ["int8", "float16", "float32"]
        if self.compute_type not in valid_compute_types:
            raise ConfigurationError(
                f"compute_type must be one of {valid_compute_types}, got {self.compute_type}"
            )
        
        if self.use_google_for_thai:
            if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                raise ConfigurationError(
                    "use_google_for_thai requires GOOGLE_APPLICATION_CREDENTIALS to be set"
                )
