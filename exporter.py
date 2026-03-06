"""Export classification results to CSV and JSON."""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path

from constants import CSV_FIELDNAMES, CSV_FIELDNAMES_NO_TRANSCRIPTION
from exceptions import StorageError
from utils import ensure_directory_exists

logger = logging.getLogger(__name__)


def export_csv(results: list[dict], output_dir: str, include_transcription: bool = False) -> Path:
    """Write results to summary.csv.
    
    Args:
        results: List of classification result dictionaries
        output_dir: Output directory path
        include_transcription: Whether to include transcription fields
        
    Returns:
        Path to the created CSV file
        
    Raises:
        StorageError: If CSV export fails
    """
    try:
        out = Path(output_dir)
        ensure_directory_exists(out)
        csv_path = out / "summary.csv"

        fieldnames = CSV_FIELDNAMES if include_transcription else CSV_FIELDNAMES_NO_TRANSCRIPTION

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(results)

        logger.info("CSV written to %s (%d rows)", csv_path, len(results))
        return csv_path
    except Exception as e:
        raise StorageError(f"Failed to export CSV: {e}")


def export_json(results: list[dict], output_dir: str) -> Path:
    """Write results to summary.json.
    
    Args:
        results: List of classification result dictionaries
        output_dir: Output directory path
        
    Returns:
        Path to the created JSON file
        
    Raises:
        StorageError: If JSON export fails
    """
    try:
        out = Path(output_dir)
        ensure_directory_exists(out)
        json_path = out / "summary.json"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info("JSON written to %s (%d records)", json_path, len(results))
        return json_path
    except Exception as e:
        raise StorageError(f"Failed to export JSON: {e}")
