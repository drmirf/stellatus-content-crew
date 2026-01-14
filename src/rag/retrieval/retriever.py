"""
RAG retrieval service.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.config import get_settings
from src.rag.embeddings.base import BaseEmbedding
from src.rag.embeddings.openai_embeddings import OpenAIEmbeddings
from src.rag.vector_store.chroma_store import ChromaVectorStore, Document, QueryResult
from src.utils.logger import get_logger


@dataclass
class RetrievalResult:
    """Result from a retrieval query."""

    documents: list[Document]
    scores: list[float]
    query: str
    collection: str


class RAGRetriever:
    """Retrieval service for RAG queries."""

    def __init__(
        self,
        vector_store: ChromaVectorStore | None = None,
        embedding_service: BaseEmbedding | None = None,
    ) -> None:
        settings = get_settings()
        self.vector_store = vector_store or ChromaVectorStore()

        # Initialize embedding service
        if embedding_service:
            self.embedding_service = embedding_service
        else:
            try:
                self.embedding_service = OpenAIEmbeddings()
            except ValueError:
                # No API key, use ChromaDB's default embedding
                self.embedding_service = None

        self.default_n_results = settings.rag.default_n_results
        self.logger = get_logger("rag.retrieval")

    async def retrieve(
        self,
        query: str,
        collection: str,
        n_results: int | None = None,
        filter_metadata: dict[str, Any] | None = None,
    ) -> RetrievalResult:
        """Retrieve relevant documents for a query."""
        n = n_results or self.default_n_results

        self.logger.info(
            "Retrieving documents",
            query=query[:50] + "..." if len(query) > 50 else query,
            collection=collection,
            n_results=n,
        )

        if self.embedding_service:
            # Use custom embeddings
            query_embedding = await self.embedding_service.embed_text(query)
            result = await self.vector_store.query(
                collection_name=collection,
                query_embedding=query_embedding,
                n_results=n,
                where=filter_metadata,
            )
        else:
            # Use ChromaDB's default embedding
            result = await self.vector_store.query_by_text(
                collection_name=collection,
                query_text=query,
                n_results=n,
                where=filter_metadata,
            )

        # Convert distances to similarity scores (lower distance = higher similarity)
        scores = [1.0 / (1.0 + d) for d in result.distances] if result.distances else []

        self.logger.info(
            "Documents retrieved",
            count=len(result.documents),
            top_score=scores[0] if scores else 0,
        )

        return RetrievalResult(
            documents=result.documents,
            scores=scores,
            query=query,
            collection=collection,
        )

    async def retrieve_style_references(
        self,
        query: str,
        n_results: int = 5,
    ) -> RetrievalResult:
        """Retrieve similar content for style matching."""
        return await self.retrieve(
            query=query,
            collection=ChromaVectorStore.STYLE_COLLECTION,
            n_results=n_results,
        )

    async def retrieve_knowledge(
        self,
        query: str,
        n_results: int = 10,
        tags: list[str] | None = None,
    ) -> RetrievalResult:
        """Retrieve relevant knowledge base content."""
        filter_metadata = None
        if tags:
            filter_metadata = {"tags": {"$in": tags}}

        return await self.retrieve(
            query=query,
            collection=ChromaVectorStore.KNOWLEDGE_COLLECTION,
            n_results=n_results,
            filter_metadata=filter_metadata,
        )

    async def retrieve_combined(
        self,
        query: str,
        style_results: int = 3,
        knowledge_results: int = 5,
    ) -> dict[str, RetrievalResult]:
        """Retrieve from both collections."""
        style = await self.retrieve_style_references(query, style_results)
        knowledge = await self.retrieve_knowledge(query, knowledge_results)

        return {
            "style": style,
            "knowledge": knowledge,
        }

    def format_context(
        self,
        retrieval_result: RetrievalResult,
        max_length: int = 3000,
    ) -> str:
        """Format retrieved documents as context string."""
        context_parts = []
        current_length = 0

        for i, doc in enumerate(retrieval_result.documents):
            source = doc.metadata.get("source", "Unknown")
            title = doc.metadata.get("title", "")

            header = f"[Source {i + 1}: {title or source}]"
            content = doc.content

            section = f"{header}\n{content}\n"

            if current_length + len(section) > max_length:
                break

            context_parts.append(section)
            current_length += len(section)

        return "\n".join(context_parts)
