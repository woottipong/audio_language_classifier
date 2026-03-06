#!/usr/bin/env python3
"""Audio Language Classifier & Summarizer — CLI Entry Point.

Scans audio files, detects language using faster-whisper, and exports results.
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 10):
    sys.exit(
        f"Error: Python 3.10+ is required (running {sys.version.split()[0]}).\n"
        "Run with the project venv:\n"
        "  source .venv/bin/activate\n"
        "  python main.py ..."
    )

import argparse
import logging
import sys
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

from cache import ResultCache
from classifier import detect_language, load_model
from config import AppConfig
from constants import DEFAULT_MODEL_SIZE, THONBURIAN_MODEL
from exporter import append_csv_row, export_csv, export_json
from performance import PerformanceMetrics, PerformanceTimer
from storage import LocalStorage

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger("audio_classifier")


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def setup_logging(level: str, log_file: str = "") -> None:
    """Configure root logger with console (and optional file) handler."""
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format=fmt, handlers=handlers)


# ---------------------------------------------------------------------------
# CLI argument parser
# ---------------------------------------------------------------------------

def parse_args() -> tuple[AppConfig, bool]:
    """Parse CLI arguments and return an AppConfig."""
    parser = argparse.ArgumentParser(
        description="Detect language of audio files and export summary.",
    )
    parser.add_argument("-i", "--input", default="./audio_files", help="Input directory with audio files")
    parser.add_argument("-o", "--output", default="./results", help="Output directory for summary files")
    parser.add_argument("--model-size", default=DEFAULT_MODEL_SIZE, help="Model size (default: base, or tiny/small/medium/large)")
    parser.add_argument("--use-thonburian", action="store_true", help="Use Thonburian model (fine-tuned for Thai, more accurate but slower)")
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"], help="Compute device")
    parser.add_argument("--compute-type", default="int8", help="Model compute type (int8/float16/float32)")
    parser.add_argument("--max-duration", type=int, default=30, help="Max seconds to read per file")
    parser.add_argument("--max-workers", type=int, default=4, help="Number of concurrent workers")
    parser.add_argument("--transcribe", action="store_true", help="Enable full transcription of audio content")
    parser.add_argument("--use-google-for-thai", action="store_true", help="Use Google Cloud STT (Chirp 2) for Thai language transcription (requires GOOGLE_APPLICATION_CREDENTIALS)")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    parser.add_argument("--log-file", default="", help="Optional log file path")
    
    # Cache options
    parser.add_argument("--enable-cache", action="store_true", help="Enable result caching (skip re-processing unchanged files)")
    parser.add_argument("--cache-dir", default="./.cache", help="Cache directory path")
    parser.add_argument("--cache-ttl", type=int, default=24, help="Cache TTL in hours")
    parser.add_argument("--clear-cache", action="store_true", help="Clear cache before processing")
    
    # Performance options (removed --show-timing, always show performance summary)

    args = parser.parse_args()
    
    # Use Thonburian if requested
    model_size = THONBURIAN_MODEL if args.use_thonburian else args.model_size

    return AppConfig(
        input_path=args.input,
        output_dir=args.output,
        model_size=model_size,
        device=args.device,
        compute_type=args.compute_type,
        max_duration=args.max_duration,
        max_workers=args.max_workers,
        enable_transcription=args.transcribe,
        use_google_for_thai=args.use_google_for_thai,
        log_level=args.log_level,
        log_file=args.log_file,
        enable_cache=args.enable_cache,
        cache_dir=args.cache_dir,
        cache_ttl_hours=args.cache_ttl,
        show_timing=True,  # Always show performance summary
    ), args.clear_cache


# ---------------------------------------------------------------------------
# Batch processing
# ---------------------------------------------------------------------------

def process_files(
    file_paths: list[str],
    cfg: AppConfig,
    metrics: PerformanceMetrics,
    cache: ResultCache | None = None,
    on_result: Callable[[dict, list[dict]], None] | None = None,
) -> list[dict]:
    """Process audio files concurrently and return classification results.
    
    Note: Uses ThreadPoolExecutor instead of ProcessPoolExecutor because:
    - faster-whisper model cannot be pickled (cannot be sent across processes)
    - Model loading is expensive, so we load once and share across threads
    - For CPU-bound tasks, threads still provide parallelism via GIL release during I/O
    """
    # Track model loading time
    with PerformanceTimer("Model loading") as timer:
        model = load_model(cfg.model_size, cfg.device, cfg.compute_type)
    metrics.model_load_time = timer.get_elapsed()
    
    results: list[dict] = []
    
    # Optimization: Sort files by size (small files first)
    # This improves throughput by processing quick files early
    file_paths_with_size = [(fp, Path(fp).stat().st_size) for fp in file_paths]
    file_paths_with_size.sort(key=lambda x: x[1])  # Sort by size ascending
    sorted_file_paths = [fp for fp, _ in file_paths_with_size]
    
    logger.info(
        "Processing %d files (sorted by size for optimal throughput)",
        len(sorted_file_paths),
    )

    def _classify(fp: str) -> dict:
        file_path = Path(fp)
        file_start_time = time.time()
        
        # Check cache first
        if cache:
            cached_result = cache.get(file_path)
            if cached_result:
                metrics.add_file_timing(file_path.name, time.time() - file_start_time)
                return cached_result.get("result", cached_result)
        
        # Process file
        result = detect_language(
            file_path, 
            cfg.max_duration, 
            model, 
            cfg.enable_transcription,
            cfg.use_google_for_thai
        )
        
        # Cache result
        if cache and result.get("detected_lang") != "error":
            cache.set(file_path, result)
        
        # Track timing
        processing_time = time.time() - file_start_time
        metrics.add_file_timing(file_path.name, processing_time)
        
        return result

    # Optimize: Use more workers for better CPU utilization
    # Rule of thumb: 2x CPU cores for I/O-bound tasks
    optimal_workers = min(cfg.max_workers, len(file_paths))
    
    start_time = time.time()
    completed_count = 0
    
    with ThreadPoolExecutor(max_workers=optimal_workers) as executor:
        futures = {executor.submit(_classify, fp): fp for fp in sorted_file_paths}

        desc = "Transcribing" if cfg.enable_transcription else "Classifying"
        # Enhanced progress bar with rate and ETA
        with tqdm(
            total=len(futures),
            desc=desc,
            unit="file",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
        ) as pbar:
            for future in as_completed(futures):
                file_path = futures[future]
                try:
                    result = future.result()
                    results.append(result)

                    # Write result immediately after each file completes
                    if on_result is not None:
                        on_result(result, results)

                    # Update metrics
                    metrics.total_files += 1
                    if result.get("detected_lang") != "error":
                        metrics.successful_files += 1
                    else:
                        metrics.failed_files += 1
                    
                    completed_count += 1
                    
                    # Calculate throughput
                    elapsed = time.time() - start_time
                    throughput = completed_count / elapsed if elapsed > 0 else 0
                    
                    # Update progress bar with current file info
                    pbar.set_postfix_str(
                        f"Current: {Path(file_path).name[:30]}... | {throughput:.2f} files/s"
                    )
                    pbar.update(1)
                except Exception as e:
                    logger.error("Failed to process %s: %s", file_path, e)
                    pbar.update(1)

    # Sort by file name for deterministic output
    results.sort(key=lambda r: r["file_name"])
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    cfg, clear_cache = parse_args()
    setup_logging(cfg.log_level, cfg.log_file)
    
    # Initialize performance metrics
    metrics = PerformanceMetrics()
    overall_start = time.time()

    logger.info("=== Audio Language Classifier & Summarizer ===")
    
    try:
        cfg.validate()
    except Exception as e:
        logger.error("Configuration validation failed: %s", e)
        sys.exit(1)
    
    logger.info("Input:  %s", cfg.input_path)
    logger.info("Output: %s", cfg.output_dir)
    logger.info("Model:  %s (device=%s, compute=%s)", cfg.model_size, cfg.device, cfg.compute_type)
    logger.info("Workers: %d | Max duration: %ds | Transcription: %s | Google Thai: %s", cfg.max_workers, cfg.max_duration, cfg.enable_transcription, cfg.use_google_for_thai)
    
    if cfg.enable_cache:
        logger.info("Cache: enabled (dir=%s, ttl=%dh)", cfg.cache_dir, cfg.cache_ttl_hours)

    try:
        # Initialize cache if enabled
        cache = None
        if cfg.enable_cache:
            cache = ResultCache(Path(cfg.cache_dir), cfg.cache_ttl_hours)
            if clear_cache:
                cleared = cache.clear_all()
                logger.info("Cleared cache: %d entries", cleared)
            else:
                stats = cache.get_stats()
                logger.info("Cache stats: %d entries, %s MB", stats['total_entries'], stats['total_size_mb'])
        
        storage = LocalStorage(cfg.input_path, cfg.audio_extensions)
        file_paths = storage.list_audio_files()

        if not file_paths:
            logger.warning("No audio files found in %s. Exiting.", cfg.input_path)
            sys.exit(0)

        # Prepare incremental CSV path — cleared before processing so each run starts fresh
        incremental_csv = Path(cfg.output_dir) / "summary.csv"
        if incremental_csv.exists():
            incremental_csv.unlink()

        def _on_result(result: dict, current_results: list[dict]) -> None:
            """Write one completed result to disk immediately."""
            append_csv_row(result, incremental_csv, cfg.enable_transcription)
            export_json(current_results, cfg.output_dir)

        results = process_files(file_paths, cfg, metrics, cache, on_result=_on_result)

        # Overwrite with final sorted results for deterministic output
        export_csv(results, cfg.output_dir, cfg.enable_transcription)
        export_json(results, cfg.output_dir)

        # Calculate final metrics
        metrics.total_processing_time = time.time() - overall_start
        
        english_count = sum(1 for r in results if r["is_english"])
        error_count = sum(1 for r in results if r["detected_lang"] == "error")
        logger.info(
            "Done! Total: %d | English: %d | Other: %d | Errors: %d",
            len(results),
            english_count,
            len(results) - english_count - error_count,
            error_count,
        )
        
        # Show performance summary if requested
        if cfg.show_timing:
            metrics.log_summary()
    except Exception as e:
        logger.error("Fatal error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
