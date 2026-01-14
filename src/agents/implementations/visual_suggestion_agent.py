"""
Visual Suggestion Agent for layout and design recommendations.
"""

from __future__ import annotations

from src.agents.base.agent import BaseAgent
from src.core.registry import agent_registry
from src.interfaces.agent_interface import AgentCapability, Task, TaskResult
from src.skills.llm_call import LLMCallSkill


@agent_registry.register(name="visual_suggestion", category="content")
class VisualSuggestionAgent(BaseAgent):
    """
    Visual Suggestion Agent for layout and design recommendations.

    Capabilities:
    - Layout suggestions
    - Image placement recommendations
    - Color scheme suggestions
    - Visual hierarchy definition
    """

    name = "visual_suggestion"
    description = "Recommends visual layout and design elements"
    category = "content"

    def _setup(self) -> None:
        """Initialize agent with skills and capabilities."""
        super()._setup()

        self.add_skill(LLMCallSkill())

        self.add_capability(
            AgentCapability(
                name="visual_design",
                description="Suggest visual design elements",
                task_types=["visual", "layout", "design", "suggest"],
                required_skills=["llm_call"],
                priority=4,
            )
        )

    async def _execute_task(self, task: Task) -> TaskResult:
        """Execute visual suggestion task."""
        quality_result = task.metadata.get("quality", {})
        content = quality_result.get("content", task.description)
        topic = quality_result.get("topic", "")
        image_prompts = task.metadata.get("image_prompts", {})

        self.logger.info("Generating visual suggestions", topic=topic)

        prompt = f"""Analise o seguinte conteúdo e prompts de imagem para criar recomendações visuais completas:

CONTEÚDO DO ARTIGO:
{content[:2000]}...

PROMPTS DE IMAGEM GERADOS:
{image_prompts.get('prompts', 'Não disponível')}

TEMA: {topic}
NICHO: Misticismo + Gestão/Negócios

Forneça recomendações detalhadas para:

1. LAYOUT DO ARTIGO
- Estrutura visual recomendada
- Espaçamento entre seções
- Posicionamento de headers
- Uso de pull quotes ou destaques

2. POSICIONAMENTO DE IMAGENS
- Onde colocar cada imagem no texto
- Tamanho relativo (full-width, half, float)
- Alinhamento sugerido
- Captions recomendadas

3. ESQUEMA DE CORES
- Cor primária (para headers, links, CTAs)
- Cor secundária (acentos, destaques)
- Cores de fundo sugeridas
- Paleta que combine misticismo com profissionalismo
- Códigos HEX específicos

4. TIPOGRAFIA
- Estilo de fonte para títulos (serif/sans-serif)
- Estilo para corpo do texto
- Hierarquia de tamanhos (H1, H2, H3, parágrafo)
- Espaçamento entre linhas

5. ELEMENTOS VISUAIS ADICIONAIS
- Ícones sugeridos
- Divisores de seção
- Boxes de destaque (citações, dicas)
- Call-to-action styling

6. RESPONSIVIDADE
- Adaptações para mobile
- Comportamento de imagens em telas menores
- Prioridades de conteúdo para mobile

7. ACESSIBILIDADE
- Contraste de cores
- Tamanhos mínimos de fonte
- Alt text guidelines

FORMATO DE SAÍDA:
Organize as recomendações de forma clara e acionável, como um guia de estilo específico para este artigo."""

        system_prompt = """Você é um designer UX/UI especializado em blogs editoriais de alta qualidade.
Você entende como criar experiências visuais que:
- Facilitam a leitura e engajamento
- Transmitem profissionalismo e espiritualidade simultaneamente
- Funcionam bem em todas as plataformas
- São acessíveis e inclusivas

Suas recomendações são práticas e específicas, prontas para implementação."""

        visual_result = await self.execute_skill(
            "llm_call",
            params={
                "prompt": prompt,
                "system_prompt": system_prompt,
            },
        )

        if not visual_result.success:
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error=visual_result.error,
            )

        visual_suggestions = {
            "suggestions": visual_result.output,
            "topic": topic,
            "image_prompts": image_prompts,
            "quality": quality_result,
        }

        return TaskResult(
            task_id=task.task_id,
            success=True,
            output=visual_suggestions,
        )
