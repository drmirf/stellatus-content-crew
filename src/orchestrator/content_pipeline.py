"""
Content creation pipeline orchestrator.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.core.config import get_settings
from src.core.events import Event, EventType, event_bus
from src.interfaces.agent_interface import Task
from src.orchestrator.orchestrator import Orchestrator
from src.utils.logger import get_logger


@dataclass
class ContentResult:
    """Final result of content creation pipeline."""

    topic: str
    content: str
    meta_title: str = ""
    meta_description: str = ""
    keywords: list[str] = field(default_factory=list)
    image_prompts: str = ""
    visual_suggestions: str = ""
    quality_review: str = ""
    approved: bool = False
    word_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    pipeline_id: str = field(default_factory=lambda: str(uuid4()))

    @property
    def slug(self) -> str:
        """Generate URL slug from topic."""
        import re

        slug = self.topic.lower()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug)
        return slug[:50]

    def save(self, output_path: Path) -> Path:
        """Save content to file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build complete document
        document = f"""---
title: "{self.meta_title or self.topic}"
description: "{self.meta_description}"
keywords: {self.keywords}
created_at: {self.created_at.isoformat()}
word_count: {self.word_count}
approved: {self.approved}
---

{self.content}

---

## Prompts de Imagem

{self.image_prompts}

---

## Sugestões Visuais

{self.visual_suggestions}

---

## Revisão de Qualidade

{self.quality_review}
"""

        output_path.write_text(document, encoding="utf-8")
        return output_path


class ContentPipeline:
    """
    Orchestrates the content creation workflow.

    Pipeline stages:
    1. Research - Gather information on topic
    2. Write - Create initial draft
    3. Edit - Review and improve
    4. SEO - Optimize for search engines
    5. Quality Review - Final quality check
    6. Image Prompts - Generate image prompts
    7. Visual Suggestions - Layout recommendations
    """

    def __init__(self, orchestrator: Orchestrator | None = None) -> None:
        self.orchestrator = orchestrator or Orchestrator()
        self.settings = get_settings()
        self.logger = get_logger("pipeline.content")

    async def create_content(
        self,
        topic: str,
        target_length: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ContentResult:
        """Execute the full content creation pipeline."""
        await self.orchestrator.initialize()

        pipeline_id = str(uuid4())
        target_length = target_length or self.settings.content.default_target_length

        self.logger.info(
            "Starting content pipeline",
            pipeline_id=pipeline_id,
            topic=topic,
            target_length=target_length,
        )

        await event_bus.publish(
            Event(
                type=EventType.PIPELINE_STARTED,
                source="content_pipeline",
                data={"pipeline_id": pipeline_id, "topic": topic},
            )
        )

        pipeline_context = {
            "topic": topic,
            "target_length": target_length,
            **(metadata or {}),
        }

        try:
            # Stage 1: Research
            research_result = await self._execute_stage(
                "research",
                Task(
                    description=topic,
                    task_type="research",
                    metadata=pipeline_context,
                ),
            )

            # Stage 2: Write
            write_result = await self._execute_stage(
                "writer",
                Task(
                    description=f"Write content about: {topic}",
                    task_type="write",
                    metadata={
                        **pipeline_context,
                        "research": research_result.output,
                    },
                ),
            )

            # Stage 3: Edit
            edit_result = await self._execute_stage(
                "editor",
                Task(
                    description=f"Edit content about: {topic}",
                    task_type="edit",
                    metadata={
                        **pipeline_context,
                        "draft": write_result.output,
                    },
                ),
            )

            # Stage 4: SEO
            seo_result = await self._execute_stage(
                "seo",
                Task(
                    description=f"Optimize SEO for: {topic}",
                    task_type="optimize",
                    metadata={
                        **pipeline_context,
                        "edited": edit_result.output,
                    },
                ),
            )

            # Stage 5: Quality Review
            quality_result = await self._execute_stage(
                "quality_reviewer",
                Task(
                    description=f"Review quality for: {topic}",
                    task_type="quality",
                    metadata={
                        **pipeline_context,
                        "seo": seo_result.output,
                        "min_quality_score": self.settings.content.min_quality_score,
                    },
                ),
            )

            # Stage 6: Image Prompts
            image_result = await self._execute_stage(
                "image_prompt",
                Task(
                    description=f"Generate image prompts for: {topic}",
                    task_type="image_prompt",
                    metadata={
                        **pipeline_context,
                        "quality": quality_result.output,
                    },
                ),
            )

            # Stage 7: Visual Suggestions
            visual_result = await self._execute_stage(
                "visual_suggestion",
                Task(
                    description=f"Generate visual suggestions for: {topic}",
                    task_type="visual",
                    metadata={
                        **pipeline_context,
                        "quality": quality_result.output,
                        "image_prompts": image_result.output,
                    },
                ),
            )

            # Compile final result
            seo_output = seo_result.output or {}
            quality_output = quality_result.output or {}
            image_output = image_result.output or {}
            visual_output = visual_result.output or {}

            # Extract content from SEO output (it contains the optimized content)
            final_content = seo_output.get("content", "")

            # Extract keywords
            keywords_data = seo_output.get("keywords", {})
            keywords = [k.get("keyword", "") for k in keywords_data.get("keywords", [])[:10]]

            result = ContentResult(
                topic=topic,
                content=final_content,
                keywords=keywords,
                image_prompts=image_output.get("prompts", ""),
                visual_suggestions=visual_output.get("suggestions", ""),
                quality_review=quality_output.get("review", ""),
                approved=quality_output.get("approved", False),
                word_count=len(final_content.split()),
                pipeline_id=pipeline_id,
            )

            await event_bus.publish(
                Event(
                    type=EventType.PIPELINE_COMPLETED,
                    source="content_pipeline",
                    data={
                        "pipeline_id": pipeline_id,
                        "topic": topic,
                        "approved": result.approved,
                    },
                )
            )

            self.logger.info(
                "Content pipeline completed",
                pipeline_id=pipeline_id,
                approved=result.approved,
                word_count=result.word_count,
            )

            return result

        except Exception as e:
            self.logger.error(
                "Content pipeline failed",
                pipeline_id=pipeline_id,
                error=str(e),
            )

            await event_bus.publish(
                Event(
                    type=EventType.PIPELINE_FAILED,
                    source="content_pipeline",
                    data={"pipeline_id": pipeline_id, "error": str(e)},
                )
            )

            raise

    async def _execute_stage(self, agent_name: str, task: Task) -> Any:
        """Execute a pipeline stage with an agent."""
        self.logger.info(f"Executing stage: {agent_name}")

        await event_bus.publish(
            Event(
                type=EventType.PIPELINE_STAGE_STARTED,
                source="content_pipeline",
                data={"stage": agent_name, "task_id": task.task_id},
            )
        )

        result = await self.orchestrator.execute_task(agent_name, task)

        await event_bus.publish(
            Event(
                type=EventType.PIPELINE_STAGE_COMPLETED,
                source="content_pipeline",
                data={
                    "stage": agent_name,
                    "task_id": task.task_id,
                    "success": result.success,
                },
            )
        )

        if not result.success:
            raise Exception(f"Stage '{agent_name}' failed: {result.error}")

        return result
