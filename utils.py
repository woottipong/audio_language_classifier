"""Utility functions for the audio language classifier."""

from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path

from constants import MAX_FILE_SIZE_MB
from exceptions import ConfigurationError, FileSizeError

logger = logging.getLogger(__name__)


def get_project_id_from_credentials(credentials_path: str) -> str:
    """Extract project ID from Google Cloud credentials JSON file.
    
    Args:
        credentials_path: Path to the credentials JSON file
        
    Returns:
        Project ID string
        
    Raises:
        ConfigurationError: If project ID cannot be extracted
    """
    try:
        with open(credentials_path, "r") as f:
            creds_data = json.load(f)
            project_id = creds_data.get("project_id")
            
        if not project_id:
            raise ConfigurationError(
                f"No project_id found in credentials file: {credentials_path}"
            )
            
        return project_id
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise ConfigurationError(
            f"Failed to read project ID from credentials: {e}"
        )


def get_google_project_id() -> str:
    """Get Google Cloud project ID from environment or credentials.
    
    Returns:
        Project ID string
        
    Raises:
        ConfigurationError: If project ID cannot be determined
    """
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    
    if not project_id:
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if credentials_path:
            project_id = get_project_id_from_credentials(credentials_path)
        else:
            raise ConfigurationError(
                "GOOGLE_CLOUD_PROJECT not set and GOOGLE_APPLICATION_CREDENTIALS not found"
            )
    
    return project_id


def check_file_size(file_path: Path, max_size_mb: int = MAX_FILE_SIZE_MB) -> tuple[bool, float]:
    """Check if file size is within the specified limit.
    
    Args:
        file_path: Path to the file to check
        max_size_mb: Maximum file size in megabytes
        
    Returns:
        Tuple of (is_valid, size_mb)
    """
    file_size = file_path.stat().st_size
    size_mb = file_size / (1024 * 1024)
    is_valid = size_mb <= max_size_mb
    return is_valid, size_mb


def get_audio_duration(file_path: Path) -> float:
    """Get audio duration in seconds using ffprobe.
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        Duration in seconds, or 0 if unable to determine
    """
    try:
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                str(file_path)
            ],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            duration = float(data.get('format', {}).get('duration', 0))
            return duration
    except Exception as e:
        logger.warning("Unable to get audio duration for %s: %s", file_path.name, e)
    
    return 0.0


def validate_file_for_processing(
    file_path: Path,
    max_size_mb: int | None = None,
    max_duration_seconds: int | None = None
) -> tuple[bool, str]:
    """Validate if a file can be processed based on size and duration constraints.
    
    Args:
        file_path: Path to the file to validate
        max_size_mb: Maximum file size in MB (optional)
        max_duration_seconds: Maximum duration in seconds (optional)
        
    Returns:
        Tuple of (is_valid, reason)
    """
    if max_size_mb is not None:
        is_valid_size, size_mb = check_file_size(file_path, max_size_mb)
        if not is_valid_size:
            return False, f"File size {size_mb:.1f}MB exceeds limit of {max_size_mb}MB"
    
    if max_duration_seconds is not None:
        duration = get_audio_duration(file_path)
        if duration > max_duration_seconds:
            return False, f"Duration {duration:.1f}s exceeds limit of {max_duration_seconds}s"
    
    return True, ""


def ensure_directory_exists(directory: Path) -> None:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Path to the directory
    """
    directory.mkdir(parents=True, exist_ok=True)
