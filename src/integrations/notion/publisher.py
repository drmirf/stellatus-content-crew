"""
Notion publisher for submitting articles to a Notion database.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.integrations.notion.client import NotionClient
from src.orchestrator.content_pipeline import ContentResult
from src.utils.logger import get_logger


@dataclass
class PublishResult:
    """Result of publishing to Notion."""

    success: bool
    page_id: str | None = None
    page_url: str | None = None
    error: str | None = None


class NotionPublisher:
    """Publisher for sending articles to Notion."""

    def __init__(
        self,
        token: str | None = None,
        database_id: str | None = None,
    ) -> None:
        self.client = NotionClient(token)
        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID")

        if not self.database_id:
            raise ValueError(
                "Notion database ID is required. Set NOTION_DATABASE_ID environment variable "
                "or pass database_id parameter."
            )

        self.logger = get_logger("notion.publisher")

    def test_connection(self) -> bool:
        """Test connection to Notion and database access."""
        if not self.client.test_connection():
            return False

        db = self.client.get_database(self.database_id)
        if not db:
            self.logger.error("Cannot access database", database_id=self.database_id)
            return False

        return True

    def publish(
        self,
        content: ContentResult,
        status: str = "Rascunho",
    ) -> PublishResult:
        """
        Publish a ContentResult to Notion as a draft.

        Args:
            content: The content result from the pipeline
            status: The status to set (default: "Rascunho")

        Returns:
            PublishResult with success status and page info
        """
        try:
            self.logger.info("Publishing to Notion", topic=content.topic)

            # Build properties for the database
            properties = self._build_properties(content, status)

            # Convert content to Notion blocks
            blocks = self._build_content_blocks(content)

            # Create the page
            result = self.client.create_page(
                database_id=self.database_id,
                properties=properties,
                children=blocks,
            )

            page_id = result["id"]
            page_url = result.get("url", f"https://notion.so/{page_id.replace('-', '')}")

            self.logger.info(
                "Successfully published to Notion",
                page_id=page_id,
                page_url=page_url,
            )

            return PublishResult(
                success=True,
                page_id=page_id,
                page_url=page_url,
            )

        except Exception as e:
            self.logger.error("Failed to publish to Notion", error=str(e))
            return PublishResult(
                success=False,
                error=str(e),
            )

    def _build_properties(
        self,
        content: ContentResult,
        status: str,
    ) -> dict[str, Any]:
        """Build Notion page properties from ContentResult."""
        # Title (required)
        title = content.meta_title or content.topic

        properties = {
            # Title property (required for databases)
            "Name": {
                "title": [{"text": {"content": title}}],
            },
            # Status
            "Status": {
                "select": {"name": status},
            },
            # Created date
            "Created": {
                "date": {"start": content.created_at.isoformat()},
            },
            # Word count
            "Word Count": {
                "number": content.word_count,
            },
            # Approved checkbox
            "Approved": {
                "checkbox": content.approved,
            },
        }

        # Keywords as multi-select (if available)
        if content.keywords:
            properties["Keywords"] = {
                "multi_select": [{"name": kw[:100]} for kw in content.keywords[:10]],
            }

        return properties

    def _build_content_blocks(self, content: ContentResult) -> list[dict[str, Any]]:
        """Build Notion blocks from ContentResult."""
        blocks = []

        # Main content
        if content.content:
            # Extract just the article content (before the --- separator sections)
            main_content = content.content.split("---")[0] if "---" in content.content else content.content
            content_blocks = self.client.markdown_to_blocks(main_content)
            blocks.extend(content_blocks)

        # Add divider before image prompts
        if content.image_prompts:
            blocks.append({"type": "divider", "divider": {}})
            blocks.append({
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Prompts de Imagem"}}],
                },
            })
            # Add as a toggle block to keep it collapsed
            blocks.append({
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"type": "text", "text": {"content": "Ver prompts de imagem"}}],
                    "children": self.client.markdown_to_blocks(content.image_prompts),
                },
            })

        # Add visual suggestions in a toggle
        if content.visual_suggestions:
            blocks.append({
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"type": "text", "text": {"content": "Ver sugestões visuais"}}],
                    "children": self.client.markdown_to_blocks(content.visual_suggestions),
                },
            })

        # Add quality review in a toggle
        if content.quality_review:
            blocks.append({
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"type": "text", "text": {"content": "Ver revisão de qualidade"}}],
                    "children": self.client.markdown_to_blocks(content.quality_review),
                },
            })

        return blocks
