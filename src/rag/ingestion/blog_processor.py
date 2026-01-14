"""
Blog article processor for RAG ingestion.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.rag.ingestion.chunking import ChunkingStrategy, DocumentChunker
from src.rag.vector_store.chroma_store import Document
from src.utils.logger import get_logger


@dataclass
class BlogArticle:
    """Represents a parsed blog article."""

    title: str
    content: str
    metadata: dict[str, Any]
    file_path: str


class BlogProcessor:
    """Processor for blog articles (Markdown/HTML)."""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> None:
        self.chunker = DocumentChunker(chunk_size, chunk_overlap)
        self.logger = get_logger("rag.ingestion.blog")

    def parse_markdown(self, file_path: Path) -> BlogArticle:
        """Parse a Markdown blog article."""
        content = file_path.read_text(encoding="utf-8")

        # Extract title from first H1 or filename
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = title_match.group(1) if title_match else file_path.stem

        # Extract frontmatter if present
        metadata = {}
        frontmatter_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            for line in frontmatter.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip()
            content = content[frontmatter_match.end() :]

        # Clean content
        content = self._clean_markdown(content)

        return BlogArticle(
            title=title,
            content=content,
            metadata=metadata,
            file_path=str(file_path),
        )

    def _clean_markdown(self, content: str) -> str:
        """Clean Markdown content for better embedding."""
        # Remove code blocks
        content = re.sub(r"```[\s\S]*?```", "", content)

        # Remove inline code
        content = re.sub(r"`[^`]+`", "", content)

        # Remove images
        content = re.sub(r"!\[.*?\]\(.*?\)", "", content)

        # Remove links but keep text
        content = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", content)

        # Remove HTML tags
        content = re.sub(r"<[^>]+>", "", content)

        # Normalize whitespace
        content = re.sub(r"\n{3,}", "\n\n", content)
        content = re.sub(r" +", " ", content)

        return content.strip()

    async def process_file(
        self,
        file_path: str | Path,
        collection_type: str = "style",
    ) -> list[Document]:
        """Process a blog article file into documents."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        self.logger.info("Processing blog article", file=str(file_path))

        article = self.parse_markdown(file_path)

        # Determine chunking strategy based on collection type
        strategy = (
            ChunkingStrategy.SEMANTIC
            if collection_type == "style"
            else ChunkingStrategy.PARAGRAPH
        )

        chunks = self.chunker.chunk(
            article.content,
            strategy=strategy,
            metadata={
                "source": str(file_path),
                "title": article.title,
                "collection_type": collection_type,
                **article.metadata,
            },
        )

        documents = []
        for chunk in chunks:
            doc_id = f"{file_path.stem}_{chunk.metadata.get('chunk_index', uuid4())}"
            documents.append(
                Document(
                    id=doc_id,
                    content=chunk.content,
                    metadata=chunk.metadata,
                )
            )

        self.logger.info(
            "Blog article processed",
            file=str(file_path),
            chunks=len(documents),
        )

        return documents

    async def process_directory(
        self,
        directory: str | Path,
        collection_type: str = "style",
    ) -> list[Document]:
        """Process all blog articles in a directory."""
        directory = Path(directory)

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        all_documents = []

        for file_path in directory.glob("**/*.md"):
            try:
                documents = await self.process_file(file_path, collection_type)
                all_documents.extend(documents)
            except Exception as e:
                self.logger.error(
                    "Failed to process file",
                    file=str(file_path),
                    error=str(e),
                )

        self.logger.info(
            "Directory processed",
            directory=str(directory),
            total_documents=len(all_documents),
        )

        return all_documents
