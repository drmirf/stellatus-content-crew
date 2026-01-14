"""
Research Agent for topic discovery and information gathering.
"""

from __future__ import annotations

from src.agents.base.agent import BaseAgent
from src.core.registry import agent_registry
from src.interfaces.agent_interface import AgentCapability, Task, TaskResult
from src.skills.llm_call import LLMCallSkill
from src.skills.rag_query import RAGQuerySkill
from src.skills.web_search import WebSearchSkill


@agent_registry.register(name="research", category="content")
class ResearchAgent(BaseAgent):
    """
    Research Agent for discovering topics and gathering information.

    Capabilities:
    - Topic discovery and trend analysis
    - Web research for current information
    - RAG queries for existing knowledge
    - Source compilation and verification
    """

    name = "research"
    description = "Discovers topics, gathers information, and compiles research briefs"
    category = "content"

    def _setup(self) -> None:
        """Initialize agent with skills and capabilities."""
        super()._setup()

        # Add skills
        self.add_skill(WebSearchSkill())
        self.add_skill(RAGQuerySkill())
        self.add_skill(LLMCallSkill())

        # Define capabilities
        self.add_capability(
            AgentCapability(
                name="research",
                description="Research topics and gather information",
                task_types=["research", "discover", "gather", "verify"],
                required_skills=["web_search", "rag_query", "llm_call"],
                priority=10,
            )
        )

    async def _execute_task(self, task: Task) -> TaskResult:
        """Execute research task."""
        topic = task.description
        metadata = task.metadata

        self.logger.info("Starting research", topic=topic)

        research_data = {
            "topic": topic,
            "web_results": None,
            "rag_context": None,
            "analysis": None,
        }

        # Step 1: Search the web for current information
        web_result = await self.execute_skill(
            "web_search",
            params={
                "query": f"{topic} misticismo gestão negócios",
                "max_results": 5,
            },
        )
        if web_result.success:
            research_data["web_results"] = web_result.output

        # Step 2: Query RAG for existing knowledge
        rag_result = await self.execute_skill(
            "rag_query",
            params={
                "query": topic,
                "collection": "both",
                "n_results": 5,
            },
        )
        if rag_result.success:
            research_data["rag_context"] = rag_result.output

        # Step 3: Analyze and synthesize findings
        analysis_prompt = f"""Analise as seguintes informações sobre o tópico "{topic}" e crie um resumo de pesquisa estruturado.

INFORMAÇÕES DA WEB:
{research_data.get('web_results', {}).get('summary', 'Nenhuma informação encontrada')}

CONHECIMENTO EXISTENTE:
{research_data.get('rag_context', 'Nenhum contexto disponível')}

Por favor, forneça:
1. PRINCIPAIS PONTOS: Os insights mais importantes sobre o tópico
2. CONEXÃO MISTICISMO-GESTÃO: Como o tema conecta sabedoria ancestral com práticas de negócios
3. ÂNGULOS DE CONTEÚDO: 3-5 ângulos interessantes para abordar o tema
4. FONTES E REFERÊNCIAS: Resumo das fontes encontradas
5. PALAVRAS-CHAVE SUGERIDAS: Termos relevantes para o conteúdo

Mantenha o tom equilibrado entre espiritualidade e pragmatismo nos negócios."""

        system_prompt = """Você é um pesquisador especializado em criar conexões entre sabedoria ancestral/misticismo
e práticas modernas de gestão e negócios. Seu objetivo é encontrar insights únicos que unam
esses dois mundos de forma autêntica e prática."""

        analysis_result = await self.execute_skill(
            "llm_call",
            params={
                "prompt": analysis_prompt,
                "system_prompt": system_prompt,
            },
        )

        if analysis_result.success:
            research_data["analysis"] = analysis_result.output

        # Compile research brief
        research_brief = {
            "topic": topic,
            "analysis": research_data.get("analysis", ""),
            "web_sources": research_data.get("web_results", {}).get("results", []),
            "rag_context": research_data.get("rag_context", ""),
            "metadata": metadata,
        }

        return TaskResult(
            task_id=task.task_id,
            success=True,
            output=research_brief,
            metadata={"sources_count": len(research_brief.get("web_sources", []))},
        )
