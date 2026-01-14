#!/usr/bin/env python3
"""
Content Crew CLI - AI-powered content creation for Mysticism & Business blog.
"""

import asyncio
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from src.core.config import get_settings
from src.orchestrator.content_pipeline import ContentPipeline
from src.rag.rag_service import RAGService
from src.storage.content_store import ContentStore
from src.utils.logger import configure_logging

console = Console()


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug mode")
def cli(debug: bool) -> None:
    """Stellatus Content Crew - AI-powered content creation."""
    log_level = "DEBUG" if debug else "INFO"
    configure_logging(log_level)


@cli.command()
@click.argument("topic")
@click.option("--length", "-l", default=1500, help="Target word count")
@click.option("--output", "-o", default="output/articles", help="Output directory")
@click.option("--format", "-f", type=click.Choice(["md", "json", "both"]), default="md")
@click.option("--notion", is_flag=True, help="Publish to Notion as draft")
@click.option("--no-local", is_flag=True, help="Don't save locally (use with --notion)")
def create(topic: str, length: int, output: str, format: str, notion: bool, no_local: bool) -> None:
    """Create new content on a topic."""
    console.print(Panel(f"[bold blue]Creating content about:[/] {topic}"))

    async def run_pipeline():
        pipeline = ContentPipeline()
        store = ContentStore(output)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running content pipeline...", total=None)

            result = await pipeline.create_content(
                topic=topic,
                target_length=length,
            )

            # Save locally unless --no-local is set
            if not no_local:
                progress.update(task, description="Saving content...")

                if format in ("md", "both"):
                    md_path = store.save(result)
                    console.print(f"[green]Markdown saved:[/] {md_path}")

                if format in ("json", "both"):
                    json_path = store.save_json(result)
                    console.print(f"[green]JSON saved:[/] {json_path}")

            # Publish to Notion if requested
            if notion:
                progress.update(task, description="Publishing to Notion...")
                try:
                    from src.integrations.notion import NotionPublisher

                    publisher = NotionPublisher()
                    publish_result = publisher.publish(result)

                    if publish_result.success:
                        console.print(f"[green]Published to Notion:[/] {publish_result.page_url}")
                    else:
                        console.print(f"[red]Notion publish failed:[/] {publish_result.error}")
                except Exception as e:
                    console.print(f"[red]Notion error:[/] {e}")

            return result

    result = asyncio.run(run_pipeline())

    # Show summary
    table = Table(title="Content Summary")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Topic", result.topic)
    table.add_row("Word Count", str(result.word_count))
    table.add_row("Approved", "[green]Yes[/]" if result.approved else "[yellow]No[/]")
    table.add_row("Keywords", ", ".join(result.keywords[:5]))

    console.print(table)


@cli.command()
@click.argument("path")
@click.option("--type", "-t", type=click.Choice(["blog", "pdf", "auto"]), default="auto")
def ingest(path: str, type: str) -> None:
    """Ingest documents into the RAG system."""
    path_obj = Path(path)

    if not path_obj.exists():
        console.print(f"[red]Error:[/] Path not found: {path}")
        return

    async def run_ingest():
        rag = RAGService()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Ingesting documents...", total=None)

            if path_obj.is_file():
                if type == "blog" or (type == "auto" and path_obj.suffix == ".md"):
                    count = await rag.ingest_blog_article(path_obj)
                elif type == "pdf" or (type == "auto" and path_obj.suffix == ".pdf"):
                    count = await rag.ingest_pdf(path_obj)
                else:
                    console.print(f"[yellow]Unknown file type:[/] {path_obj.suffix}")
                    return 0
            else:
                count = await rag.ingest_directory(path_obj, type)

            progress.update(task, description="Done!")
            return count

    count = asyncio.run(run_ingest())
    console.print(f"[green]Ingested {count} document chunks[/]")


@cli.command()
@click.argument("directory")
def ingest_batch(directory: str) -> None:
    """Batch ingest all documents in a directory."""
    dir_path = Path(directory)

    if not dir_path.exists():
        console.print(f"[red]Error:[/] Directory not found: {directory}")
        return

    async def run_batch():
        rag = RAGService()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Processing directory...", total=None)
            count = await rag.ingest_directory(dir_path)
            progress.update(task, description="Done!")
            return count

    count = asyncio.run(run_batch())
    console.print(f"[green]Ingested {count} document chunks from {directory}[/]")


