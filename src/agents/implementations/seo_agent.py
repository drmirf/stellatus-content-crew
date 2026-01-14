"""
SEO Agent for search engine optimization.
"""

from __future__ import annotations

from src.agents.base.agent import BaseAgent
from src.core.registry import agent_registry
from src.interfaces.agent_interface import AgentCapability, Task, TaskResult
from src.skills.keyword_extraction import KeywordExtractionSkill
from src.skills.llm_call import LLMCallSkill


@agent_registry.register(name="seo", category="content")
class SEOAgent(BaseAgent):
    """
    SEO Agent for search engine optimization.

    Capabilities:
    - Keyword optimization
    - Meta tag generation
    - Content structure optimization
    - Internal/external link suggestions
    """

    name = "seo"
    description = "Optimizes content for search engines"
    category = "content"

    def _setup(self) -> None:
        """Initialize agent with skills and capabilities."""
        super()._setup()

        self.add_skill(LLMCallSkill())
        self.add_skill(KeywordExtractionSkill())

        self.add_capability(
            AgentCapability(
                name="seo_optimization",
                description="Optimize content for SEO",
                task_types=["optimize", "seo", "keywords", "meta"],
                required_skills=["llm_call", "keyword_extraction"],
                priority=7,
            )
        )

    async def _execute_task(self, task: Task) -> TaskResult:
        """Execute SEO optimization task."""
        edited_content = task.metadata.get("edited", {})
        content = edited_content.get("content", task.description)
        topic = edited_content.get("topic", "")

        self.logger.info("Starting SEO optimization", topic=topic)

        # Step 1: Extract keywords from content
        keyword_result = await self.execute_skill(
            "keyword_extraction",
            params={
                "text": content,
                "max_keywords": 15,
            },
        )
        keywords = keyword_result.output if keyword_result.success else {}

        # Step 2: Generate SEO optimization
        seo_prompt = f"""Otimize o seguinte conteúdo para SEO:

CONTEÚDO:
{content}

KEYWORDS EXTRAÍDAS:
{keywords.get('keywords', [])}

Por favor, forneça:

1. META TÍTULO (máx. 60 caracteres)
- Inclua keyword principal
- Seja atraente para cliques

2. META DESCRIÇÃO (máx. 160 caracteres)
- Resuma o valor do artigo
- Inclua call-to-action sutil
- Use keyword principal

3. SUGESTÕES DE OTIMIZAÇÃO DO CONTEÚDO
- Keywords para adicionar/enfatizar
- Melhorias em headers (H1, H2, H3)
- Oportunidades de links internos
- Alt text sugerido para imagens

4. CONTEÚDO OTIMIZADO
Reescreva o conteúdo incorporando:
- Keywords naturalmente distribuídas (densidade 1-2%)
- Headers otimizados com keywords
- Primeiro parágrafo com keyword principal
- Conclusão com keyword e CTA

5. SCHEMA MARKUP SUGERIDO (tipo de conteúdo)

Formate a resposta claramente com cada seção identificada."""

        system_prompt = """Você é um especialista em SEO para blogs de nicho (espiritualidade + negócios).
Você entende como otimizar conteúdo para ranquear bem no Google mantendo a qualidade e naturalidade do texto.
Foque em SEO on-page e experiência do usuário."""

        seo_result = await self.execute_skill(
            "llm_call",
            params={
                "prompt": seo_prompt,
                "system_prompt": system_prompt,
                "max_tokens": 4096,
            },
        )

        if not seo_result.success:
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error=seo_result.error,
            )

        seo_content = {
            "content": seo_result.output,
            "original_content": content,
            "keywords": keywords,
            "topic": topic,
            "edited": edited_content,
        }

        return TaskResult(
            task_id=task.task_id,
            success=True,
            output=seo_content,
            metadata={"keywords_count": len(keywords.get("keywords", []))},
        )
