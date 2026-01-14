"""
Agent interface definitions.

Defines the contract that all agents must implement.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable
from uuid import uuid4

if TYPE_CHECKING:
    from src.interfaces.skill_interface import ISkill


class TaskStatus(Enum):
    """Status of a task."""

    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


class TaskPriority(Enum):
    """Priority levels for tasks."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Task:
    """Represents a task to be executed by an agent."""

    description: str
    task_type: str = "general"
    task_id: str = field(default_factory=lambda: str(uuid4()))
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    parent_task_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "task_id": self.task_id,
            "description": self.description,
            "task_type": self.task_type,
            "priority": self.priority.name,
            "status": self.status.name,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class TaskResult:
    """Result of a task execution."""

    task_id: str
    success: bool
    output: Any = None
    error: str | None = None
    execution_time: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "task_id": self.task_id,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "metadata": self.metadata,
        }


@dataclass
class AgentCapability:
    """Describes a capability of an agent."""

    name: str
    description: str
    task_types: list[str] = field(default_factory=list)
    required_skills: list[str] = field(default_factory=list)
    priority: int = 0


@runtime_checkable
class IAgent(Protocol):
    """
    Protocol defining the agent interface.

    All agents must implement this interface to be compatible
    with the orchestrator and registry system.
    """

    name: str
    description: str
    category: str
    capabilities: list[AgentCapability]
    skills: list[ISkill]

    async def execute(self, task: Task) -> TaskResult:
        """Execute a task and return the result."""
        ...

    async def can_handle(self, task: Task) -> bool:
        """Check if this agent can handle the given task."""
        ...

    def get_capabilities(self) -> list[AgentCapability]:
        """Return the list of capabilities this agent has."""
        ...

    def add_skill(self, skill: ISkill) -> None:
        """Add a skill to this agent."""
        ...

    def has_skill(self, skill_name: str) -> bool:
        """Check if the agent has a specific skill."""
        ...
