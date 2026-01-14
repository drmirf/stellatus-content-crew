"""
Image Prompt Agent for generating AI image prompts.
"""

from __future__ import annotations

from src.agents.base.agent import BaseAgent
from src.core.registry import agent_registry
from src.interfaces.agent_interface import AgentCapability, Task, TaskResult
from src.skills.llm_call import LLMCallSkill


@agent_registry.register(name="image_prompt", category="content")
class ImagePromptAgent(BaseAgent):
    """
    Image Prompt Agent for generating AI image prompts.

    Capabilities:
    - Featured image prompt generation
    - Inline image prompts
    - Thumbnail generation
    - Style consistency
    """

    name = "image_prompt"
    description = "Generates detailed prompts for AI image generation"
    category = "content"

    def _setup(self) -> None:
        """Initialize agent with skills and capabilities."""
        super()._setup()

        self.add_skill(LLMCallSkill())

        self.add_capability(
            AgentCapability(
                name="image_prompts",
                description="Generate image prompts",
                task_types=["image_prompt", "visual_prompt", "thumbnail"],
                required_skills=["llm_call"],
                priority=5,
            )
        )

    async def _execute_task(self, task: Task) -> TaskResult:
        """Execute image prompt generation task."""
        quality_result = task.metadata.get("quality", {})
        content = quality_result.get("content", task.description)
        topic = quality_result.get("topic", "")

        self.logger.info("Generating image prompts", topic=topic)

        prompt = f"""Analise o seguinte conteúdo de blog e crie prompts detalhados para geração de imagens com IA:

CONTEÚDO:
{content[:2000]}...

TEMA GERAL: {topic}
NICHO: Misticismo + Gestão/Negócios

Por favor, crie:

1. IMAGEM DESTACADA (Featured Image)
Prompt detalhado para a imagem principal do artigo:
- Estilo: Místico-profissional, elegante, inspirador
- Elementos visuais que combinem espiritualidade e business
- Cores sugeridas (tons que equilibrem mistério e profissionalismo)
- Composição e enquadramento
- Prompt em inglês otimizado para Midjourney/DALL-E

2. IMAGENS DE SEÇÃO (2-3 prompts)
Para ilustrar seções específicas do conteúdo:
- Identifique momentos-chave que se beneficiariam de imagem
- Crie prompts que complementem o texto
- Mantenha consistência visual com a imagem principal

3. THUMBNAIL PARA REDES SOCIAIS
Versão otimizada para miniatura:
- Foco em impacto visual imediato
- Texto overlay sugerido (se aplicável)
- Dimensões consideradas (1200x630 para OG, 1080x1080 para IG)

4. NEGATIVE PROMPTS
O que evitar em todas as imagens:
- Elementos que não combinam com o tema
- Estilos visuais inapropriados
- Clichês a evitar

FORMATO DE CADA PROMPT:
```
[TÍTULO DA IMAGEM]
Prompt: [prompt detalhado em inglês]
Estilo: [referência de estilo]
Aspect Ratio: [proporção recomendada]
Negative Prompt: [o que evitar]
```"""

        system_prompt = """Você é um especialista em arte digital e prompt engineering para IA generativa.
Você entende como criar prompts que resultam em imagens profissionais e evocativas que combinam
elementos místicos/espirituais com estética corporativa moderna. Suas imagens são:
- Elegantes e sofisticadas
- Espiritualmente inspiradoras sem serem kitsch
- Profissionais sem serem frias
- Únicas e memoráveis"""

        image_result = await self.execute_skill(
            "llm_call",
            params={
                "prompt": prompt,
                "system_prompt": system_prompt,
            },
        )

        if not image_result.success:
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error=image_result.error,
            )

        image_prompts = {
            "prompts": image_result.output,
            "topic": topic,
            "quality": quality_result,
        }

        return TaskResult(
            task_id=task.task_id,
            success=True,
            output=image_prompts,
        )
