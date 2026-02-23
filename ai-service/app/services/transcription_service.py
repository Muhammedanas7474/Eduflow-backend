"""
Transcription service using Faster Whisper.
Downloads video from S3, extracts audio, and produces timestamped transcript segments.
"""

import logging
import os

from app.core.config import settings
from app.services.s3_service import S3Service

logger = logging.getLogger(__name__)

# Lazy-loaded Whisper model
_model = None


def _get_whisper_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        model_size = settings.whisper_model_size
        logger.info(f"Loading Whisper model: {model_size}")
        _model = WhisperModel(model_size, compute_type="int8")
        logger.info("Whisper model loaded")
    return _model


class TranscriptionService:
    """Transcribe video/audio files and return timestamped segments."""

    def __init__(self):
        self.s3 = S3Service()

    def transcribe_from_s3(self, s3_url: str) -> list[dict]:
        """
        Download file from S3 and transcribe it.

        Args:
            s3_url: Full S3 URL or just the S3 key

        Returns:
            List of {text, start, end} segment dicts
        """
        # Extract S3 key from URL
        s3_key = self._extract_s3_key(s3_url)
        logger.info(f"Downloading from S3: {s3_key}")

        local_path = self.s3.download_file(s3_key)

        try:
            segments = self.transcribe_local(local_path)
            return segments
        finally:
            # Clean up temp file
            if os.path.exists(local_path):
                os.unlink(local_path)

    def transcribe_local(self, file_path: str) -> list[dict]:
        """
        Transcribe a local video/audio file.

        Returns:
            List of {text, start, end} segment dicts
        """
        model = _get_whisper_model()
        logger.info(f"Transcribing: {file_path}")

        segments, info = model.transcribe(
            file_path,
            beam_size=5,
            language=None,  # auto-detect
            vad_filter=True,  # filter silence
        )

        result = []
        for segment in segments:
            result.append(
                {
                    "text": segment.text.strip(),
                    "start": round(segment.start, 2),
                    "end": round(segment.end, 2),
                }
            )

        logger.info(
            f"Transcription complete: {len(result)} segments, "
            f"language={info.language}, duration={info.duration:.1f}s"
        )
        return result

    def _extract_s3_key(self, s3_url: str) -> str:
        """Extract the S3 object key from a full URL or return as-is."""
        if s3_url.startswith("http"):
            # e.g. https://bucket.s3.amazonaws.com/path/to/file.mp4
            # or   https://s3.region.amazonaws.com/bucket/path/to/file.mp4
            from urllib.parse import urlparse

            parsed = urlparse(s3_url)
            path = parsed.path.lstrip("/")

            # If the bucket name is in the hostname
            if settings.aws_storage_bucket_name in parsed.hostname:
                return path
            else:
                # Bucket is the first path component
                parts = path.split("/", 1)
                return parts[1] if len(parts) > 1 else path

        return s3_url
