"""
OpenAI embedding implementation.
"""

from __future__ import annotations

import openai

from src.core.config import get_settings
from src.core.exceptions import EmbeddingError
from src.rag.embeddings.base import BaseEmbedding
from src.utils.logger import get_logger


class OpenAIEmbeddings(BaseEmbedding):
    """OpenAI embedding provider."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key

        if not self.api_key:
            raise ValueError("OpenAI API key is required for embeddings")

        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = model or settings.rag.embedding_model
        self.logger = get_logger("rag.embeddings.openai")

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
            )
            return response.data[0].embedding
        except openai.APIError as e:
            self.logger.error("Embedding generation failed", error=str(e))
            raise EmbeddingError(str(e)) from e

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        try:
            self.logger.debug("Generating batch embeddings", count=len(texts))

            # OpenAI has a limit on batch size
            batch_size = 100
            all_embeddings = []

            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                )
                all_embeddings.extend([data.embedding for data in response.data])

            return all_embeddings
        except openai.APIError as e:
            self.logger.error("Batch embedding generation failed", error=str(e))
            raise EmbeddingError(str(e)) from e
