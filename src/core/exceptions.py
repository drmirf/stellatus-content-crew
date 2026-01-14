"""
Exception classes for the Content Crew system.

Provides structured error handling with context information.
"""

from typing import Any


class BaseError(Exception):
    """Base exception with structured error handling."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        recoverable: bool = True,
    ) -> None:
        self.message = message
        self.details = details or {}
        self.recoverable = recoverable
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary."""
        return {
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable,
            "type": self.__class__.__name__,
        }


# Agent Exceptions
class AgentError(BaseError):
    """Base exception for agent-related errors."""

    pass


class AgentNotFoundError(AgentError):
    """Raised when an agent is not found in the registry."""

    def __init__(self, agent_name: str) -> None:
        super().__init__(
            f"Agent '{agent_name}' not found in registry",
            {"agent_name": agent_name},
        )


class AgentExecutionError(AgentError):
    """Raised when an agent fails to execute a task."""

    def __init__(self, agent_name: str, task_id: str, reason: str) -> None:
        super().__init__(
            f"Agent '{agent_name}' failed to execute task '{task_id}': {reason}",
            {"agent_name": agent_name, "task_id": task_id, "reason": reason},
        )


# Skill Exceptions
class SkillError(BaseError):
    """Base exception for skill-related errors."""

    pass


class SkillNotFoundError(SkillError):
    """Raised when a skill is not found in the registry."""

    def __init__(self, skill_name: str) -> None:
        super().__init__(
            f"Skill '{skill_name}' not found in registry",
            {"skill_name": skill_name},
        )


class SkillExecutionError(SkillError):
    """Raised when a skill fails to execute."""

    def __init__(self, skill_name: str, reason: str) -> None:
        super().__init__(
            f"Skill '{skill_name}' execution failed: {reason}",
            {"skill_name": skill_name, "reason": reason},
        )


# Registry Exceptions
class RegistryError(BaseError):
    """Base exception for registry-related errors."""

    pass


class DuplicateRegistrationError(RegistryError):
    """Raised when attempting to register a duplicate item."""

    def __init__(self, item_type: str, item_name: str) -> None:
        super().__init__(
            f"{item_type} '{item_name}' is already registered",
            {"item_type": item_type, "item_name": item_name},
        )


# RAG Exceptions
class RAGError(BaseError):
    """Base exception for RAG-related errors."""

    pass


class EmbeddingError(RAGError):
    """Raised when embedding generation fails."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Embedding generation failed: {reason}")


class VectorStoreError(RAGError):
    """Raised when vector store operations fail."""

    def __init__(self, operation: str, reason: str) -> None:
        super().__init__(
            f"Vector store {operation} failed: {reason}",
            {"operation": operation, "reason": reason},
        )


class DocumentProcessingError(RAGError):
    """Raised when document processing fails."""

    def __init__(self, document: str, reason: str) -> None:
        super().__init__(
            f"Failed to process document '{document}': {reason}",
            {"document": document, "reason": reason},
        )


# Pipeline Exceptions
class PipelineError(BaseError):
    """Base exception for pipeline-related errors."""

    pass


class StageExecutionError(PipelineError):
    """Raised when a pipeline stage fails."""

    def __init__(self, stage: str, reason: str) -> None:
        super().__init__(
            f"Pipeline stage '{stage}' failed: {reason}",
            {"stage": stage, "reason": reason},
        )


# LLM Exceptions
class LLMError(BaseError):
    """Base exception for LLM-related errors."""

    pass


class LLMAPIError(LLMError):
    """Raised when LLM API call fails."""

    def __init__(self, provider: str, reason: str) -> None:
        super().__init__(
            f"LLM API call to '{provider}' failed: {reason}",
            {"provider": provider, "reason": reason},
        )
