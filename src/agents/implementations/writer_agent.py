"""
Writer Agent for creating content drafts.
"""

from __future__ import annotations

from src.agents.base.agent import BaseAgent
from src.core.registry import agent_registry
from src.interfaces.agent_interface import AgentCapability, Task, TaskResult
from src.skills.llm_call import LLMCallSkill
from src.skills.rag_query import RAGQuerySkill


@agent_registry.register(name="writer", category="content")
class WriterAgent(BaseAgent):
    """
    Writer Agent for creating content drafts.

    Capabilities:
    - Blog post writing
    - Content expansion from outlines
    - Style matching using RAG
    - Spiritual/business content integration
    """

    name = "writer"
    description = "Creates content drafts based on research and style references"
    category = "content"

    def _setup(self) -> None:
        """Initialize agent with skills and capabilities."""
        super()._setup()

        self.add_skill(LLMCallSkill())
        self.add_skill(RAGQuerySkill())

        self.add_capability(
            AgentCapability(
                name="writing",
                description="Create content drafts",
                task_types=["write", "create", "draft", "compose"],
                required_skills=["llm_call", "rag_query"],
                priority=9,
            )
        )

    async def _execute_task(self, task: Task) -> TaskResult:
        """Execute writing task."""
        research_brief = task.metadata.get("research", {})
        topic = research_brief.get("topic", task.description)
        target_length = task.metadata.get("target_length", 1500)
        user_context = task.metadata.get("user_context", "")
        writing_style = task.metadata.get("writing_style", "")

        self.logger.info(
            "Starting content creation",
            topic=topic,
            has_user_context=bool(user_context),
            has_writing_style=bool(writing_style),
        )

        # Step 1: Get style reference from RAG
        style_result = await self.execute_skill(
            "rag_query",
            params={
                "query": topic,
                "collection": "style",
                "n_results": 3,
                "format_as_context": True,
            },
        )
        rag_style_context = style_result.output if style_result.success else ""

        # Build style section for prompts
        style_section = ""
        if writing_style:
            style_section = f"""
ESTILO DE ESCRITA DO AUTOR (SEGUIR OBRIGATORIAMENTE):
{writing_style}
"""
        if rag_style_context:
            style_section += f"""
REFERÊNCIAS DE ESTILO DA BASE DE CONHECIMENTO:
{rag_style_context}
"""

        # Build user context section
        user_context_section = ""
        if user_context:
            user_context_section = f"""
DIRETRIZES ESPECÍFICAS DO USUÁRIO (INCORPORAR NO ARTIGO):
{user_context}
"""

        # Step 2: Create content outline
        outline_prompt = f"""Crie um outline detalhado para um artigo de blog sobre:

TÓPICO: {topic}
{user_context_section}
PESQUISA DISPONÍVEL:
{research_brief.get('analysis', 'Nenhuma análise disponível')}

BASE DE CONHECIMENTO (USAR COMO REFERÊNCIA):
{research_brief.get('rag_context', 'Não disponível')}

O artigo deve:
- Ter aproximadamente {target_length} palavras
- Equilibrar sabedoria mística/espiritual com aplicações práticas de gestão
- Incluir introdução envolvente, corpo com 3-5 seções, e conclusão com call-to-action
- Ser acessível para profissionais de negócios interessados em espiritualidade
- INCORPORAR as diretrizes do usuário quando fornecidas

Forneça o outline no formato:
1. Título sugerido
2. Introdução (gancho + contexto)
3. Seções principais (com subtópicos)
4. Conclusão (síntese + call-to-action)"""

        # Use custom writing style if available, otherwise use default
        if writing_style:
            system_prompt = f"""Você é um escritor que segue RIGOROSAMENTE o estilo de escrita definido abaixo.
{writing_style}

Adapte seu tom, voz e estrutura conforme o estilo definido."""
        else:
            system_prompt = """Você é um escritor especializado em conteúdo que une misticismo, espiritualidade
e sabedoria ancestral com práticas modernas de gestão e liderança. Seu estilo é:
- Acessível mas profundo
- Prático mas inspirador
- Respeitoso com tradições espirituais
- Aplicável ao mundo dos negócios"""

        outline_result = await self.execute_skill(
            "llm_call",
            params={
                "prompt": outline_prompt,
                "system_prompt": system_prompt,
            },
        )

        # Step 3: Write full content
        write_prompt = f"""Escreva um artigo completo de blog seguindo este outline:

{outline_result.output if outline_result.success else 'Crie um artigo estruturado sobre: ' + topic}
{style_section}
{user_context_section}
PESQUISA E INSIGHTS:
{research_brief.get('analysis', '')}

BASE DE CONHECIMENTO (USAR COMO REFERÊNCIA PRINCIPAL):
{research_brief.get('rag_context', '')}

INSTRUÇÕES (ORDEM DE PRIORIDADE):
1. PRIMEIRO: Siga o estilo de escrita definido
2. SEGUNDO: Baseie o conteúdo na base de conhecimento
3. TERCEIRO: Incorpore as diretrizes específicas do usuário
4. QUARTO: Complemente com a pesquisa adicional

- Escreva aproximadamente {target_length} palavras
- Use linguagem envolvente e acessível
- Inclua exemplos práticos quando possível
- Balance profundidade espiritual com aplicabilidade nos negócios
- Formate com headers Markdown (## para seções)
- Inclua uma introdução cativante e conclusão memorável

Escreva o artigo completo agora:"""

        content_result = await self.execute_skill(
            "llm_call",
            params={
                "prompt": write_prompt,
                "system_prompt": system_prompt,
                "max_tokens": 4096,
            },
        )

        if not content_result.success:
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error=content_result.error,
            )

        draft = {
            "content": content_result.output,
            "outline": outline_result.output if outline_result.success else "",
            "topic": topic,
            "word_count": len(content_result.output.split()),
            "research_brief": research_brief,
        }

        return TaskResult(
            task_id=task.task_id,
            success=True,
            output=draft,
            metadata={"word_count": draft["word_count"]},
        )
