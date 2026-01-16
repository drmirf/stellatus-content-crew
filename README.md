# Stellatus Content Crew

Sistema de criação de conteúdo com IA para o blog Stellatus - unindo misticismo e gestão de negócios.

## Visão Geral

O Stellatus Content Crew é um pipeline automatizado de criação de conteúdo que utiliza 7 agentes especializados de IA para produzir artigos de alta qualidade. O sistema integra:

- **RAG (Retrieval Augmented Generation)** para usar sua base de conhecimento como referência
- **Estilo de escrita personalizado** para manter consistência de voz
- **Integração com Notion** para publicação automática
- **Contexto expandido** para diretrizes detalhadas por artigo

## Instalação

```bash
# Clone o repositório
git clone <repo-url>
cd stellatus-content-crew

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Instale dependências
pip install -r requirements.txt
```

## Configuração

### 1. Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# LLM API Keys
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx  # Opcional, para embeddings

# Notion Integration (opcional)
NOTION_TOKEN=ntn_xxx
NOTION_DATABASE_ID=xxx

# RAG Configuration
RAG_EMBEDDING_PROVIDER=openai
RAG_VECTOR_STORE_PATH=./data/vector_store

# Content Settings
DEFAULT_CONTENT_LENGTH=1500
MIN_QUALITY_SCORE=75
```

### 2. Estilo de Escrita

Edite `config/writing_style.md` com suas preferências de estilo:

```bash
# Abra e preencha o arquivo
nano config/writing_style.md
```

O arquivo contém campos para:
- Tom e voz
- Estrutura preferida
- Vocabulário (termos a usar/evitar)
- Formatação
- Público-alvo

### 3. Base de Conhecimento

Ingira documentos na base de conhecimento:

```bash
# Ingerir PDFs
python -m src.cli.main ingest data/knowledge_base/

# Ingerir artigos de blog (para referência de estilo)
python -m src.cli.main ingest data/blog_references/ --type blog
```

## Uso

### Criar Artigo Básico

```bash
python -m src.cli.main create "Título do Artigo"
```

### Criar com Contexto Detalhado

```bash
# Contexto inline
python -m src.cli.main create "Meditação para Líderes" \
  --context "Foco em técnicas de 5 minutos para executivos ocupados. Tom prático e direto."

# Contexto de arquivo
python -m src.cli.main create "Meditação para Líderes" \
  --context-file prompts/meditacao.txt
```

### Publicar no Notion

```bash
python -m src.cli.main create "Título do Artigo" --notion
```

### Opções Disponíveis

| Opção | Descrição |
|-------|-----------|
| `--length`, `-l` | Tamanho alvo em palavras (padrão: 1500) |
| `--context`, `-c` | Contexto/prompt detalhado inline |
| `--context-file`, `-cf` | Arquivo com contexto detalhado |
| `--notion` | Publicar no Notion |
| `--no-local` | Não salvar localmente |
| `--format`, `-f` | Formato de saída (md/json/both) |

## Pipeline de Agentes

O sistema executa 7 agentes em sequência:

1. **Research Agent** - Pesquisa no RAG e web (RAG prioritário)
2. **Writer Agent** - Cria o rascunho seguindo estilo
3. **Editor Agent** - Revisa aplicando estilo
4. **SEO Agent** - Otimiza para buscadores
5. **Quality Reviewer** - Avalia qualidade
6. **Image Prompt Agent** - Gera prompts de imagem
7. **Visual Suggestion Agent** - Sugere layout visual

## Estrutura do Projeto

```
stellatus-content-crew/
├── config/
│   └── writing_style.md      # Seu estilo de escrita
├── data/
│   ├── knowledge_base/       # PDFs e documentos
│   ├── blog_references/      # Artigos de referência
│   └── vector_store/         # Base vetorial (ChromaDB)
├── output/
│   └── articles/             # Artigos gerados
├── src/
│   ├── agents/               # Agentes de IA
│   ├── cli/                  # Interface de linha de comando
│   ├── integrations/         # Notion, etc.
│   ├── orchestrator/         # Pipeline e orquestração
│   ├── rag/                  # Sistema RAG
│   └── skills/               # Habilidades dos agentes
└── docs/                     # Documentação detalhada
```

## Comandos CLI

```bash
# Criar conteúdo
python -m src.cli.main create "Tópico" [opções]

# Ingerir documentos no RAG
python -m src.cli.main ingest <caminho> [--type blog|pdf|auto]

# Consultar RAG
python -m src.cli.main query "Sua pergunta" [--collection style|knowledge|both]

# Ver status do sistema
python -m src.cli.main status

# Verificar integração Notion
python -m src.cli.main notion-status

# Listar conteúdos gerados
python -m src.cli.main list-content
```

## Documentação

Para documentação detalhada, consulte:

- [Guia de Início Rápido](docs/getting-started.md)
- [Referência da CLI](docs/cli-reference.md)
- [Configuração](docs/configuration.md)
- [Estilo de Escrita](docs/writing-style.md)
- [Sistema RAG](docs/rag-system.md)
- [Integração Notion](docs/notion-integration.md)
- [Agentes](docs/agents.md)
- [Arquitetura](docs/architecture.md)

## Licença

Projeto privado - Todos os direitos reservados.
