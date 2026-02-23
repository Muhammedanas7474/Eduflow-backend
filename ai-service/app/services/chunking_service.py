"""
Chunking service for transcript segments.
Merges small segments into 500-800 token chunks with 20% overlap,
preserving start/end timestamps.
"""

import logging

logger = logging.getLogger(__name__)

# Rough approximation: 1 token ≈ 4 characters
CHARS_PER_TOKEN = 4
MIN_CHUNK_TOKENS = 400
MAX_CHUNK_TOKENS = 800
OVERLAP_RATIO = 0.2


class ChunkingService:
    """Merge transcript segments into overlapping chunks optimized for embedding."""

    def chunk_segments(self, segments: list[dict]) -> list[dict]:
        """
        Merge transcript segments into chunks.

        Args:
            segments: List of {text, start, end} dicts from transcription

        Returns:
            List of {text, start_time, end_time} chunk dicts
        """
        if not segments:
            return []

        chunks = []
        current_text = ""
        current_start = segments[0]["start"]
        current_end = segments[0]["end"]

        for seg in segments:
            seg_text = seg["text"].strip()
            if not seg_text:
                continue

            # Check if adding this segment would exceed max
            combined = f"{current_text} {seg_text}".strip()
            combined_tokens = len(combined) / CHARS_PER_TOKEN

            if combined_tokens > MAX_CHUNK_TOKENS and current_text:
                # Save current chunk
                chunks.append(
                    {
                        "text": current_text.strip(),
                        "start_time": current_start,
                        "end_time": current_end,
                    }
                )

                # Start new chunk with overlap
                overlap_text = self._get_overlap(current_text)
                current_text = f"{overlap_text} {seg_text}".strip()
                # Estimate overlap start time
                overlap_ratio = len(overlap_text) / max(len(current_text), 1)
                current_start = current_end - (
                    (current_end - current_start) * overlap_ratio
                )
                current_end = seg["end"]
            else:
                current_text = combined
                current_end = seg["end"]

        # Don't forget the last chunk
        if current_text.strip():
            chunks.append(
                {
                    "text": current_text.strip(),
                    "start_time": current_start,
                    "end_time": current_end,
                }
            )

        logger.info(
            f"Chunking complete: {len(segments)} segments → {len(chunks)} chunks"
        )
        return chunks

    def _get_overlap(self, text: str) -> str:
        """Get the last ~20% of text for overlap with next chunk."""
        overlap_chars = int(len(text) * OVERLAP_RATIO)
        if overlap_chars < 50:
            return ""

        overlap = text[-overlap_chars:]
        # Try to start at a word boundary
        space_idx = overlap.find(" ")
        if space_idx != -1:
            overlap = overlap[space_idx + 1 :]
        return overlap
