"""
Anthropic Claude client for content generation.
"""

from __future__ import annotations

from typing import Any

import anthropic

from src.core.config import get_settings
from src.core.exceptions import LLMAPIError
from src.utils.logger import get_logger


class AnthropicClient:
    """Client for Anthropic Claude API."""

    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.anthropic_api_key

        if not self.api_key:
            raise ValueError("Anthropic API key is required")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = settings.llm.anthropic_model
        self.max_tokens = settings.llm.max_tokens
        self.temperature = settings.llm.temperature
        self.logger = get_logger("llm.anthropic")

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using Claude."""
        try:
            self.logger.info("Generating content with Claude")

            messages = [{"role": "user", "content": prompt}]

            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature,
                system=system_prompt or "",
                messages=messages,
                **kwargs,
            )

            content = response.content[0].text

            self.logger.info(
                "Content generated",
                tokens_used=response.usage.output_tokens,
            )

            return content

        except anthropic.APIError as e:
            self.logger.error("Anthropic API error", error=str(e))
            raise LLMAPIError("anthropic", str(e)) from e

    async def generate_with_context(
        self,
        prompt: str,
        context: str,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text with RAG context."""
        full_prompt = f"""Context information:
{context}

Based on the context above, please respond to the following:
{prompt}"""

        return await self.generate(
            prompt=full_prompt,
            system_prompt=system_prompt,
            **kwargs,
        )

    async def generate_structured(
        self,
        prompt: str,
        output_format: str,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate structured output (e.g., JSON, YAML)."""
        format_prompt = f"""{prompt}

Please provide your response in the following format:
{output_format}"""

        return await self.generate(
            prompt=format_prompt,
            system_prompt=system_prompt,
            **kwargs,
        )
