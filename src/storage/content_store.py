"""
Content storage for generated articles.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.config import get_settings
from src.orchestrator.content_pipeline import ContentResult
from src.utils.logger import get_logger


class ContentStore:
    """Storage for generated content."""

    def __init__(self, output_dir: str | Path | None = None) -> None:
        settings = get_settings()
        self.output_dir = Path(output_dir or settings.content.output_directory)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger("storage.content")

    def save(self, result: ContentResult) -> Path:
        """Save content result to file."""
        filename = f"{result.slug}.md"
        filepath = self.output_dir / filename

        saved_path = result.save(filepath)

        self.logger.info(
            "Content saved",
            path=str(saved_path),
            word_count=result.word_count,
        )

        return saved_path

    def save_json(self, result: ContentResult) -> Path:
        """Save content result as JSON."""
        filename = f"{result.slug}.json"
        filepath = self.output_dir / filename

        data = {
            "topic": result.topic,
            "content": result.content,
            "meta_title": result.meta_title,
            "meta_description": result.meta_description,
            "keywords": result.keywords,
            "image_prompts": result.image_prompts,
            "visual_suggestions": result.visual_suggestions,
            "quality_review": result.quality_review,
            "approved": result.approved,
            "word_count": result.word_count,
            "created_at": result.created_at.isoformat(),
            "pipeline_id": result.pipeline_id,
        }

        filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        self.logger.info("Content saved as JSON", path=str(filepath))

        return filepath

    def list_content(self) -> list[dict[str, Any]]:
        """List all saved content."""
        content_list = []

        for filepath in self.output_dir.glob("*.md"):
            content_list.append({
                "filename": filepath.name,
                "path": str(filepath),
                "modified": datetime.fromtimestamp(filepath.stat().st_mtime).isoformat(),
                "size": filepath.stat().st_size,
            })

        return sorted(content_list, key=lambda x: x["modified"], reverse=True)

    def get_content(self, slug: str) -> str | None:
        """Get content by slug."""
        filepath = self.output_dir / f"{slug}.md"
        if filepath.exists():
            return filepath.read_text(encoding="utf-8")
        return None
