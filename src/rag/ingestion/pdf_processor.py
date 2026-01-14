"""
PDF document processor for RAG ingestion.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from pypdf import PdfReader

from src.rag.ingestion.chunking import ChunkingStrategy, DocumentChunker
from src.rag.vector_store.chroma_store import Document
from src.utils.logger import get_logger


class PDFProcessor:
    """Processor for PDF documents."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
    ) -> None:
        self.chunker = DocumentChunker(chunk_size, chunk_overlap)
        self.logger = get_logger("rag.ingestion.pdf")

    def extract_text(self, file_path: Path) -> tuple[str, dict[str, Any]]:
        """Extract text and metadata from a PDF file."""
        reader = PdfReader(file_path)

        # Extract metadata
        metadata = {}
        if reader.metadata:
            if reader.metadata.title:
                metadata["title"] = reader.metadata.title
            if reader.metadata.author:
                metadata["author"] = reader.metadata.author
            if reader.metadata.subject:
                metadata["subject"] = reader.metadata.subject

        # Extract text from all pages
        text_parts = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(f"[Page {i + 1}]\n{page_text}")

        metadata["page_count"] = len(reader.pages)

        return "\n\n".join(text_parts), metadata

    async def process_file(
        self,
        file_path: str | Path,
        collection_type: str = "knowledge",
    ) -> list[Document]:
        """Process a PDF file into documents."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if file_path.suffix.lower() != ".pdf":
            raise ValueError(f"Not a PDF file: {file_path}")

        self.logger.info("Processing PDF", file=str(file_path))

        content, pdf_metadata = self.extract_text(file_path)

        if not content.strip():
            self.logger.warning("PDF has no extractable text", file=str(file_path))
            return []

        # Use paragraph chunking for PDFs (preserves structure better)
        chunks = self.chunker.chunk(
            content,
            strategy=ChunkingStrategy.PARAGRAPH,
            metadata={
                "source": str(file_path),
                "source_type": "pdf",
                "collection_type": collection_type,
                **pdf_metadata,
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
            "PDF processed",
            file=str(file_path),
            pages=pdf_metadata.get("page_count", 0),
            chunks=len(documents),
        )

        return documents

    async def process_directory(
        self,
        directory: str | Path,
        collection_type: str = "knowledge",
    ) -> list[Document]:
        """Process all PDF files in a directory."""
        directory = Path(directory)

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        all_documents = []

        for file_path in directory.glob("**/*.pdf"):
            try:
                documents = await self.process_file(file_path, collection_type)
                all_documents.extend(documents)
            except Exception as e:
                self.logger.error(
                    "Failed to process PDF",
                    file=str(file_path),
                    error=str(e),
                )

        self.logger.info(
            "Directory processed",
            directory=str(directory),
            total_documents=len(all_documents),
        )

        return all_documents
