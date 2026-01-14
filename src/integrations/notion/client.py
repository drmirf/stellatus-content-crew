"""
Notion API client for creating and managing pages.
"""

from __future__ import annotations

import os
import re
from typing import Any

from notion_client import Client
from notion_client.errors import APIResponseError

from src.utils.logger import get_logger


class NotionClient:
    """Client for interacting with Notion API."""

    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.getenv("NOTION_TOKEN")

        if not self.token:
            raise ValueError(
                "Notion token is required. Set NOTION_TOKEN environment variable "
                "or pass token parameter."
            )

        self.client = Client(auth=self.token)
        self.logger = get_logger("notion.client")

    def test_connection(self) -> bool:
        """Test if the connection to Notion is working."""
        try:
            self.client.users.me()
            return True
        except APIResponseError as e:
            self.logger.error("Notion connection failed", error=str(e))
            return False

    def get_database(self, database_id: str) -> dict[str, Any] | None:
        """Get database information."""
        try:
            return self.client.databases.retrieve(database_id=database_id)
        except APIResponseError as e:
            self.logger.error("Failed to get database", error=str(e))
            return None

    def create_page(
        self,
        database_id: str,
        properties: dict[str, Any],
        children: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Create a new page in a database."""
        try:
            page_data = {
                "parent": {"database_id": database_id},
                "properties": properties,
            }

            if children:
                page_data["children"] = children

            result = self.client.pages.create(**page_data)

            self.logger.info(
                "Page created in Notion",
                page_id=result["id"],
            )

            return result

        except APIResponseError as e:
            self.logger.error("Failed to create page", error=str(e))
            raise

    def markdown_to_blocks(self, markdown: str) -> list[dict[str, Any]]:
        """Convert Markdown content to Notion blocks."""
        blocks = []
        lines = markdown.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]

            # Skip empty lines
            if not line.strip():
                i += 1
                continue

            # Headers
            if line.startswith("### "):
                blocks.append(self._heading_block(line[4:], level=3))
            elif line.startswith("## "):
                blocks.append(self._heading_block(line[3:], level=2))
            elif line.startswith("# "):
                blocks.append(self._heading_block(line[2:], level=1))

            # Bullet lists
            elif line.strip().startswith("- ") or line.strip().startswith("* "):
                text = line.strip()[2:]
                blocks.append(self._bulleted_list_block(text))

            # Numbered lists
            elif re.match(r"^\d+\.\s", line.strip()):
                text = re.sub(r"^\d+\.\s", "", line.strip())
                blocks.append(self._numbered_list_block(text))

            # Code blocks
            elif line.strip().startswith("```"):
                code_lines = []
                language = line.strip()[3:] or "plain text"
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    code_lines.append(lines[i])
                    i += 1
                blocks.append(self._code_block("\n".join(code_lines), language))

            # Blockquotes
            elif line.strip().startswith(">"):
                text = line.strip()[1:].strip()
                blocks.append(self._quote_block(text))

            # Horizontal rule
            elif line.strip() in ("---", "***", "___"):
                blocks.append(self._divider_block())

            # Regular paragraph
            else:
                # Collect consecutive paragraph lines
                para_lines = [line]
                while (
                    i + 1 < len(lines)
                    and lines[i + 1].strip()
                    and not lines[i + 1].startswith("#")
                    and not lines[i + 1].strip().startswith("-")
                    and not lines[i + 1].strip().startswith("*")
                    and not re.match(r"^\d+\.\s", lines[i + 1].strip())
                    and not lines[i + 1].strip().startswith("```")
                    and not lines[i + 1].strip().startswith(">")
                    and lines[i + 1].strip() not in ("---", "***", "___")
                ):
                    i += 1
                    para_lines.append(lines[i])

                text = " ".join(para_lines)
                if text.strip():
                    blocks.append(self._paragraph_block(text))

            i += 1

        return blocks

    def _paragraph_block(self, text: str) -> dict[str, Any]:
        """Create a paragraph block."""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": self._rich_text(text),
            },
        }

    def _heading_block(self, text: str, level: int = 1) -> dict[str, Any]:
        """Create a heading block."""
        heading_type = f"heading_{level}"
        return {
            "object": "block",
            "type": heading_type,
            heading_type: {
                "rich_text": self._rich_text(text),
            },
        }

    def _bulleted_list_block(self, text: str) -> dict[str, Any]:
        """Create a bulleted list item block."""
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": self._rich_text(text),
            },
        }

    def _numbered_list_block(self, text: str) -> dict[str, Any]:
        """Create a numbered list item block."""
        return {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": self._rich_text(text),
            },
        }

    def _code_block(self, code: str, language: str = "plain text") -> dict[str, Any]:
        """Create a code block."""
        return {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [{"type": "text", "text": {"content": code}}],
                "language": language.lower(),
            },
        }

    def _quote_block(self, text: str) -> dict[str, Any]:
        """Create a quote block."""
        return {
            "object": "block",
            "type": "quote",
            "quote": {
                "rich_text": self._rich_text(text),
            },
        }

    def _divider_block(self) -> dict[str, Any]:
        """Create a divider block."""
        return {
            "object": "block",
            "type": "divider",
            "divider": {},
        }

    def _rich_text(self, text: str) -> list[dict[str, Any]]:
        """Convert text to rich text format with basic formatting."""
        # Handle bold (**text**)
        parts = []
        remaining = text

        # Simple approach: just return plain text for now
        # More complex formatting can be added later
        if remaining:
            parts.append({
                "type": "text",
                "text": {"content": remaining},
            })

        return parts
