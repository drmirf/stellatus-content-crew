"""
Skill interface definitions.

Defines the contract that all skills must implement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Protocol, runtime_checkable
from uuid import uuid4


class SkillStatus(Enum):
    """Execution status of a skill."""

    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    SKIPPED = auto()


@dataclass
class SkillContext:
    """Context object passed to skills during execution."""

    params: dict[str, Any] = field(default_factory=dict)
    execution_id: str = field(default_factory=lambda: str(uuid4()))
    parent_task_id: str | None = None
    agent_name: str | None = None
    shared_state: dict[str, Any] = field(default_factory=dict)
    working_dir: str | None = None
    output_dir: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a parameter value."""
        return self.params.get(key, default)

    def set_shared(self, key: str, value: Any) -> None:
        """Set a shared state value."""
        self.shared_state[key] = value

    def get_shared(self, key: str, default: Any = None) -> Any:
        """Get a shared state value."""
        return self.shared_state.get(key, default)


@dataclass
class SkillResult:
    """Result of a skill execution."""

    skill_name: str
    success: bool
    status: SkillStatus = SkillStatus.COMPLETED
    output: Any = None
    error: str | None = None
    execution_time: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "skill_name": self.skill_name,
            "success": self.success,
            "status": self.status.name,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "metadata": self.metadata,
        }


@dataclass
class SkillParameter:
    """Definition of a skill parameter."""

    name: str
    param_type: type
    description: str = ""
    required: bool = True
    default: Any = None


@runtime_checkable
class ISkill(Protocol):
    """
    Protocol defining the skill interface.

    All skills must implement this interface to be compatible
    with agents and the registry system.
    """

    name: str
    description: str
    category: str
    parameters: list[SkillParameter]

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute the skill with the given context."""
        ...

    def validate(self, context: SkillContext) -> tuple[bool, list[str]]:
        """Validate the input parameters."""
        ...

    def get_parameters(self) -> list[SkillParameter]:
        """Return the list of parameters this skill accepts."""
        ...
