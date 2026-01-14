"""
Quality Reviewer Agent for final quality checks.
"""

from __future__ import annotations

from src.agents.base.agent import BaseAgent
from src.core.registry import agent_registry
from src.interfaces.agent_interface import AgentCapability, Task, TaskResult
from src.skills.llm_call import LLMCallSkill
from src.skills.rag_query import RAGQuerySkill


@agent_registry.register(name="quality_reviewer", category="content")
class QualityReviewerAgent(BaseAgent):
    """
    Quality Reviewer Agent for final quality checks.

    Capabilities:
    - Fact checking against knowledge base
    - Quality scoring
    - Compliance verification
    - Final approval or revision requests
    """

    name = "quality_reviewer"
    description = "Performs final quality checks and approval"
    category = "content"

    def _setup(self) -> None:
        """Initialize agent with skills and capabilities."""
        super()._setup()

        self.add_skill(LLMCallSkill())
        self.add_skill(RAGQuerySkill())

        self.add_capability(
            AgentCapability(
                name="quality_review",
                description="Review content quality",
                task_types=["quality", "final_review", "approve", "validate"],
                required_skills=["llm_call", "rag_query"],
                priority=6,
            )
        )

    async def _execute_task(self, task: Task) -> TaskResult:
        """Execute quality review task."""
        seo_content = task.metadata.get("seo", {})
        content = seo_content.get("content", task.description)
        topic = seo_content.get("topic", "")
        min_score = task.metadata.get("min_quality_score", 75)

        self.logger.info("Starting quality review", topic=topic)

        # Step 1: Check against knowledge base for accuracy
        rag_result = await self.execute_skill(
            "rag_query",
            params={
                "query": topic,
                "collection": "knowledge",
                "n_results": 3,
            },
        )
        knowledge_context = rag_result.output if rag_result.success else ""

        # Step 2: Quality assessment
        review_prompt = f"""Faça uma revisão de qualidade completa do seguinte conteúdo:

CONTEÚDO:
{content}

CONTEXTO DE VERIFICAÇÃO (do nosso banco de conhecimento):
{knowledge_context}

Por favor, avalie o conteúdo nos seguintes critérios (0-100 cada):

1. PRECISÃO (25 pontos)
- As informações místicas/espirituais são apresentadas com respeito e precisão?
- Os conceitos de negócios são corretos e aplicáveis?
- Há afirmações que precisam de correção?

2. CLAREZA E LEGIBILIDADE (25 pontos)
- O texto é fácil de entender?
- A estrutura é lógica e bem organizada?
- As transições são suaves?

3. ENGAJAMENTO (25 pontos)
- O conteúdo é interessante e envolvente?
- O leitor é motivado a continuar lendo?
- Há um bom equilíbrio entre informação e entretenimento?

4. RELEVÂNCIA E VALOR (25 pontos)
- O conteúdo oferece valor real ao leitor?
- As conexões entre misticismo e gestão são convincentes?
- O leitor sai com insights práticos?

FORNEÇA:

1. PONTUAÇÃO DETALHADA
   - Precisão: X/25
   - Clareza: X/25
   - Engajamento: X/25
   - Valor: X/25
   - TOTAL: X/100

2. PONTOS FORTES
   - Liste 3-5 aspectos positivos

3. ÁREAS DE MELHORIA
   - Liste problemas encontrados (se houver)
   - Sugira correções específicas

4. DECISÃO FINAL
   - APROVADO (se score >= {min_score})
   - REVISÃO NECESSÁRIA (se score < {min_score}, liste o que precisa mudar)

5. FEEDBACK ADICIONAL
   - Observações gerais
   - Sugestões para conteúdos futuros relacionados"""

        system_prompt = """Você é um revisor de qualidade editorial experiente, especializado em conteúdo
que une espiritualidade e negócios. Você é criterioso mas justo, identificando problemas reais
sem ser excessivamente crítico. Seu objetivo é garantir que o conteúdo publicado seja de alta qualidade
e agregue valor genuíno aos leitores."""

        review_result = await self.execute_skill(
            "llm_call",
            params={
                "prompt": review_prompt,
                "system_prompt": system_prompt,
            },
        )

        if not review_result.success:
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error=review_result.error,
            )

        # Parse approval status from response
        review_output = review_result.output
        approved = "APROVADO" in review_output.upper() and "REVISÃO NECESSÁRIA" not in review_output.upper()

        quality_result = {
            "review": review_output,
            "approved": approved,
            "content": content,
            "topic": topic,
            "seo": seo_content,
        }

        return TaskResult(
            task_id=task.task_id,
            success=True,
            output=quality_result,
            metadata={"approved": approved},
        )
