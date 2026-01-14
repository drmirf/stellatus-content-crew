"""
Web Search skill using DuckDuckGo.
"""

from __future__ import annotations

from duckduckgo_search import DDGS

from src.core.registry import skill_registry
from src.interfaces.skill_interface import SkillContext, SkillParameter, SkillResult, SkillStatus
from src.skills.base import BaseSkill


@skill_registry.register(name="web_search", category="search")
class WebSearchSkill(BaseSkill):
    """Skill for searching the web."""

    name = "web_search"
    description = "Search the web for information using DuckDuckGo"
    category = "search"
    parameters = [
        SkillParameter(
            name="query",
            param_type=str,
            description="The search query",
            required=True,
        ),
        SkillParameter(
            name="max_results",
            param_type=int,
            description="Maximum number of results",
            required=False,
            default=5,
        ),
        SkillParameter(
            name="region",
            param_type=str,
            description="Region for search results",
            required=False,
            default="wt-wt",
        ),
    ]

    async def _execute(self, context: SkillContext) -> SkillResult:
        """Execute the web search."""
        query = context.get("query")
        max_results = context.get("max_results", 5)
        region = context.get("region", "wt-wt")

        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(
                    query,
                    region=region,
                    max_results=max_results,
                ))

            # Format results
            formatted_results = []
            for r in results:
                formatted_results.append({
                    "title": r.get("title", ""),
                    "body": r.get("body", ""),
                    "href": r.get("href", ""),
                })

            # Create summary text
            summary_parts = []
            for i, r in enumerate(formatted_results, 1):
                summary_parts.append(
                    f"[{i}] {r['title']}\n{r['body']}\nSource: {r['href']}"
                )
            summary = "\n\n".join(summary_parts)

            return SkillResult(
                skill_name=self.name,
                success=True,
                status=SkillStatus.COMPLETED,
                output={
                    "results": formatted_results,
                    "summary": summary,
                    "query": query,
                },
                metadata={"results_count": len(formatted_results)},
            )

        except Exception as e:
            self.logger.error("Web search failed", error=str(e))
            return SkillResult(
                skill_name=self.name,
                success=False,
                status=SkillStatus.FAILED,
                error=str(e),
            )