@cli.command()
@click.argument("query")
@click.option("--collection", "-c", type=click.Choice(["style", "knowledge", "both"]), default="both")
@click.option("--limit", "-n", default=5, help="Number of results")
def query(query: str, collection: str, limit: int) -> None:
    """Query the RAG system."""
    async def run_query():
        rag = RAGService()

        if collection == "style":
            result = await rag.retriever.retrieve_style_references(query, limit)
        elif collection == "knowledge":
            result = await rag.retriever.retrieve_knowledge(query, limit)
        else:
            result = await rag.query(query, n_results=limit)

        return result

    result = asyncio.run(run_query())

    console.print(Panel(f"[bold]Query:[/] {query}\n[bold]Collection:[/] {collection}"))

    for i, doc in enumerate(result.documents, 1):
        score = result.scores[i - 1] if i <= len(result.scores) else 0
        console.print(f"\n[cyan]Result {i}[/] (score: {score:.3f})")
        console.print(f"Source: {doc.metadata.get('source', 'Unknown')}")
        console.print(doc.content[:300] + "..." if len(doc.content) > 300 else doc.content)


@cli.command()
def status() -> None:
    """Show system status."""
    from src.orchestrator.orchestrator import Orchestrator

    async def get_status():
        orchestrator = Orchestrator()
        await orchestrator.initialize()

        rag = RAGService()

        return {
            "orchestrator": orchestrator.get_status(),
            "rag": rag.get_stats(),
        }

    status_data = asyncio.run(get_status())

    console.print(Panel("[bold blue]Stellatus Content Crew Status[/]"))

    # Agents table
    agents_table = Table(title="Registered Agents")
    agents_table.add_column("Name", style="cyan")
    agents_table.add_column("Category", style="green")
    agents_table.add_column("Skills", style="white")

    for name, info in status_data["orchestrator"]["agents"].items():
        agents_table.add_row(
            name,
            info["category"],
            ", ".join(info["skills"]),
        )

    console.print(agents_table)

    # RAG stats
    rag_table = Table(title="RAG System")
    rag_table.add_column("Metric", style="cyan")
    rag_table.add_column("Value", style="white")

    rag = status_data["rag"]
    rag_table.add_row("Collections", ", ".join(rag["collections"]) or "None")
    rag_table.add_row("Style Documents", str(rag["style_documents"]))
    rag_table.add_row("Knowledge Documents", str(rag["knowledge_documents"]))
    rag_table.add_row("Embeddings Available", "[green]Yes[/]" if rag["embeddings_available"] else "[red]No[/]")

    console.print(rag_table)


@cli.command()
def list_content() -> None:
    """List all generated content."""
    store = ContentStore()
    content_list = store.list_content()

    if not content_list:
        console.print("[yellow]No content found[/]")
        return

    table = Table(title="Generated Content")
    table.add_column("Filename", style="cyan")
    table.add_column("Modified", style="green")
    table.add_column("Size", style="white")

    for item in content_list:
        table.add_row(
            item["filename"],
            item["modified"][:19],
            f"{item['size']} bytes",
        )

    console.print(table)


@cli.command("notion-status")
def notion_status() -> None:
    """Check Notion integration status."""
    console.print(Panel("[bold blue]Notion Integration Status[/]"))

    try:
        from src.integrations.notion import NotionPublisher

        publisher = NotionPublisher()

        if publisher.test_connection():
            console.print("[green]Connection successful![/]")

            # Get database info
            db = publisher.client.get_database(publisher.database_id)
            if db:
                db_title = db.get("title", [{}])[0].get("plain_text", "Unknown")
                console.print(f"Database: {db_title}")
                console.print(f"Database ID: {publisher.database_id}")

                # Show properties
                props = db.get("properties", {})
                table = Table(title="Database Properties")
                table.add_column("Property", style="cyan")
                table.add_column("Type", style="green")

                for name, prop in props.items():
                    table.add_row(name, prop.get("type", "unknown"))

                console.print(table)
        else:
            console.print("[red]Connection failed![/]")
            console.print("Check your NOTION_TOKEN and NOTION_DATABASE_ID")

    except ValueError as e:
        console.print(f"[red]Configuration error:[/] {e}")
        console.print("\nMake sure you have set:")
        console.print("  - NOTION_TOKEN")
        console.print("  - NOTION_DATABASE_ID")
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")


if __name__ == "__main__":
    cli()
