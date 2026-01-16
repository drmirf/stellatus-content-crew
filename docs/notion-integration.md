# Integração Notion

Como configurar e usar a integração com Notion para publicação automática.

## Visão Geral

A integração permite publicar artigos diretamente no Notion como rascunhos, prontos para revisão e publicação.

## Configuração

### 1. Criar Integration no Notion

1. Acesse [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Clique em "New integration"
3. Configure:
   - Name: `Stellatus Content Crew` (ou outro nome)
   - Capabilities: Read, Update, Insert content
4. Copie o **Internal Integration Token**

### 2. Configurar Database

Crie um database no Notion com as seguintes propriedades:

| Propriedade | Tipo | Descrição |
|-------------|------|-----------|
| Title | title | Título do artigo |
| Slug | Text (rich_text) | URL slug |
| Description | Text (rich_text) | Descrição curta |
| Date | Date | Data de criação |
| Tags | Multi-select | Categorias/tags |
| Published | Checkbox | Status de publicação |

### 3. Compartilhar Database

1. Abra o database no Notion
2. Clique em **...** (três pontos) no canto superior direito
3. Vá em **Connections**
4. Adicione sua integration

### 4. Configurar Variáveis de Ambiente

Adicione ao `.env`:

```env
NOTION_TOKEN=ntn_d9871264931b5sRWyMKrHVveM40bhpzV4Sf6uxx4wxHeYY
NOTION_DATABASE_ID=2e924c5f8ca38088b24cfa7e516c7a97
```

**Nota**: O Database ID é a parte da URL após o workspace:
```
https://www.notion.so/workspace/2e924c5f8ca38088b24cfa7e516c7a97
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

## Uso

### Publicar Artigo

```bash
python -m src.cli.main create "Título do Artigo" --notion
```

### Apenas Notion (sem salvar local)

```bash
python -m src.cli.main create "Título do Artigo" --notion --no-local
```

### Verificar Conexão

```bash
python -m src.cli.main notion-status
```

## O que é Publicado

Quando você usa `--notion`, o sistema publica:

### Propriedades

| Campo | Conteúdo |
|-------|----------|
| Title | Título do artigo |
| Slug | URL-friendly do título |
| Description | Primeiros 160 caracteres ou meta description |
| Date | Data de criação |
| Tags | Keywords extraídas pelo SEO agent |
| Published | `true` (pronto para publicar no site) |

### Conteúdo

O corpo da página contém:
1. **Artigo principal** (otimizado para SEO)
2. **Toggle: SEO & Meta Tags** (informações SEO)
3. **Toggle: Prompts de Imagem** (para geração de imagens)
4. **Toggle: Sugestões Visuais** (recomendações de layout)
5. **Toggle: Revisão de Qualidade** (avaliação do conteúdo)

## Integração com Vercel

Se você usa Vercel para seu blog (como Next.js), configure o mesmo database:

1. Defina `NOTION_TOKEN` e `NOTION_DATABASE_ID` no Vercel
2. O blog lerá artigos onde `Published = true`
3. Use o `Slug` como URL do artigo

## Troubleshooting

### "Could not find database"

- Verifique se o database está compartilhado com a integration
- Confirme o Database ID no .env

### "Status is not a property"

- O database não tem a propriedade Status
- Remova ou adicione a propriedade conforme necessário

### "Invalid token"

- Verifique se o NOTION_TOKEN está correto
- Tokens começam com `ntn_`

### Artigos não aparecem no site

1. Verifique se `Published = true`
2. Confirme que o site está usando o mesmo database
3. Verifique as variáveis de ambiente do Vercel
