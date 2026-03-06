"""Google Cloud STT integration for Thai language using Chirp 2 model (v2 API)."""

from __future__ import annotations

import logging
import os
import time
import uuid
from pathlib import Path

from google.api_core import exceptions as google_exceptions

from google.api_core.client_options import ClientOptions
from google.cloud import speech_v2 as speech
from google.cloud import storage
from google.cloud.speech_v2 import types as cloud_speech

from constants import (
    GOOGLE_STT_BATCH_API_TIMEOUT,
    GOOGLE_STT_BATCH_POLL_INTERVAL,
    GOOGLE_STT_MAX_RETRIES,
    GOOGLE_STT_RETRY_BACKOFF,
    GOOGLE_STT_RETRY_DELAY,
    MAX_AUDIO_DURATION_SECONDS,
    MAX_FILE_SIZE_MB,
    THAI_STT_LANGUAGE_CODE,
)
from exceptions import ConfigurationError, GoogleSTTError
from utils import check_file_size, get_audio_duration, get_google_project_id

logger = logging.getLogger(__name__)

_stt_client: speech.SpeechClient | None = None
_storage_client: storage.Client | None = None


def get_stt_client() -> speech.SpeechClient:
    """Get or create STT v2 client (singleton) with regional endpoint.
    
    Returns:
        Initialized SpeechClient instance
        
    Raises:
        ConfigurationError: If credentials are not configured
    """
    global _stt_client
    if _stt_client is None:
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_path:
            raise ConfigurationError(
                "GOOGLE_APPLICATION_CREDENTIALS environment variable not set. "
                "Please set it to your service account JSON key file path."
            )
        
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        
        client_options = None
        if location != "global":
            api_endpoint = f"{location}-speech.googleapis.com"
            client_options = ClientOptions(api_endpoint=api_endpoint)
            logger.info("Using regional endpoint: %s", api_endpoint)
        
        _stt_client = speech.SpeechClient.from_service_account_json(
            credentials_path,
            client_options=client_options
        )
        logger.info("Google STT v2 client initialized (location: %s)", location)
    return _stt_client


def get_storage_client() -> storage.Client:
    """Get or create GCS storage client (singleton).
    
    Returns:
        Initialized storage.Client instance
        
    Raises:
        ConfigurationError: If credentials are not configured
    """
    global _storage_client
    if _storage_client is None:
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        
        if credentials_path:
            _storage_client = storage.Client.from_service_account_json(
                credentials_path,
                project=project_id
            )
        else:
            _storage_client = storage.Client(project=project_id)
        
        logger.info("Google Cloud Storage client initialized")
    return _storage_client


def _should_use_batch_api(file_path: Path, duration: float | None = None) -> tuple[bool, float, float]:
    """Determine if batch API should be used based on file constraints.
    
    Args:
        file_path: Path to the audio file
        duration: Optional pre-computed duration in seconds (avoids ffprobe call)
        
    Returns:
        Tuple of (use_batch, size_mb, duration_seconds)
    """
    is_valid_size, size_mb = check_file_size(file_path, MAX_FILE_SIZE_MB)
    
    # Use provided duration or fall back to ffprobe
    if duration is None:
        duration = get_audio_duration(file_path)
    
    use_batch = (not is_valid_size) or (duration > MAX_AUDIO_DURATION_SECONDS)
    return use_batch, size_mb, duration


def _build_recognition_config() -> cloud_speech.RecognitionConfig:
    """Build common recognition configuration for Chirp 2.
    
    Returns:
        RecognitionConfig instance
    """
    return cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=[THAI_STT_LANGUAGE_CODE],
        features=cloud_speech.RecognitionFeatures(
            enable_automatic_punctuation=True,
        ),
    )


def _get_recognizer_path() -> str:
    """Build recognizer resource path.
    
    Returns:
        Recognizer path string
        
    Raises:
        ConfigurationError: If required configuration is missing
    """
    project_id = get_google_project_id()
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    recognizer_id = os.getenv("STT_RECOGNIZER", "_")
    return f"projects/{project_id}/locations/{location}/recognizers/{recognizer_id}"


def transcribe_with_chirp(file_path: Path, duration: float | None = None) -> str | None:
    """Transcribe audio using Google Chirp 2 model (v2 API) with recognizer resource.
    
    Uses synchronous API for short files (≤60s, ≤10MB) or batch API via GCS for longer files.
    
    Args:
        file_path: Path to audio file
        duration: Optional pre-computed duration in seconds (avoids ffprobe overhead)
        
    Returns:
        Transcription text or None if error
        
    Raises:
        GoogleSTTError: If transcription fails
    """
    use_batch, size_mb, duration = _should_use_batch_api(file_path, duration)
    
    if use_batch:
        logger.info(
            "File %s (%.1fMB, %.1fs) requires batch API via GCS",
            file_path.name, size_mb, duration,
        )
        return _transcribe_with_batch_api(file_path)
    else:
        logger.info(
            "File %s (%.1fMB, %.1fs) using synchronous API",
            file_path.name, size_mb, duration,
        )
        return _transcribe_with_sync_api(file_path)



