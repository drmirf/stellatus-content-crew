# Agentes

Documentação dos 7 agentes especializados do pipeline.

## Visão Geral

O pipeline executa 7 agentes em sequência, cada um com uma responsabilidade específica:

```
Research → Writer → Editor → SEO → Quality → Image → Visual
```

---

## 1. Research Agent

**Responsabilidade**: Pesquisa e coleta de informações.

### Entradas
- Tópico do artigo
- Contexto do usuário (opcional)

### Processo
1. **RAG Query** (prioridade)
   - Consulta base de conhecimento
   - Se ≥3 documentos, pula web search
2. **Web Search** (complementar)
   - Apenas se RAG insuficiente
3. **Síntese**
   - Combina fontes
   - Cria research brief

### Saídas
- Research brief
- Contexto RAG
- Fontes web (se consultadas)

---

## 2. Writer Agent

**Responsabilidade**: Criação do rascunho inicial.

### Entradas
- Research brief
- Contexto do usuário
- Estilo de escrita
- Tamanho alvo

### Processo
1. **Consulta estilo RAG**
   - Busca referências de estilo
2. **Cria outline**
   - Estrutura do artigo
3. **Escreve conteúdo**
   - Seguindo estilo definido
   - Usando base de conhecimento

### Saídas
- Rascunho completo
- Outline
- Word count

---

## 3. Editor Agent

**Responsabilidade**: Revisão e melhoria do conteúdo.

### Entradas
- Rascunho do Writer
- Estilo de escrita

### Processo
1. **Consulta estilo RAG**
2. **Revisão completa**:
   - Aplicação do estilo
   - Gramática e ortografia
   - Clareza e fluidez
   - Estrutura
   - Engajamento

### Saídas
- Conteúdo revisado
- Lista de alterações

---

## 4. SEO Agent

**Responsabilidade**: Otimização para buscadores.

### Entradas
- Conteúdo editado
- Tópico

### Processo
1. **Extração de keywords**
2. **Otimização**:
   - Meta título
   - Meta descrição
   - Headers otimizados
   - Densidade de keywords
3. **Formatação final**

### Saídas
- Conteúdo otimizado
- Keywords
- Meta tags

---

## 5. Quality Reviewer Agent

**Responsabilidade**: Avaliação final de qualidade.

### Entradas
- Conteúdo SEO-otimizado
- Score mínimo requerido

### Processo
1. **Consulta RAG** (referência)
2. **Avaliação**:
   - Qualidade geral
   - Coerência
   - Adequação ao público
   - Precisão
3. **Decisão de aprovação**

### Saídas
- Revisão de qualidade
- Score
- Aprovado (sim/não)

---

## 6. Image Prompt Agent

**Responsabilidade**: Geração de prompts para imagens.

### Entradas
- Conteúdo aprovado
- Tópico

### Processo
1. **Análise do conteúdo**
2. **Geração de prompts**:
   - Imagem principal
   - Imagens de seção
   - Thumbnails

### Saídas
- Prompts para geração de imagem
- Sugestões de estilo visual

---

## 7. Visual Suggestion Agent

**Responsabilidade**: Recomendações de layout e design.

### Entradas
- Conteúdo
- Prompts de imagem

### Processo
1. **Análise de estrutura**
2. **Sugestões**:
   - Layout geral
   - Posicionamento de imagens
   - Elementos visuais
   - Tipografia
   - Cores

### Saídas
- Sugestões visuais detalhadas
- Recomendações de layout

---

## Fluxo de Dados

```
┌──────────────┐
│   Research   │──→ research_brief
└──────────────┘          │
                          ▼
┌──────────────┐
│    Writer    │──→ draft
└──────────────┘          │
                          ▼
┌──────────────┐
│    Editor    │──→ edited_content
└──────────────┘          │
                          ▼
┌──────────────┐
│     SEO      │──→ seo_content + keywords
└──────────────┘          │
                          ▼
┌──────────────┐
│   Quality    │──→ review + approved
└──────────────┘          │
                          ▼
┌──────────────┐
│    Image     │──→ image_prompts
└──────────────┘          │
                          ▼
┌──────────────┐
│    Visual    │──→ visual_suggestions
└──────────────┘
```

## Extensão

Cada agente pode ser estendido ou substituído. Veja `src/agents/implementations/` para implementações.
