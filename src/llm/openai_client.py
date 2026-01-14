"""
OpenAI client for embeddings and optional text generation.
"""

from __future__ import annotations

from typing import Any

import openai

from src.core.config import get_settings
from src.core.exceptions import LLMAPIError
from src.utils.logger import get_logger


class OpenAIClient:
    """Client for OpenAI API."""

    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key

        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = settings.llm.openai_model
        self.embedding_model = settings.rag.embedding_model
        self.max_tokens = settings.llm.max_tokens
        self.temperature = settings.llm.temperature
        self.logger = get_logger("llm.openai")

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        try:
            self.logger.debug("Generating embedding")

            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text,
            )

            return response.data[0].embedding

        except openai.APIError as e:
            self.logger.error("OpenAI embedding error", error=str(e))
            raise LLMAPIError("openai", str(e)) from e

    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        try:
            self.logger.debug("Generating batch embeddings", count=len(texts))

            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=texts,
            )

            return [data.embedding for data in response.data]

        except openai.APIError as e:
            self.logger.error("OpenAI batch embedding error", error=str(e))
            raise LLMAPIError("openai", str(e)) from e

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using GPT."""
        try:
            self.logger.info("Generating content with GPT")

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature,
                messages=messages,
                **kwargs,
            )

            content = response.choices[0].message.content

            self.logger.info(
                "Content generated",
                tokens_used=response.usage.total_tokens,
            )

            return content

        except openai.APIError as e:
            self.logger.error("OpenAI API error", error=str(e))
            raise LLMAPIError("openai", str(e)) from e
