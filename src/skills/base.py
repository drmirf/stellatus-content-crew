"""
Base Skill implementation.

Provides the foundation for all skills.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from src.core.events import Event, EventType, event_bus
from src.interfaces.skill_interface import (
    SkillContext,
    SkillParameter,
    SkillResult,
    SkillStatus,
)
from src.utils.logger import get_logger


class BaseSkill(ABC):
    """
    Abstract base class for all skills.

    Provides common functionality including:
    - Parameter validation
    - Execution lifecycle
    - Event publishing
    """

    name: str = "base_skill"
    description: str = "Base skill implementation"
    category: str = "general"
    parameters: list[SkillParameter] = []

    def __init__(self) -> None:
        self.logger = get_logger(f"skill.{self.name}")

    def get_parameters(self) -> list[SkillParameter]:
        """Return the list of parameters this skill accepts."""
        return self.parameters

    def validate(self, context: SkillContext) -> tuple[bool, list[str]]:
        """Validate the input parameters."""
        errors = []

        for param in self.parameters:
            value = context.get(param.name)

            if param.required and value is None:
                errors.append(f"Missing required parameter: {param.name}")
                continue

            if value is not None and not isinstance(value, param.param_type):
                errors.append(
                    f"Parameter '{param.name}' must be of type {param.param_type.__name__}"
                )

        return len(errors) == 0, errors

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute the skill with the given context."""
        start_time = time.time()

        self.logger.info(
            "Skill started",
            skill=self.name,
            execution_id=context.execution_id,
        )

        await event_bus.publish(
            Event(
                type=EventType.SKILL_STARTED,
                source=self.name,
                data={"execution_id": context.execution_id},
            )
        )

        try:
            await self._pre_execute(context)
            result = await self._execute(context)
            await self._post_execute(context, result)

            result.execution_time = time.time() - start_time

            self.logger.info(
                "Skill completed",
                skill=self.name,
                success=result.success,
                execution_time=result.execution_time,
            )

            await event_bus.publish(
                Event(
                    type=EventType.SKILL_COMPLETED,
                    source=self.name,
                    data={"result": result.to_dict()},
                )
            )

            return result

        except Exception as e:
            self.logger.error(
                "Skill failed",
                skill=self.name,
                error=str(e),
            )

            result = SkillResult(
                skill_name=self.name,
                success=False,
                status=SkillStatus.FAILED,
                error=str(e),
                execution_time=time.time() - start_time,
            )

            await event_bus.publish(
                Event(
                    type=EventType.SKILL_FAILED,
                    source=self.name,
                    data={"error": str(e)},
                )
            )

            return result

    @abstractmethod
    async def _execute(self, context: SkillContext) -> SkillResult:
        """Execute the actual skill logic. Must be implemented by subclasses."""
        pass

    async def _pre_execute(self, context: SkillContext) -> None:
        """Hook called before execution."""
        pass

    async def _post_execute(self, context: SkillContext, result: SkillResult) -> None:
        """Hook called after execution."""
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"

    def to_dict(self) -> dict[str, Any]:
        """Convert skill to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.param_type.__name__,
                    "description": p.description,
                    "required": p.required,
                }
                for p in self.parameters
            ],
        }
