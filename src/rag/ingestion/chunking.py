"""
Text chunking strategies for document processing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class ChunkingStrategy(Enum):
    """Available chunking strategies."""

    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"
    PARAGRAPH = "paragraph"
    SLIDING_WINDOW = "sliding_window"


@dataclass
class Chunk:
    """Represents a chunk of text."""

    id: str = field(default_factory=lambda: str(uuid4()))
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    start_index: int = 0
    end_index: int = 0


class DocumentChunker:
    """Chunking utility for documents."""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(
        self,
        text: str,
        strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC,
        metadata: dict[str, Any] | None = None,
    ) -> list[Chunk]:
        """Chunk text using the specified strategy."""
        metadata = metadata or {}

        if strategy == ChunkingStrategy.FIXED_SIZE:
            return self._chunk_fixed_size(text, metadata)
        elif strategy == ChunkingStrategy.SEMANTIC:
            return self._chunk_semantic(text, metadata)
        elif strategy == ChunkingStrategy.PARAGRAPH:
            return self._chunk_paragraph(text, metadata)
        elif strategy == ChunkingStrategy.SLIDING_WINDOW:
            return self._chunk_sliding_window(text, metadata)
        else:
            return self._chunk_fixed_size(text, metadata)

    def _chunk_fixed_size(
        self,
        text: str,
        metadata: dict[str, Any],
    ) -> list[Chunk]:
        """Split text into fixed-size chunks."""
        chunks = []
        start = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))

            # Try to break at word boundary
            if end < len(text):
                last_space = text.rfind(" ", start, end)
                if last_space > start:
                    end = last_space

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    Chunk(
                        content=chunk_text,
                        metadata={**metadata, "chunk_index": len(chunks)},
                        start_index=start,
                        end_index=end,
                    )
                )

            start = end - self.chunk_overlap if end < len(text) else len(text)

        return chunks

    def _chunk_semantic(
        self,
        text: str,
        metadata: dict[str, Any],
    ) -> list[Chunk]:
        """Split text at sentence boundaries."""
        # Split into sentences
        sentences = re.split(r"(?<=[.!?])\s+", text)

        chunks = []
        current_chunk = ""
        current_start = 0

        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= self.chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk.strip():
                    chunks.append(
                        Chunk(
                            content=current_chunk.strip(),
                            metadata={**metadata, "chunk_index": len(chunks)},
                            start_index=current_start,
                            end_index=current_start + len(current_chunk),
                        )
                    )
                current_start = current_start + len(current_chunk)
                current_chunk = sentence + " "

        # Add remaining text
        if current_chunk.strip():
            chunks.append(
                Chunk(
                    content=current_chunk.strip(),
                    metadata={**metadata, "chunk_index": len(chunks)},
                    start_index=current_start,
                    end_index=current_start + len(current_chunk),
                )
            )

        return chunks

    def _chunk_paragraph(
        self,
        text: str,
        metadata: dict[str, Any],
    ) -> list[Chunk]:
        """Split text at paragraph boundaries."""
        paragraphs = re.split(r"\n\n+", text)

        chunks = []
        current_chunk = ""
        current_start = 0
        position = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                position += 2  # Account for paragraph break
                continue

            if len(current_chunk) + len(para) <= self.chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk.strip():
                    chunks.append(
                        Chunk(
                            content=current_chunk.strip(),
                            metadata={**metadata, "chunk_index": len(chunks)},
                            start_index=current_start,
                            end_index=position,
                        )
                    )
                current_start = position
                current_chunk = para + "\n\n"

            position += len(para) + 2

        # Add remaining text
        if current_chunk.strip():
            chunks.append(
                Chunk(
                    content=current_chunk.strip(),
                    metadata={**metadata, "chunk_index": len(chunks)},
                    start_index=current_start,
                    end_index=position,
                )
            )

        return chunks

    def _chunk_sliding_window(
        self,
        text: str,
        metadata: dict[str, Any],
    ) -> list[Chunk]:
        """Split text using sliding window with overlap."""
        chunks = []
        start = 0
        step = self.chunk_size - self.chunk_overlap

        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    Chunk(
                        content=chunk_text,
                        metadata={**metadata, "chunk_index": len(chunks)},
                        start_index=start,
                        end_index=end,
                    )
                )

            if end >= len(text):
                break

            start += step

        return chunks
