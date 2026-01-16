"""
Notion publisher for submitting articles to a Notion database.
"""

from __future__ import annotations

import os
import re
import unicodedata
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
        status: str = "Not started",
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
        title = content.meta_title or content.topic
        slug = self._generate_slug(title)
        description = self._extract_description(content)

        properties = {
            # Title (required)
            "Title": {
                "title": [{"text": {"content": title[:2000]}}],
            },
            # Slug for URL (required by Vercel)
            "Slug": {
                "rich_text": [{"text": {"content": slug}}],
            },
            # Description for cards (required by Vercel)
            "Description": {
                "rich_text": [{"text": {"content": description[:2000]}}],
            },
            # Date (Vercel expects "Date", not "Created")
            "Date": {
                "date": {"start": content.created_at.isoformat()},
            },
            # Tags as multi-select (Vercel expects "Tags", not "Keywords")
            "Tags": {
                "multi_select": [{"name": kw[:100]} for kw in (content.keywords or [])[:10]],
            },
            # Published checkbox (required by Vercel - this is the main filter!)
            "Published": {
                "checkbox": content.approved,
            },
        }

        return properties

    def _generate_slug(self, title: str) -> str:
        """Generate URL slug from title."""
        # Normalize unicode characters (remove accents)
        slug = unicodedata.normalize("NFKD", title.lower())
        slug = slug.encode("ascii", "ignore").decode("ascii")
        # Remove non-word characters except spaces and hyphens
        slug = re.sub(r"[^\w\s-]", "", slug)
        # Replace spaces and multiple hyphens with single hyphen
        slug = re.sub(r"[-\s]+", "-", slug).strip("-")
        return slug

    def _extract_description(self, content: ContentResult) -> str:
        """Extract description from meta or content."""
        # Try to get meta description from SEO content
        if content.content and "META DESCRIÇÃO" in content.content.upper():
            lines = content.content.split("\n")
            for i, line in enumerate(lines):
                if "META DESCRIÇÃO" in line.upper():
                    # Get the next non-empty line
                    for next_line in lines[i + 1 : i + 5]:
                        cleaned = next_line.strip().strip(">").strip('"').strip()
                        if cleaned and not cleaned.startswith("#") and not cleaned.startswith("-"):
                            return cleaned[:300]

        # Fallback: extract from article content
        article = self._extract_article_content(content.content or "")
        # Remove markdown headers and get first paragraph
        clean_text = re.sub(r"^#+\s+.*$", "", article, flags=re.MULTILINE)
        clean_text = re.sub(r"\*\*|__|\*|_", "", clean_text)  # Remove bold/italic
        clean_text = clean_text.strip()

        if clean_text:
            # Get first 160 chars, break at word boundary
            if len(clean_text) > 160:
                return clean_text[:160].rsplit(" ", 1)[0] + "..."
            return clean_text

        return content.topic or ""

    def _extract_article_content(self, raw_content: str) -> str:
        """Extract only the article content, excluding SEO sections."""
        # Try to find content after "CONTEÚDO OTIMIZADO" section
        markers = ["## 4. CONTEÚDO OTIMIZADO", "## CONTEÚDO OTIMIZADO", "# CONTEÚDO OTIMIZADO"]
        for marker in markers:
            if marker in raw_content:
                content = raw_content.split(marker, 1)[1].strip()
                # Remove everything after the final --- separator (quotes, etc.)
                if "\n---\n" in content:
                    content = content.split("\n---\n")[0].strip()
                return content

        # Fallback: skip YAML front matter and return rest
        if raw_content.startswith("---"):
            parts = raw_content.split("---", 2)
            if len(parts) >= 3:
                return parts[2].strip()

        return raw_content

    def _extract_seo_content(self, raw_content: str) -> str:
        """Extract SEO sections (1-3) from content."""
        if "# OTIMIZAÇÃO SEO" in raw_content:
            start = raw_content.find("# OTIMIZAÇÃO SEO")
            end_marker = "## 4. CONTEÚDO OTIMIZADO"
            if end_marker in raw_content:
                end = raw_content.find(end_marker)
                return raw_content[start:end].strip()
        return ""

    def _build_content_blocks(self, content: ContentResult) -> list[dict[str, Any]]:
        """Build Notion blocks from ContentResult."""
        blocks = []

        # 1. Main article content (clean, no SEO)
        if content.content:
            main_content = self._extract_article_content(content.content)
            content_blocks = self.client.markdown_to_blocks(main_content)
            blocks.extend(content_blocks[:95])

        # 2. Divider before additional info
        blocks.append({"type": "divider", "divider": {}})

        # 3. Toggle: SEO & Meta Tags
        if content.content:
            seo_content = self._extract_seo_content(content.content)
            if seo_content:
                seo_blocks = self.client.markdown_to_blocks(seo_content)
                blocks.append({
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": "SEO & Meta Tags"}}],
                        "children": seo_blocks[:95],
                    },
                })

        # 4. Toggle: Image Prompts
        if content.image_prompts:
            image_blocks = self.client.markdown_to_blocks(content.image_prompts)
            blocks.append({
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"type": "text", "text": {"content": "Prompts de Imagem"}}],
                    "children": image_blocks[:95],
                },
            })

        # 5. Toggle: Visual Suggestions
        if content.visual_suggestions:
            visual_blocks = self.client.markdown_to_blocks(content.visual_suggestions)
            blocks.append({
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"type": "text", "text": {"content": "Sugestões Visuais"}}],
                    "children": visual_blocks[:95],
                },
            })

        # 6. Toggle: Quality Review
        if content.quality_review:
            review_blocks = self.client.markdown_to_blocks(content.quality_review)
            blocks.append({
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"type": "text", "text": {"content": "Revisão de Qualidade"}}],
                    "children": review_blocks[:95],
                },
            })

        return blocks
