"""
RAG Query skill for retrieving relevant documents.
"""

from __future__ import annotations

from src.core.registry import skill_registry
from src.interfaces.skill_interface import SkillContext, SkillParameter, SkillResult, SkillStatus
from src.rag.rag_service import RAGService
from src.rag.vector_store.chroma_store import ChromaVectorStore
from src.skills.base import BaseSkill


@skill_registry.register(name="rag_query", category="rag")
class RAGQuerySkill(BaseSkill):
    """Skill for querying the RAG system."""

    name = "rag_query"
    description = "Query the RAG system for relevant documents"
    category = "rag"
    parameters = [
        SkillParameter(
            name="query",
            param_type=str,
            description="The query to search for",
            required=True,
        ),
        SkillParameter(
            name="collection",
            param_type=str,
            description="Collection to search (style, knowledge, or both)",
            required=False,
            default="both",
        ),
        SkillParameter(
            name="n_results",
            param_type=int,
            description="Number of results to return",
            required=False,
            default=5,
        ),
        SkillParameter(
            name="format_as_context",
            param_type=bool,
            description="Whether to format results as context string",
            required=False,
            default=True,
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._rag_service: RAGService | None = None

    def _get_rag_service(self) -> RAGService:
        """Get or create the RAG service."""
        if self._rag_service is None:
            self._rag_service = RAGService()
        return self._rag_service

    async def _execute(self, context: SkillContext) -> SkillResult:
        """Execute the RAG query."""
        query = context.get("query")
        collection = context.get("collection", "both")
        n_results = context.get("n_results", 5)
        format_as_context = context.get("format_as_context", True)

        try:
            rag = self._get_rag_service()

            # Map collection parameter to actual collection names
            if collection == "style":
                result = await rag.retriever.retrieve_style_references(
                    query, n_results
                )
            elif collection == "knowledge":
                result = await rag.retriever.retrieve_knowledge(query, n_results)
            else:
                # Query both
                result = await rag.query(query, n_results=n_results)

            if format_as_context:
                output = rag.retriever.format_context(result)
            else:
                output = {
                    "documents": [
                        {
                            "content": doc.content,
                            "metadata": doc.metadata,
                        }
                        for doc in result.documents
                    ],
                    "scores": result.scores,
                }

            return SkillResult(
                skill_name=self.name,
                success=True,
                status=SkillStatus.COMPLETED,
                output=output,
                metadata={
                    "query": query,
                    "collection": collection,
                    "results_count": len(result.documents),
                },
            )

        except Exception as e:
            self.logger.error("RAG query failed", error=str(e))
            return SkillResult(
                skill_name=self.name,
                success=False,
                status=SkillStatus.FAILED,
                error=str(e),
            )
