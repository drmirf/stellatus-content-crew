# Configuração

Guia completo de configuração do sistema.

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# ================================
# LLM API Keys (obrigatório)
# ================================
ANTHROPIC_API_KEY=sk-ant-api03-xxx

# OpenAI (opcional - usado para embeddings)
OPENAI_API_KEY=sk-xxx

# ================================
# RAG Configuration
# ================================
# Provider de embeddings: openai ou default
RAG_EMBEDDING_PROVIDER=openai

# Caminho para armazenamento vetorial
RAG_VECTOR_STORE_PATH=./data/vector_store

# ================================
# Content Settings
# ================================
# Tamanho padrão de artigos (palavras)
DEFAULT_CONTENT_LENGTH=1500

# Score mínimo de qualidade para aprovação (0-100)
MIN_QUALITY_SCORE=75

# ================================
# Notion Integration (opcional)
# ================================
NOTION_TOKEN=ntn_xxx
NOTION_DATABASE_ID=xxx

# ================================
# API Configuration (opcional)
# ================================
API_HOST=127.0.0.1
API_PORT=8000
API_KEY=your-secure-api-key

# ================================
# Logging
# ================================
LOG_LEVEL=INFO
DEBUG=false
```

## Arquivos de Configuração

### config/writing_style.md

Define seu estilo de escrita pessoal. Veja [writing-style.md](writing-style.md).

### Estrutura de Diretórios

```
stellatus-content-crew/
├── config/
│   └── writing_style.md      # Estilo de escrita
├── data/
│   ├── knowledge_base/       # PDFs para RAG
│   ├── blog_references/      # Artigos de referência
│   └── vector_store/         # ChromaDB (auto-gerado)
├── output/
│   └── articles/             # Artigos gerados
├── prompts/
│   └── agents/               # Prompts dos agentes
└── .env                      # Variáveis de ambiente
```

## Configurações por Ambiente

### Desenvolvimento

```env
LOG_LEVEL=DEBUG
DEBUG=true
```

### Produção

```env
LOG_LEVEL=INFO
DEBUG=false
```

## Notion Database

O database do Notion deve ter as seguintes propriedades:

| Propriedade | Tipo | Descrição |
|-------------|------|-----------|
| Title | title | Título do artigo |
| Slug | rich_text | URL slug |
| Description | rich_text | Descrição curta |
| Date | date | Data de publicação |
| Tags | multi_select | Categorias |
| Published | checkbox | Publicado? |

## Troubleshooting

### Variáveis não carregando

```bash
# Verifique se .env existe
cat .env

# Carregue manualmente
source .env && export ANTHROPIC_API_KEY
```

### ChromaDB não persiste

Verifique permissões no diretório:
```bash
chmod -R 755 data/vector_store/
```