def _transcribe_with_sync_api(file_path: Path) -> str | None:
    """Transcribe using synchronous API (for files ≤60s, ≤10MB) with retry logic.
    
    Args:
        file_path: Path to audio file
        
    Returns:
        Transcription text or None if error
    """
    client = get_stt_client()
    recognizer_path = _get_recognizer_path()
    
    with open(file_path, "rb") as audio_file:
        content = audio_file.read()
    
    config = _build_recognition_config()
    
    request = cloud_speech.RecognizeRequest(
        recognizer=recognizer_path,
        config=config,
        content=content,
    )
    
    # Retry logic with exponential backoff
    for attempt in range(GOOGLE_STT_MAX_RETRIES):
        try:
            logger.info(
                "Sending to Google STT v2 (sync): %s (attempt %d/%d)",
                file_path.name, attempt + 1, GOOGLE_STT_MAX_RETRIES,
            )
            
            response = client.recognize(request=request)
            
            transcript = ""
            for result in response.results:
                if result.alternatives:
                    transcript += result.alternatives[0].transcript
            
            if transcript:
                logger.info("Transcription received: %s...", transcript[:50])
                return transcript
            else:
                logger.warning("Empty transcription received")
                return None
                
        except (google_exceptions.ServiceUnavailable, 
                google_exceptions.DeadlineExceeded,
                google_exceptions.ResourceExhausted) as e:
            # Retryable errors
            if attempt < GOOGLE_STT_MAX_RETRIES - 1:
                delay = GOOGLE_STT_RETRY_DELAY * (GOOGLE_STT_RETRY_BACKOFF ** attempt)
                logger.warning(
                    "Google STT API error (retryable): %s. Retrying in %.1fs...",
                    e, delay,
                )
                time.sleep(delay)
            else:
                logger.error(
                    "Google STT API failed after %d attempts: %s",
                    GOOGLE_STT_MAX_RETRIES, e,
                )
                return None
                
        except Exception as e:
            # Non-retryable errors
            logger.error("Error calling Google STT v2 sync API: %s", e)
            return None
    
    return None


def _transcribe_with_batch_api(file_path: Path) -> str | None:
    """Transcribe using batch API via GCS (for files >60s or >10MB).
    
    Args:
        file_path: Path to audio file
        
    Returns:
        Transcription text or None if error
    """
    gcs_uri = None
    bucket_name = None
    
    try:
        bucket_name = os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")
        if not bucket_name:
            logger.error("GOOGLE_CLOUD_STORAGE_BUCKET not set, cannot use batch API")
            return None
        
        recognizer_path = _get_recognizer_path()
        
        storage_client = get_storage_client()
        bucket = storage_client.bucket(bucket_name)
        
        blob_name = f"audio_classifier/{uuid.uuid4()}/{file_path.name}"
        blob = bucket.blob(blob_name)
        
        logger.info("Uploading %s to GCS: gs://%s/%s", file_path.name, bucket_name, blob_name)
        blob.upload_from_filename(str(file_path))
        gcs_uri = f"gs://{bucket_name}/{blob_name}"
        
        config = _build_recognition_config()
        
        files = [cloud_speech.BatchRecognizeFileMetadata(uri=gcs_uri)]
        recognition_output_config = cloud_speech.RecognitionOutputConfig(
            inline_response_config=cloud_speech.InlineOutputConfig()
        )
        
        request = cloud_speech.BatchRecognizeRequest(
            recognizer=recognizer_path,
            config=config,
            files=files,
            recognition_output_config=recognition_output_config,
        )
        
        logger.info("Sending to Google STT v2 (batch): %s", file_path.name)
        
        stt_client = get_stt_client()
        operation = stt_client.batch_recognize(request=request)
        
        logger.info("Waiting for batch transcription to complete...")
        start_time = time.time()
        
        while not operation.done():
            if time.time() - start_time > GOOGLE_STT_BATCH_API_TIMEOUT:
                logger.error("Batch transcription timed out")
                return None
            time.sleep(GOOGLE_STT_BATCH_POLL_INTERVAL)
        
        result = operation.result()
        
        transcript = ""
        if result and hasattr(result, 'results') and result.results:
            for uri, file_result in result.results.items():
                if hasattr(file_result, 'transcript') and file_result.transcript:
                    for result_item in file_result.transcript.results:
                        if result_item.alternatives:
                            transcript += result_item.alternatives[0].transcript
        
        if transcript:
            logger.info("Batch transcription received: %s...", transcript[:50])
        else:
            logger.warning("Empty batch transcription received")
        
        return transcript if transcript else None
        
    except Exception as e:
        logger.error("Error calling Google STT v2 batch API: %s", e)
        return None
    finally:
        if gcs_uri and bucket_name:
            try:
                storage_client = get_storage_client()
                bucket = storage_client.bucket(bucket_name)
                blob_name = gcs_uri.replace(f"gs://{bucket_name}/", "")
                blob = bucket.blob(blob_name)
                blob.delete()
                logger.info("Cleaned up GCS file: %s", gcs_uri)
            except Exception as e:
                logger.warning("Failed to cleanup GCS file: %s", e)
