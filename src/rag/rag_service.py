"""
Main RAG service facade.

Provides a unified interface for all RAG operations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.config import get_settings
from src.core.events import Event, EventType, event_bus
from src.rag.embeddings.openai_embeddings import OpenAIEmbeddings
from src.rag.ingestion.blog_processor import BlogProcessor
from src.rag.ingestion.pdf_processor import PDFProcessor
from src.rag.retrieval.retriever import RAGRetriever, RetrievalResult
from src.rag.vector_store.chroma_store import ChromaVectorStore, Document
from src.utils.logger import get_logger


class RAGService:
    """
    Main RAG service providing unified access to:
    - Document ingestion
    - Embedding generation
    - Vector storage
    - Retrieval
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.logger = get_logger("rag.service")

        # Initialize components
        self.vector_store = ChromaVectorStore()

        # Try to initialize embeddings (may fail if no API key)
        try:
            self.embeddings = OpenAIEmbeddings()
        except ValueError:
            self.embeddings = None
            self.logger.warning("OpenAI embeddings not available, using default")

        self.retriever = RAGRetriever(
            vector_store=self.vector_store,
            embedding_service=self.embeddings,
        )

        # Document processors
        self.blog_processor = BlogProcessor(
            chunk_size=settings.rag.chunk_size,
            chunk_overlap=settings.rag.chunk_overlap,
        )
        self.pdf_processor = PDFProcessor(
            chunk_size=settings.rag.chunk_size * 2,  # Larger chunks for PDFs
            chunk_overlap=settings.rag.chunk_overlap * 2,
        )

        self.logger.info("RAG service initialized")

    # ==================== Ingestion ====================

    async def ingest_blog_article(
        self,
        file_path: str | Path,
        add_embeddings: bool = True,
    ) -> int:
        """Ingest a blog article into the style collection."""
        self.logger.info("Ingesting blog article", file=str(file_path))

        await event_bus.publish(
            Event(
                type=EventType.RAG_INGESTION_STARTED,
                source="rag_service",
                data={"file": str(file_path), "type": "blog"},
            )
        )

        documents = await self.blog_processor.process_file(
            file_path,
            collection_type="style",
        )

        if add_embeddings and self.embeddings:
            documents = await self._add_embeddings(documents)

        await self.vector_store.add_documents(
            collection_name=ChromaVectorStore.STYLE_COLLECTION,
            documents=documents,
        )

        await event_bus.publish(
            Event(
                type=EventType.RAG_INGESTION_COMPLETED,
                source="rag_service",
                data={"file": str(file_path), "documents": len(documents)},
            )
        )

        return len(documents)

    async def ingest_pdf(
        self,
        file_path: str | Path,
        add_embeddings: bool = True,
    ) -> int:
        """Ingest a PDF into the knowledge collection."""
        self.logger.info("Ingesting PDF", file=str(file_path))

        await event_bus.publish(
            Event(
                type=EventType.RAG_INGESTION_STARTED,
                source="rag_service",
                data={"file": str(file_path), "type": "pdf"},
            )
        )

        documents = await self.pdf_processor.process_file(
            file_path,
            collection_type="knowledge",
        )

        if add_embeddings and self.embeddings:
            documents = await self._add_embeddings(documents)

        await self.vector_store.add_documents(
            collection_name=ChromaVectorStore.KNOWLEDGE_COLLECTION,
            documents=documents,
        )

        await event_bus.publish(
            Event(
                type=EventType.RAG_INGESTION_COMPLETED,
                source="rag_service",
                data={"file": str(file_path), "documents": len(documents)},
            )
        )

        return len(documents)

    async def ingest_directory(
        self,
        directory: str | Path,
        doc_type: str = "auto",
    ) -> int:
        """Ingest all documents from a directory."""
        directory = Path(directory)
        total = 0

        if doc_type in ("auto", "blog"):
            # Process markdown files
            blog_docs = await self.blog_processor.process_directory(
                directory,
                collection_type="style",
            )
            if blog_docs:
                if self.embeddings:
                    blog_docs = await self._add_embeddings(blog_docs)
                await self.vector_store.add_documents(
                    ChromaVectorStore.STYLE_COLLECTION,
                    blog_docs,
                )
                total += len(blog_docs)

        if doc_type in ("auto", "pdf"):
            # Process PDF files
            pdf_docs = await self.pdf_processor.process_directory(
                directory,
                collection_type="knowledge",
            )
            if pdf_docs:
                if self.embeddings:
                    pdf_docs = await self._add_embeddings(pdf_docs)
                await self.vector_store.add_documents(
                    ChromaVectorStore.KNOWLEDGE_COLLECTION,
                    pdf_docs,
                )
                total += len(pdf_docs)

        self.logger.info(
            "Directory ingestion complete",
            directory=str(directory),
            total_documents=total,
        )

        return total

    async def _add_embeddings(self, documents: list[Document]) -> list[Document]:
        """Add embeddings to documents."""
        if not self.embeddings:
            return documents

        texts = [doc.content for doc in documents]
        embeddings = await self.embeddings.embed_batch(texts)

        for doc, embedding in zip(documents, embeddings):
            doc.embedding = embedding

        return documents

    # ==================== Retrieval ====================

    async def query(
        self,
        query: str,
        collection: str | None = None,
        n_results: int = 5,
    ) -> RetrievalResult:
        """Query the RAG system."""
        await event_bus.publish(
            Event(
                type=EventType.RAG_QUERY_STARTED,
                source="rag_service",
                data={"query": query[:50]},
            )
        )

        if collection:
            result = await self.retriever.retrieve(
                query=query,
                collection=collection,
                n_results=n_results,
            )
        else:
            # Query both collections and merge
            combined = await self.retriever.retrieve_combined(
                query=query,
                style_results=n_results // 2,
                knowledge_results=n_results,
            )
            # Merge results prioritizing knowledge
            all_docs = combined["knowledge"].documents + combined["style"].documents
            all_scores = combined["knowledge"].scores + combined["style"].scores

            result = RetrievalResult(
                documents=all_docs[:n_results],
                scores=all_scores[:n_results],
                query=query,
                collection="combined",
            )

        await event_bus.publish(
            Event(
                type=EventType.RAG_QUERY_COMPLETED,
                source="rag_service",
                data={"query": query[:50], "results": len(result.documents)},
            )
        )

        return result

    async def get_style_context(self, topic: str, n_results: int = 3) -> str:
        """Get style reference context for a topic."""
        result = await self.retriever.retrieve_style_references(topic, n_results)
        return self.retriever.format_context(result)

    async def get_knowledge_context(self, topic: str, n_results: int = 5) -> str:
        """Get knowledge context for a topic."""
        result = await self.retriever.retrieve_knowledge(topic, n_results)
        return self.retriever.format_context(result)

    # ==================== Management ====================

    def list_collections(self) -> list[str]:
        """List all collections."""
        return self.vector_store.list_collections()

    def get_collection_count(self, collection: str) -> int:
        """Get document count in a collection."""
        return self.vector_store.get_collection_count(collection)

    def get_stats(self) -> dict[str, Any]:
        """Get RAG system statistics."""
        return {
            "collections": self.list_collections(),
            "style_documents": self.get_collection_count(
                ChromaVectorStore.STYLE_COLLECTION
            ),
            "knowledge_documents": self.get_collection_count(
                ChromaVectorStore.KNOWLEDGE_COLLECTION
            ),
            "embeddings_available": self.embeddings is not None,
        }
