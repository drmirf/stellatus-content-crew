# Estilo de Escrita

Como configurar e usar o arquivo de estilo para personalizar a geração de conteúdo.

## Visão Geral

O arquivo `config/writing_style.md` define seu estilo de escrita pessoal. Todos os agentes (Writer, Editor) usam este arquivo para manter consistência.

## Localização

```
config/writing_style.md
```

## Como Preencher

### Tom e Voz

Define a personalidade da escrita.

```markdown
## Tom e Voz

- **Tom**: inspirador
- **Voz**: primeira pessoa (nós)
- **Abordagem**: storytelling com aplicações práticas
- **Energia**: calma mas provocativa
```

**Opções de Tom:**
- Conversacional
- Formal
- Inspirador
- Técnico
- Provocativo

**Opções de Voz:**
- Primeira pessoa singular (eu)
- Primeira pessoa plural (nós)
- Terceira pessoa

### Estrutura Preferida

Define como organizar os artigos.

```markdown
## Estrutura Preferida

### Introdução
- Gancho emocional ou história pessoal
- Apresentação do problema/oportunidade

### Desenvolvimento
- Exemplos práticos e casos reais
- Metáforas conectando misticismo e negócios
- 3-5 seções com subtópicos claros

### Conclusão
- Reflexão provocativa
- Call-to-action prático
```

### Vocabulário

Define palavras a usar e evitar.

```markdown
## Vocabulário

### Termos a Usar
- consciência
- presença
- intencionalidade
- sabedoria ancestral
- liderança consciente

### Termos a Evitar
- basicamente
- na verdade
- literalmente
- obviamente
- simplesmente

### Jargões Permitidos
- mindfulness (com moderação)
- propósito
- flow
```

### Formatação

Define preferências visuais.

```markdown
## Formatação

- **Tamanho de parágrafos**: curtos (2-3 frases)
- **Uso de listas**: moderado
- **Subtítulos**: a cada 3-4 parágrafos
- **Destaques**: negrito para conceitos-chave
```

### Público-Alvo

Define para quem você escreve.

```markdown
## Público-Alvo

- **Quem**: executivos e empreendedores
- **Nível**: intermediário a avançado
- **Contexto**: negócios + espiritualidade prática
- **Dor principal**: falta de propósito e clareza
- **Desejo principal**: liderança com significado
```

### Exemplos de Frases

Inclua frases reais suas para referência.

```markdown
## Exemplos de Frases no Meu Estilo

1. "A verdadeira liderança começa quando paramos de tentar controlar e começamos a confiar."
2. "Não existe separação entre o executivo na sala de reuniões e o ser humano que busca significado."
3. "Os antigos mestres sabiam algo que a ciência moderna está redescobrindo."
```

### O que NÃO Fazer

Liste anti-padrões.

```markdown
## O que NÃO Fazer

- Não usar linguagem excessivamente acadêmica
- Não fazer promessas exageradas ("transforme sua vida em 5 passos")
- Não usar clickbait
- Não ser condescendente com o leitor
- Não simplificar demais conceitos complexos
```

## Exemplo Completo

Veja um exemplo completo em `config/writing_style.md`.

## Como o Sistema Usa

1. **Pipeline**: Carrega o arquivo no início
2. **Writer Agent**: Usa como system prompt
3. **Editor Agent**: Aplica durante revisão
4. **Resultado**: Consistência de voz em todos os artigos

## Dicas

1. **Seja específico**: Quanto mais detalhado, melhor o resultado
2. **Use exemplos**: Frases reais ajudam muito
3. **Atualize regularmente**: Refine conforme aprende
4. **Teste**: Gere artigos e ajuste baseado nos resultados
