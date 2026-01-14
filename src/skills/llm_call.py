"""
LLM Call skill for interacting with language models.
"""

from __future__ import annotations

from src.core.registry import skill_registry
from src.interfaces.skill_interface import SkillContext, SkillParameter, SkillResult, SkillStatus
from src.llm.anthropic_client import AnthropicClient
from src.skills.base import BaseSkill


@skill_registry.register(name="llm_call", category="llm")
class LLMCallSkill(BaseSkill):
    """Skill for making LLM API calls."""

    name = "llm_call"
    description = "Make calls to language models for text generation"
    category = "llm"
    parameters = [
        SkillParameter(
            name="prompt",
            param_type=str,
            description="The prompt to send to the LLM",
            required=True,
        ),
        SkillParameter(
            name="system_prompt",
            param_type=str,
            description="Optional system prompt",
            required=False,
        ),
        SkillParameter(
            name="context",
            param_type=str,
            description="Optional context to include",
            required=False,
        ),
        SkillParameter(
            name="max_tokens",
            param_type=int,
            description="Maximum tokens in response",
            required=False,
            default=4096,
        ),
        SkillParameter(
            name="temperature",
            param_type=float,
            description="Temperature for generation",
            required=False,
            default=0.7,
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._client: AnthropicClient | None = None

    def _get_client(self) -> AnthropicClient:
        """Get or create the LLM client."""
        if self._client is None:
            self._client = AnthropicClient()
        return self._client

    async def _execute(self, context: SkillContext) -> SkillResult:
        """Execute the LLM call."""
        prompt = context.get("prompt")
        system_prompt = context.get("system_prompt")
        rag_context = context.get("context")
        max_tokens = context.get("max_tokens", 4096)
        temperature = context.get("temperature", 0.7)

        try:
            client = self._get_client()

            if rag_context:
                response = await client.generate_with_context(
                    prompt=prompt,
                    context=rag_context,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            else:
                response = await client.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

            return SkillResult(
                skill_name=self.name,
                success=True,
                status=SkillStatus.COMPLETED,
                output=response,
                metadata={"tokens_estimated": len(response.split())},
            )

        except Exception as e:
            self.logger.error("LLM call failed", error=str(e))
            return SkillResult(
                skill_name=self.name,
                success=False,
                status=SkillStatus.FAILED,
                error=str(e),
            )
