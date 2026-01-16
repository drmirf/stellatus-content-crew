# Sistema RAG

Documentação do sistema de Retrieval Augmented Generation.

## O que é RAG?

RAG (Retrieval Augmented Generation) permite que a IA use seus documentos como referência ao gerar conteúdo. Isso resulta em artigos mais precisos e alinhados com sua base de conhecimento.

## Arquitetura

```
                    ┌─────────────────┐
                    │   Documentos    │
                    │  (PDFs, MDs)    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    Ingestion    │
                    │  (Chunking +    │
                    │   Embedding)    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   ChromaDB      │
                    │ (Vector Store)  │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
   ┌───────▼───────┐ ┌───────▼───────┐ ┌───────▼───────┐
   │    Style      │ │   Knowledge   │ │   Combined    │
   │  Collection   │ │  Collection   │ │    Query      │
   └───────────────┘ └───────────────┘ └───────────────┘
```

## Collections

### Style Collection

Armazena artigos de blog para referência de estilo.

```bash
# Ingerir artigos de referência
python -m src.cli.main ingest data/blog_references/ --type blog
```

**Uso**: Writer e Editor agents consultam para manter consistência de estilo.

### Knowledge Collection

Armazena PDFs e documentos técnicos.

```bash
# Ingerir PDFs
python -m src.cli.main ingest data/knowledge_base/ --type pdf
```

**Uso**: Research agent consulta para embasar conteúdo.

## Comandos

### Ingerir Documento Individual

```bash
# PDF
python -m src.cli.main ingest documento.pdf

# Markdown (blog)
python -m src.cli.main ingest artigo.md --type blog
```

### Ingerir Diretório

```bash
python -m src.cli.main ingest-batch data/knowledge_base/
```

### Consultar RAG

```bash
# Consulta geral (ambas collections)
python -m src.cli.main query "meditação para líderes"

# Apenas estilo
python -m src.cli.main query "meditação" --collection style

# Apenas conhecimento
python -m src.cli.main query "meditação" --collection knowledge
```

### Ver Estatísticas

```bash
python -m src.cli.main status
```

## Estrutura de Diretórios

```
data/
├── knowledge_base/           # PDFs e documentos técnicos
│   ├── livro1.pdf
│   ├── pesquisa.pdf
│   └── ...
├── blog_references/          # Artigos para referência de estilo
│   ├── artigo1.md
│   ├── artigo2.md
│   └── ...
└── vector_store/             # ChromaDB (auto-gerado)
    └── chroma.sqlite3
```

## Como Funciona no Pipeline

1. **Research Agent**:
   - Consulta ambas collections
   - Prioriza RAG sobre web search
   - Se RAG tem ≥3 documentos, pula web search

2. **Writer Agent**:
   - Consulta style collection
   - Usa como referência de tom e estrutura

3. **Editor Agent**:
   - Consulta style collection
   - Aplica durante revisão

## Boas Práticas

### Documentos de Qualidade

- Use PDFs bem formatados
- Artigos de blog devem ser exemplos do estilo desejado
- Evite documentos muito longos (serão divididos em chunks)

### Organização

```
knowledge_base/
├── livros/
├── artigos_cientificos/
└── pesquisas/

blog_references/
├── melhores_artigos/
└── exemplos_estilo/
```

### Manutenção

```bash
# Verificar documentos indexados
python -m src.cli.main status

# Re-indexar (delete vector_store e ingira novamente)
rm -rf data/vector_store/
python -m src.cli.main ingest-batch data/knowledge_base/
```

## Embeddings

### OpenAI (Recomendado)

```env
RAG_EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-xxx
```

### Default (Fallback)

Se não houver API key OpenAI, usa embeddings default do ChromaDB.

```env
RAG_EMBEDDING_PROVIDER=default
```

## Troubleshooting

### RAG não retorna resultados

1. Verifique se documentos foram ingeridos
2. Confirme que embeddings estão disponíveis
3. Teste com query mais específica

### Resultados irrelevantes

1. Melhore a qualidade dos documentos fonte
2. Use consultas mais específicas
3. Aumente `n_results` para mais contexto
