"""
Editor Agent for reviewing and improving content.
"""

from __future__ import annotations

from src.agents.base.agent import BaseAgent
from src.core.registry import agent_registry
from src.interfaces.agent_interface import AgentCapability, Task, TaskResult
from src.skills.llm_call import LLMCallSkill
from src.skills.rag_query import RAGQuerySkill


@agent_registry.register(name="editor", category="content")
class EditorAgent(BaseAgent):
    """
    Editor Agent for reviewing and improving content.

    Capabilities:
    - Grammar and spelling check
    - Style consistency review
    - Coherence and flow improvement
    - Tone adjustment
    """

    name = "editor"
    description = "Reviews and improves content for grammar, style, and coherence"
    category = "content"

    def _setup(self) -> None:
        """Initialize agent with skills and capabilities."""
        super()._setup()

        self.add_skill(LLMCallSkill())
        self.add_skill(RAGQuerySkill())

        self.add_capability(
            AgentCapability(
                name="editing",
                description="Edit and improve content",
                task_types=["edit", "review", "improve", "polish"],
                required_skills=["llm_call", "rag_query"],
                priority=8,
            )
        )

    async def _execute_task(self, task: Task) -> TaskResult:
        """Execute editing task."""
        draft = task.metadata.get("draft", {})
        content = draft.get("content", task.description)
        topic = draft.get("topic", "")
        writing_style = task.metadata.get("writing_style", "")

        self.logger.info(
            "Starting content editing",
            topic=topic,
            has_writing_style=bool(writing_style),
        )

        # Step 1: Get style reference from RAG
        style_result = await self.execute_skill(
            "rag_query",
            params={
                "query": topic,
                "collection": "style",
                "n_results": 2,
            },
        )
        rag_style_context = style_result.output if style_result.success else ""

        # Build style section
        style_section = ""
        if writing_style:
            style_section = f"""
ESTILO DE ESCRITA DO AUTOR (APLICAR RIGOROSAMENTE):
{writing_style}
"""
        if rag_style_context:
            style_section += f"""
REFERÊNCIAS DE ESTILO DA BASE DE CONHECIMENTO:
{rag_style_context}
"""

        # Step 2: Comprehensive edit
        edit_prompt = f"""Revise e melhore o seguinte artigo de blog:

CONTEÚDO ORIGINAL:
{content}
{style_section}
Por favor, faça uma revisão completa considerando:

1. ESTILO DE ESCRITA (PRIORIDADE MÁXIMA)
- Ajuste o tom e voz conforme o estilo definido
- Aplique o vocabulário preferido
- Siga a estrutura e formatação indicadas
- Remova termos listados para evitar

2. GRAMÁTICA E ORTOGRAFIA
- Corrija erros gramaticais
- Verifique concordância verbal e nominal
- Corrija ortografia

3. CLAREZA E FLUIDEZ
- Melhore transições entre parágrafos
- Simplifique frases complexas demais
- Garanta que cada parágrafo tenha um propósito claro

4. ESTRUTURA
- Verifique se headers estão bem posicionados
- Confirme se há boa proporção entre seções
- Garanta introdução envolvente e conclusão memorável

5. ENGAJAMENTO
- Adicione ganchos onde necessário
- Melhore call-to-actions
- Verifique se exemplos são claros e relevantes

Forneça:
1. O conteúdo revisado completo
2. Uma lista das principais alterações feitas
3. Sugestões adicionais (se houver)

CONTEÚDO REVISADO:"""

        # Use custom writing style if available
        if writing_style:
            system_prompt = f"""Você é um editor profissional que aplica RIGOROSAMENTE o estilo de escrita do autor.

{writing_style}

Seu objetivo é:
1. Garantir que o texto siga o estilo definido
2. Corrigir erros sem alterar a essência
3. Elevar a qualidade mantendo a voz do autor"""
        else:
            system_prompt = """Você é um editor profissional especializado em conteúdo que une espiritualidade
e negócios. Você tem olho afiado para:
- Erros gramaticais e de estilo
- Inconsistências de tom
- Problemas de fluidez
- Oportunidades de melhoria

Seu objetivo é elevar a qualidade do texto mantendo a voz original do autor."""

        edit_result = await self.execute_skill(
            "llm_call",
            params={
                "prompt": edit_prompt,
                "system_prompt": system_prompt,
                "max_tokens": 4096,
            },
        )

        if not edit_result.success:
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error=edit_result.error,
            )

        edited_content = {
            "content": edit_result.output,
            "original_content": content,
            "topic": topic,
            "word_count": len(edit_result.output.split()),
            "draft": draft,
        }

        return TaskResult(
            task_id=task.task_id,
            success=True,
            output=edited_content,
            metadata={"word_count": edited_content["word_count"]},
        )
