"""
Embedding service using OpenAI text-embedding-3-small.
Generates 1536-dim vectors for text chunks.
"""

import logging

import requests
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate embeddings using Hugging Face Inference API."""

    MODEL = "BAAI/bge-small-en-v1.5"
    API_URL = f"https://router.huggingface.co/hf-inference/models/{MODEL}"
    BATCH_SIZE = 50

    def embed_text(self, text: str) -> list[float]:
        """Embed a single text and return the vector."""
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Embed multiple texts efficiently in batches.
        """
        if not settings.huggingface_api_key:
            raise ValueError("Hugging Face API key is required for embeddings.")

        headers = {"Authorization": f"Bearer {settings.huggingface_api_key}"}
        all_embeddings = []

        for i in range(0, len(texts), self.BATCH_SIZE):
            batch = texts[i : i + self.BATCH_SIZE]
            response = requests.post(
                self.API_URL, headers=headers, json={"inputs": batch}, timeout=30
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"Hugging Face API error: {response.status_code} {response.text}"
                )

            batch_embeddings = response.json()
            # Handle HF sometimes returning nested lists
            if (
                batch_embeddings
                and isinstance(batch_embeddings[0], list)
                and isinstance(batch_embeddings[0][0], list)
            ):
                batch_embeddings = [item[0] for item in batch_embeddings]

            all_embeddings.extend(batch_embeddings)
            logger.info(
                f"Embedded batch {i // self.BATCH_SIZE + 1}: {len(batch)} texts"
            )

        return all_embeddings
