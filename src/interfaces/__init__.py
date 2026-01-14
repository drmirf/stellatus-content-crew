"""Interface definitions for agents and skills."""

from src.interfaces.agent_interface import (
    AgentCapability,
    IAgent,
    Task,
    TaskPriority,
    TaskResult,
    TaskStatus,
)
from src.interfaces.skill_interface import (
    ISkill,
    SkillContext,
    SkillParameter,
    SkillResult,
    SkillStatus,
)

__all__ = [
    "IAgent",
    "Task",
    "TaskResult",
    "TaskStatus",
    "TaskPriority",
    "AgentCapability",
    "ISkill",
    "SkillContext",
    "SkillResult",
    "SkillStatus",
    "SkillParameter",
]
