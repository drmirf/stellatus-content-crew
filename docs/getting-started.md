# Guia de Início Rápido

Comece a criar artigos em 5 minutos.

## Pré-requisitos

- Python 3.10+
- Chave de API Anthropic (Claude)
- Chave de API OpenAI (opcional, para embeddings)

## Instalação Rápida

```bash
# 1. Clone e entre no diretório
git clone <repo-url>
cd stellatus-content-crew

# 2. Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate

# 3. Instale dependências
pip install -r requirements.txt

# 4. Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas chaves de API
```

## Seu Primeiro Artigo

```bash
python -m src.cli.main create "O Poder da Intuição nos Negócios"
```

O sistema irá:
1. Pesquisar sobre o tema (RAG + web)
2. Criar um rascunho
3. Editar e revisar
4. Otimizar para SEO
5. Avaliar qualidade
6. Gerar prompts de imagem
7. Sugerir layout visual

O artigo será salvo em `output/articles/`.

## Com Contexto Personalizado

```bash
python -m src.cli.main create "Meditação para Executivos" \
  --context "Foque em técnicas de 5 minutos que podem ser praticadas no escritório. Tom prático e direto, sem jargões espirituais pesados."
```

## Próximos Passos

1. **Configure seu estilo**: Edite `config/writing_style.md`
2. **Alimente o RAG**: Ingira documentos em `data/knowledge_base/`
3. **Configure Notion**: Veja [notion-integration.md](notion-integration.md)

## Problemas Comuns

### Erro de API Key

```
Error: ANTHROPIC_API_KEY not set
```

Solução: Verifique se o arquivo `.env` está configurado e execute:
```bash
source .env && export ANTHROPIC_API_KEY
```

### RAG não encontra documentos

Se o RAG não retorna resultados relevantes:

```bash
# Verifique status
python -m src.cli.main status

# Ingira documentos
python -m src.cli.main ingest-batch data/knowledge_base/
```
