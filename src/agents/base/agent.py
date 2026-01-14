"""
Base Agent implementation.

Provides the foundation for all content creation agents.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from src.core.events import Event, EventType, event_bus
from src.core.exceptions import AgentExecutionError, SkillNotFoundError
from src.interfaces.agent_interface import (
    AgentCapability,
    Task,
    TaskResult,
    TaskStatus,
)
from src.interfaces.skill_interface import ISkill, SkillContext, SkillResult
from src.utils.logger import get_logger


class BaseAgent(ABC):
    """
    Abstract base class for all content creation agents.

    Provides common functionality including:
    - Skill management
    - Task execution lifecycle
    - Event publishing
    - Error handling
    """

    name: str = "base_agent"
    description: str = "Base agent implementation"
    category: str = "general"

    def __init__(self) -> None:
        self._skills: dict[str, ISkill] = {}
        self._capabilities: list[AgentCapability] = []
        self._is_initialized: bool = False
        self.logger = get_logger(f"agent.{self.name}")
        self._setup()

    def _setup(self) -> None:
        """Initialize the agent. Override for custom setup."""
        self._is_initialized = True

    def _teardown(self) -> None:
        """Cleanup the agent. Override for custom teardown."""
        self._skills.clear()
        self._is_initialized = False

    # ==================== Skill Management ====================

    def add_skill(self, skill: ISkill) -> None:
        """Add a skill to this agent."""
        self._skills[skill.name] = skill

    def remove_skill(self, skill_name: str) -> None:
        """Remove a skill from this agent."""
        self._skills.pop(skill_name, None)

    def has_skill(self, skill_name: str) -> bool:
        """Check if the agent has a specific skill."""
        return skill_name in self._skills

    def get_skill(self, skill_name: str) -> ISkill:
        """Get a skill by name."""
        if skill_name not in self._skills:
            raise SkillNotFoundError(skill_name)
        return self._skills[skill_name]

    @property
    def skills(self) -> list[ISkill]:
        """Return list of all skills."""
        return list(self._skills.values())

    @property
    def skill_names(self) -> list[str]:
        """Return list of skill names."""
        return list(self._skills.keys())

    # ==================== Capability Management ====================

    def get_capabilities(self) -> list[AgentCapability]:
        """Return the list of capabilities this agent has."""
        return self._capabilities

    def add_capability(self, capability: AgentCapability) -> None:
        """Add a capability to this agent."""
        self._capabilities.append(capability)

    @property
    def capabilities(self) -> list[AgentCapability]:
        """Return list of all capabilities."""
        return self._capabilities

    # ==================== Task Handling ====================

    async def can_handle(self, task: Task) -> bool:
        """Check if this agent can handle the given task."""
        for capability in self._capabilities:
            if task.task_type in capability.task_types:
                return True
        return False

    async def execute(self, task: Task) -> TaskResult:
        """
        Execute a task and return the result.

        Handles the full lifecycle including events and error handling.
        """
        start_time = time.time()
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()

        self.logger.info(
            "Agent started task",
            agent=self.name,
            task_id=task.task_id,
            task_type=task.task_type,
        )

        await event_bus.publish(
            Event(
                type=EventType.AGENT_STARTED,
                source=self.name,
                data={"task": task.to_dict()},
            )
        )

        try:
            await self._pre_execute(task)
            result = await self._execute_task(task)
            await self._post_execute(task, result)

            task.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
            task.completed_at = datetime.now()
            result.execution_time = time.time() - start_time

            self.logger.info(
                "Agent completed task",
                agent=self.name,
                task_id=task.task_id,
                success=result.success,
                execution_time=result.execution_time,
            )

            await event_bus.publish(
                Event(
                    type=EventType.AGENT_COMPLETED,
                    source=self.name,
                    data={"task": task.to_dict(), "result": result.to_dict()},
                )
            )

            return result

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()

            self.logger.error(
                "Agent failed task",
                agent=self.name,
                task_id=task.task_id,
                error=str(e),
            )

            result = TaskResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time,
            )

            await event_bus.publish(
                Event(
                    type=EventType.AGENT_FAILED,
                    source=self.name,
                    data={"task": task.to_dict(), "error": str(e)},
                )
            )

            raise AgentExecutionError(self.name, task.task_id, str(e)) from e

    @abstractmethod
    async def _execute_task(self, task: Task) -> TaskResult:
        """Execute the actual task logic. Must be implemented by subclasses."""
        pass

    async def _pre_execute(self, task: Task) -> None:
        """Hook called before task execution."""
        pass

    async def _post_execute(self, task: Task, result: TaskResult) -> None:
        """Hook called after task execution."""
        pass

    # ==================== Skill Execution Helpers ====================

    async def execute_skill(
        self,
        skill_name: str,
        params: dict[str, Any] | None = None,
        context: SkillContext | None = None,
    ) -> SkillResult:
        """Execute a skill by name."""
        skill = self.get_skill(skill_name)

        if context is None:
            context = SkillContext(
                params=params or {},
                agent_name=self.name,
            )
        elif params:
            context.params.update(params)

        is_valid, errors = skill.validate(context)
        if not is_valid:
            return SkillResult(
                skill_name=skill_name,
                success=False,
                error=f"Validation failed: {', '.join(errors)}",
            )

        return await skill.execute(context)

    # ==================== Utility Methods ====================

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', skills={len(self._skills)})>"

    def to_dict(self) -> dict[str, Any]:
        """Convert agent to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "skills": self.skill_names,
            "capabilities": [
                {
                    "name": cap.name,
                    "description": cap.description,
                    "task_types": cap.task_types,
                }
                for cap in self._capabilities
            ],
        }
