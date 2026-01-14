"""
ChromaDB vector store implementation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.core.config import get_settings
from src.core.exceptions import VectorStoreError
from src.utils.logger import get_logger


@dataclass
class Document:
    """Represents a document in the vector store."""

    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None


@dataclass
class QueryResult:
    """Result from a vector store query."""

    documents: list[Document]
    distances: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


class ChromaVectorStore:
    """ChromaDB vector store for RAG."""

    # Collection names
    STYLE_COLLECTION = "style_reference"
    KNOWLEDGE_COLLECTION = "knowledge_base"

    def __init__(self, persist_directory: str | Path | None = None) -> None:
        settings = get_settings()
        self.persist_directory = Path(
            persist_directory or settings.rag.vector_store_path
        )
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self.logger = get_logger("rag.vector_store.chroma")

        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        self.logger.info(
            "ChromaDB initialized",
            persist_directory=str(self.persist_directory),
        )

    def get_or_create_collection(
        self,
        name: str,
        metadata: dict[str, Any] | None = None,
    ) -> chromadb.Collection:
        """Get or create a collection."""
        return self.client.get_or_create_collection(
            name=name,
            metadata=metadata or {},
        )

    async def add_documents(
        self,
        collection_name: str,
        documents: list[Document],
    ) -> None:
        """Add documents to a collection."""
        try:
            collection = self.get_or_create_collection(collection_name)

            ids = [doc.id for doc in documents]
            contents = [doc.content for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            embeddings = [doc.embedding for doc in documents if doc.embedding]

            if embeddings and len(embeddings) == len(documents):
                collection.add(
                    ids=ids,
                    documents=contents,
                    metadatas=metadatas,
                    embeddings=embeddings,
                )
            else:
                collection.add(
                    ids=ids,
                    documents=contents,
                    metadatas=metadatas,
                )

            self.logger.info(
                "Documents added to collection",
                collection=collection_name,
                count=len(documents),
            )

        except Exception as e:
            self.logger.error("Failed to add documents", error=str(e))
            raise VectorStoreError("add", str(e)) from e

    async def query(
        self,
        collection_name: str,
        query_embedding: list[float],
        n_results: int = 5,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None,
    ) -> QueryResult:
        """Query a collection by embedding similarity."""
        try:
            collection = self.get_or_create_collection(collection_name)

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                where_document=where_document,
                include=["documents", "metadatas", "distances"],
            )

            documents = []
            for i, doc_id in enumerate(results["ids"][0]):
                documents.append(
                    Document(
                        id=doc_id,
                        content=results["documents"][0][i],
                        metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                    )
                )

            return QueryResult(
                documents=documents,
                distances=results["distances"][0] if results["distances"] else [],
            )

        except Exception as e:
            self.logger.error("Query failed", error=str(e))
            raise VectorStoreError("query", str(e)) from e

    async def query_by_text(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> QueryResult:
        """Query a collection by text (uses ChromaDB's built-in embedding)."""
        try:
            collection = self.get_or_create_collection(collection_name)

            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"],
            )

            documents = []
            for i, doc_id in enumerate(results["ids"][0]):
                documents.append(
                    Document(
                        id=doc_id,
                        content=results["documents"][0][i],
                        metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                    )
                )

            return QueryResult(
                documents=documents,
                distances=results["distances"][0] if results["distances"] else [],
            )

        except Exception as e:
            self.logger.error("Text query failed", error=str(e))
            raise VectorStoreError("query", str(e)) from e

    def delete_collection(self, collection_name: str) -> None:
        """Delete a collection."""
        try:
            self.client.delete_collection(collection_name)
            self.logger.info("Collection deleted", collection=collection_name)
        except Exception as e:
            self.logger.error("Failed to delete collection", error=str(e))
            raise VectorStoreError("delete", str(e)) from e

    def list_collections(self) -> list[str]:
        """List all collections."""
        collections = self.client.list_collections()
        return [c.name for c in collections]

    def get_collection_count(self, collection_name: str) -> int:
        """Get the number of documents in a collection."""
        try:
            collection = self.get_or_create_collection(collection_name)
            return collection.count()
        except Exception:
            return 0
