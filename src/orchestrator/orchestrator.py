"""
Main orchestrator for managing agents and task execution.
"""

from __future__ import annotations

from typing import Any

from src.agents import (
    EditorAgent,
    ImagePromptAgent,
    QualityReviewerAgent,
    ResearchAgent,
    SEOAgent,
    VisualSuggestionAgent,
    WriterAgent,
)
from src.core.registry import agent_registry
from src.interfaces.agent_interface import IAgent, Task, TaskResult
from src.utils.logger import get_logger


class Orchestrator:
    """
    Central orchestrator for the content creation system.

    Manages agents and coordinates task execution.
    """

    def __init__(self) -> None:
        self.logger = get_logger("orchestrator")
        self._agents: dict[str, IAgent] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the orchestrator and all agents."""
        if self._initialized:
            return

        self.logger.info("Initializing orchestrator")

        # Register and instantiate agents
        agent_classes = [
            ResearchAgent,
            WriterAgent,
            EditorAgent,
            SEOAgent,
            QualityReviewerAgent,
            ImagePromptAgent,
            VisualSuggestionAgent,
        ]

        for agent_cls in agent_classes:
            agent = agent_cls()
            self._agents[agent.name] = agent
            self.logger.info(f"Agent registered: {agent.name}")

        self._initialized = True
        self.logger.info(f"Orchestrator initialized with {len(self._agents)} agents")

    def get_agent(self, name: str) -> IAgent | None:
        """Get an agent by name."""
        return self._agents.get(name)

    def list_agents(self) -> list[str]:
        """List all registered agents."""
        return list(self._agents.keys())

    async def execute_task(self, agent_name: str, task: Task) -> TaskResult:
        """Execute a task with a specific agent."""
        agent = self.get_agent(agent_name)
        if not agent:
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error=f"Agent '{agent_name}' not found",
            )

        return await agent.execute(task)

    async def route_task(self, task: Task) -> TaskResult:
        """Route a task to the appropriate agent based on task type."""
        for agent in self._agents.values():
            if await agent.can_handle(task):
                return await agent.execute(task)

        return TaskResult(
            task_id=task.task_id,
            success=False,
            error=f"No agent found for task type: {task.task_type}",
        )

    def get_status(self) -> dict[str, Any]:
        """Get orchestrator status."""
        return {
            "initialized": self._initialized,
            "agents": {
                name: {
                    "description": agent.description,
                    "category": agent.category,
                    "skills": agent.skill_names,
                }
                for name, agent in self._agents.items()
            },
        }
