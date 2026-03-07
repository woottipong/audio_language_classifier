"""Export classification results to CSV."""

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


def append_csv_row(result: dict, csv_path: Path, include_transcription: bool = False) -> None:
    """Append a single result row to a CSV file, writing the header if the file is new or empty.

    Args:
        result: A single classification result dictionary
        csv_path: Absolute path to the target CSV file
        include_transcription: Whether to include transcription fields

    Raises:
        StorageError: If the append operation fails
    """
    try:
        ensure_directory_exists(csv_path.parent)
        fieldnames = CSV_FIELDNAMES if include_transcription else CSV_FIELDNAMES_NO_TRANSCRIPTION
        write_header = not csv_path.exists() or csv_path.stat().st_size == 0
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            if write_header:
                writer.writeheader()
            writer.writerow(result)
        logger.debug("Appended row for %s to %s", result.get("file_name", "?"), csv_path)
    except Exception as e:
        raise StorageError(f"Failed to append CSV row: {e}")


def export_metrics(metrics_data: dict, output_dir: str) -> Path:
    """Write performance metrics summary to metrics.json.

    Args:
        metrics_data: Dictionary from PerformanceMetrics.get_summary()
        output_dir: Output directory path

    Returns:
        Path to the created metrics.json file

    Raises:
        StorageError: If export fails
    """
    try:
        out = Path(output_dir)
        ensure_directory_exists(out)
        metrics_path = out / "metrics.json"
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics_data, f, indent=2)
        logger.info("Metrics written to %s", metrics_path)
        return metrics_path
    except Exception as e:
        raise StorageError(f"Failed to export metrics: {e}")


