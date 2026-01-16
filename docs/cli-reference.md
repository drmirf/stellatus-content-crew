# Referência da CLI

Documentação completa dos comandos de linha de comando.

## Uso Geral

```bash
python -m src.cli.main [--debug] COMANDO [OPÇÕES] [ARGUMENTOS]
```

### Opção Global

| Opção | Descrição |
|-------|-----------|
| `--debug` | Ativa modo debug com logs detalhados |

---

## Comandos

### create

Cria novo conteúdo sobre um tópico.

```bash
python -m src.cli.main create TÓPICO [OPÇÕES]
```

**Argumentos:**
- `TÓPICO`: O tema do artigo (obrigatório)

**Opções:**

| Opção | Curto | Padrão | Descrição |
|-------|-------|--------|-----------|
| `--length` | `-l` | 1500 | Tamanho alvo em palavras |
| `--output` | `-o` | output/articles | Diretório de saída |
| `--format` | `-f` | md | Formato: md, json, both |
| `--context` | `-c` | - | Contexto/prompt detalhado inline |
| `--context-file` | `-cf` | - | Caminho para arquivo com contexto |
| `--notion` | - | False | Publicar no Notion |
| `--no-local` | - | False | Não salvar localmente |

**Exemplos:**

```bash
# Básico
python -m src.cli.main create "Intuição nos Negócios"

# Com contexto inline
python -m src.cli.main create "Meditação" -c "Foco em executivos"

# Com contexto de arquivo
python -m src.cli.main create "Liderança" --context-file prompts/lideranca.txt

# Com todas opções
python -m src.cli.main create "Mindfulness" \
  --length 2000 \
  --context "Técnicas práticas de 5 minutos" \
  --notion \
  --format both
```

---

### ingest

Ingere documentos no sistema RAG.

```bash
python -m src.cli.main ingest CAMINHO [OPÇÕES]
```

**Argumentos:**
- `CAMINHO`: Arquivo ou diretório a ingerir

**Opções:**

| Opção | Curto | Padrão | Descrição |
|-------|-------|--------|-----------|
| `--type` | `-t` | auto | Tipo: blog, pdf, auto |

**Exemplos:**

```bash
# Auto-detectar tipo
python -m src.cli.main ingest documento.pdf

# Especificar tipo
python -m src.cli.main ingest artigo.md --type blog
```

---

### ingest-batch

Ingere todos documentos de um diretório.

```bash
python -m src.cli.main ingest-batch DIRETÓRIO
```

**Exemplos:**

```bash
python -m src.cli.main ingest-batch data/knowledge_base/
```

---

### query

Consulta o sistema RAG.

```bash
python -m src.cli.main query CONSULTA [OPÇÕES]
```

**Opções:**

| Opção | Curto | Padrão | Descrição |
|-------|-------|--------|-----------|
| `--collection` | `-c` | both | Collection: style, knowledge, both |
| `--limit` | `-n` | 5 | Número de resultados |

**Exemplos:**

```bash
# Consulta geral
python -m src.cli.main query "meditação para líderes"

# Apenas referências de estilo
python -m src.cli.main query "meditação" -c style -n 3
```

---

### status

Mostra status do sistema.

```bash
python -m src.cli.main status
```

Exibe:
- Agentes registrados e suas skills
- Estatísticas do RAG
- Disponibilidade de embeddings

---

### notion-status

Verifica integração com Notion.

```bash
python -m src.cli.main notion-status
```

Exibe:
- Status da conexão
- Nome do database
- Propriedades configuradas

---

### list-content

Lista conteúdos gerados.

```bash
python -m src.cli.main list-content
```

Exibe:
- Nome do arquivo
- Data de modificação
- Tamanho
