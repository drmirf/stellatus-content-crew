# Arquitetura

Visão técnica da arquitetura do sistema.

## Diagrama Geral

```
┌─────────────────────────────────────────────────────────────────┐
│                           CLI                                    │
│                    (src/cli/main.py)                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Content Pipeline                              │
│              (src/orchestrator/content_pipeline.py)             │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                     Pipeline Context                       │  │
│  │  • topic           • user_context                         │  │
│  │  • target_length   • writing_style                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Orchestrator                               │
│                (src/orchestrator/orchestrator.py)               │
│                                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │   Registry   │ │  Event Bus   │ │    Tasks     │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    Agent     │     │    Agent     │     │    Agent     │
│  (Research)  │     │   (Writer)   │     │   (Editor)   │
│              │     │              │     │              │
│  ┌────────┐  │     │  ┌────────┐  │     │  ┌────────┐  │
│  │ Skills │  │     │  │ Skills │  │     │  │ Skills │  │
│  └────────┘  │     │  └────────┘  │     │  └────────┘  │
└──────────────┘     └──────────────┘     └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Skills Layer                             │
│                                                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │ LLM Call   │  │ RAG Query  │  │ Web Search │                │
│  └────────────┘  └────────────┘  └────────────┘                │
└─────────────────────────────────────────────────────────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Anthropic  │     │    ChromaDB  │     │ DuckDuckGo   │
│     API      │     │              │     │     API      │
└──────────────┘     └──────────────┘     └──────────────┘
```

## Componentes

### CLI (`src/cli/`)

Interface de linha de comando usando Click.

- `main.py`: Comandos principais
- Processa argumentos e opções
- Chama ContentPipeline

### Orchestrator (`src/orchestrator/`)

Gerencia execução do pipeline e agentes.

- `content_pipeline.py`: Pipeline de 7 estágios
- `orchestrator.py`: Registro e execução de agentes

### Agents (`src/agents/`)

Agentes especializados de IA.

```
agents/
├── base/
│   └── agent.py          # Classe base
└── implementations/
    ├── research_agent.py
    ├── writer_agent.py
    ├── editor_agent.py
    ├── seo_agent.py
    ├── quality_reviewer_agent.py
    ├── image_prompt_agent.py
    └── visual_suggestion_agent.py
```

### Skills (`src/skills/`)

Habilidades reutilizáveis dos agentes.

- `llm_call.py`: Chamadas ao Claude
- `rag_query.py`: Consultas ao RAG
- `web_search.py`: Busca na web

### RAG (`src/rag/`)

Sistema de Retrieval Augmented Generation.

```
rag/
├── rag_service.py        # Serviço principal
├── retrieval/
│   └── retriever.py      # Recuperação de documentos
├── vector_store/
│   └── chroma_store.py   # Armazenamento ChromaDB
├── embeddings/
│   └── openai_embeddings.py
└── ingestion/
    ├── blog_processor.py
    └── pdf_processor.py
```

### Integrations (`src/integrations/`)

Integrações externas.

```
integrations/
└── notion/
    ├── client.py         # Cliente Notion API
    └── publisher.py      # Publicação de artigos
```

## Fluxo de Execução

```python
# 1. CLI recebe comando
cli.create("Tópico", context="...", notion=True)

# 2. Pipeline inicializa
pipeline = ContentPipeline()

# 3. Carrega configurações
writing_style = load("config/writing_style.md")
pipeline_context = {
    "topic": topic,
    "user_context": context,
    "writing_style": writing_style,
}

# 4. Executa 7 estágios
for stage in [research, writer, editor, seo, quality, image, visual]:
    result = await orchestrator.execute_task(stage, task)
    pipeline_context[stage] = result

# 5. Compila resultado
content_result = ContentResult(...)

# 6. Publica (opcional)
if notion:
    publisher.publish(content_result)
```

## Interfaces

### Task

```python
@dataclass
class Task:
    description: str
    task_type: str
    metadata: dict[str, Any]
    priority: TaskPriority
    status: TaskStatus
```

### TaskResult

```python
@dataclass
class TaskResult:
    task_id: str
    success: bool
    output: Any
    error: str | None
    metadata: dict[str, Any]
```

## Eventos

O sistema usa event bus para comunicação:

```python
EventType.PIPELINE_STARTED
EventType.PIPELINE_STAGE_STARTED
EventType.PIPELINE_STAGE_COMPLETED
EventType.PIPELINE_COMPLETED
EventType.PIPELINE_FAILED
```

## Extensibilidade

### Adicionar Novo Agente

```python
# src/agents/implementations/my_agent.py
@agent_registry.register(name="my_agent", category="content")
class MyAgent(BaseAgent):
    async def _execute_task(self, task: Task) -> TaskResult:
        # Implementação
        pass
```

### Adicionar Nova Skill

```python
# src/skills/my_skill.py
class MySkill(BaseSkill):
    name = "my_skill"

    async def execute(self, params: dict) -> SkillResult:
        # Implementação
        pass
```

### Adicionar Ao Pipeline

```python
# src/orchestrator/content_pipeline.py
async def create_content(...):
    # ...
    my_result = await self._execute_stage(
        "my_agent",
        Task(description=..., task_type="my_type", metadata=...)
    )
```
