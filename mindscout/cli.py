"""Command-line interface for Mind Scout."""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from datetime import datetime

from mindscout.database import init_db, get_session, Article
from mindscout.fetchers.arxiv import fetch_arxiv
from mindscout.config import DEFAULT_CATEGORIES

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Mind Scout - Your AI research assistant.

    Stay on top of advances in AI with personalized recommendations.
    """
    # Ensure database is initialized
    init_db()


@main.command()
@click.option(
    "--categories",
    "-c",
    multiple=True,
    help="arXiv categories to fetch (e.g., cs.AI, cs.LG)",
)
def fetch(categories):
    """Fetch new articles from arXiv."""
    if not categories:
        categories = DEFAULT_CATEGORIES

    console.print(f"[bold blue]Fetching articles from categories:[/bold blue] {', '.join(categories)}")

    try:
        new_count = fetch_arxiv(list(categories))
        if new_count > 0:
            console.print(f"[bold green]✓[/bold green] Added {new_count} new articles")
        else:
            console.print("[yellow]No new articles found[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@main.command()
@click.option("--unread", "-u", is_flag=True, help="Show only unread articles")
@click.option("--limit", "-n", default=10, help="Number of articles to show")
@click.option("--source", "-s", help="Filter by source (e.g., arxiv)")
def list(unread, limit, source):
    """List articles in the database."""
    session = get_session()

    try:
        query = session.query(Article)

        if unread:
            query = query.filter_by(is_read=False)

        if source:
            query = query.filter_by(source=source)

        # Order by fetched date descending
        query = query.order_by(Article.fetched_date.desc())
        articles = query.limit(limit).all()

        if not articles:
            console.print("[yellow]No articles found[/yellow]")
            return

        table = Table(title=f"Articles ({len(articles)} shown)", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim", width=6)
        table.add_column("Title", style="bold", min_width=40)
        table.add_column("Source", width=10)
        table.add_column("Date", width=12)
        table.add_column("Read", width=6, justify="center")

        for article in articles:
            date_str = article.published_date.strftime("%Y-%m-%d") if article.published_date else "N/A"
            read_status = "✓" if article.is_read else "○"
            read_color = "green" if article.is_read else "yellow"

            table.add_row(
                str(article.id),
                article.title[:80],
                article.source,
                date_str,
                f"[{read_color}]{read_status}[/{read_color}]",
            )

        console.print(table)

    finally:
        session.close()


@main.command()
@click.argument("article_id", type=int)
def show(article_id):
    """Show details of a specific article."""
    session = get_session()

    try:
        article = session.query(Article).filter_by(id=article_id).first()

        if not article:
            console.print(f"[bold red]Article {article_id} not found[/bold red]")
            return

        # Create a rich panel with article details
        content = []
        content.append(f"[bold cyan]Title:[/bold cyan] {article.title}")
        content.append(f"[bold cyan]Authors:[/bold cyan] {article.authors or 'N/A'}")
        content.append(f"[bold cyan]Source:[/bold cyan] {article.source} ({article.source_id})")

        if article.published_date:
            content.append(f"[bold cyan]Published:[/bold cyan] {article.published_date.strftime('%Y-%m-%d')}")

        content.append(f"[bold cyan]URL:[/bold cyan] {article.url}")
        content.append(f"[bold cyan]Categories:[/bold cyan] {article.categories or 'N/A'}")

        read_status = "[green]Read[/green]" if article.is_read else "[yellow]Unread[/yellow]"
        content.append(f"[bold cyan]Status:[/bold cyan] {read_status}")

        content.append("\n[bold cyan]Abstract:[/bold cyan]")
        content.append(article.abstract or "No abstract available")

        panel = Panel("\n".join(content), title=f"Article {article_id}", border_style="blue")
        console.print(panel)

    finally:
        session.close()


@main.command()
@click.argument("article_id", type=int)
def read(article_id):
    """Mark an article as read."""
    session = get_session()

    try:
        article = session.query(Article).filter_by(id=article_id).first()

        if not article:
            console.print(f"[bold red]Article {article_id} not found[/bold red]")
            return

        article.is_read = True
        session.commit()
        console.print(f"[bold green]✓[/bold green] Marked article {article_id} as read")

    finally:
        session.close()


@main.command()
@click.argument("article_id", type=int)
def unread(article_id):
    """Mark an article as unread."""
    session = get_session()

    try:
        article = session.query(Article).filter_by(id=article_id).first()

        if not article:
            console.print(f"[bold red]Article {article_id} not found[/bold red]")
            return

        article.is_read = False
        session.commit()
        console.print(f"[bold green]✓[/bold green] Marked article {article_id} as unread")

    finally:
        session.close()


@main.command()
def stats():
    """Show statistics about your article collection."""
    session = get_session()

    try:
        total = session.query(Article).count()
        unread = session.query(Article).filter_by(is_read=False).count()
        read = session.query(Article).filter_by(is_read=True).count()

        # Count by source
        sources = {}
        for article in session.query(Article).all():
            sources[article.source] = sources.get(article.source, 0) + 1

        table = Table(title="Mind Scout Statistics", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right")

        table.add_row("Total Articles", str(total))
        table.add_row("Unread", f"[yellow]{unread}[/yellow]")
        table.add_row("Read", f"[green]{read}[/green]")
        table.add_row("", "")

        for source, count in sources.items():
            table.add_row(f"{source.capitalize()} Articles", str(count))

        console.print(table)

    finally:
        session.close()


@main.command()
@click.option("--limit", "-n", type=int, help="Maximum number of articles to process")
@click.option("--force", "-f", is_flag=True, help="Reprocess already processed articles")
def process(limit, force):
    """Process articles with LLM (summarization and topic extraction)."""
    from mindscout.processors.content import ContentProcessor

    try:
        processor = ContentProcessor()

        if limit:
            console.print(f"[bold blue]Processing up to {limit} articles...[/bold blue]")
        else:
            console.print("[bold blue]Processing all unprocessed articles...[/bold blue]")

        if force:
            console.print("[yellow]Force mode: reprocessing already processed articles[/yellow]")

        processed, failed = processor.process_batch(limit=limit, force=force)

        if processed > 0:
            console.print(f"[bold green]✓[/bold green] Processed {processed} articles")
        if failed > 0:
            console.print(f"[bold red]✗[/bold red] Failed to process {failed} articles")
        if processed == 0 and failed == 0:
            console.print("[yellow]No articles to process[/yellow]")

    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        console.print("\n[yellow]Tip:[/yellow] Set ANTHROPIC_API_KEY environment variable:")
        console.print("  export ANTHROPIC_API_KEY='your-api-key-here'")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@main.command()
def topics():
    """Show all discovered topics from processed articles."""
    from mindscout.processors.content import ContentProcessor

    processor = ContentProcessor(lazy_init=True)
    stats = processor.get_processing_stats()

    if not stats["top_topics"]:
        console.print("[yellow]No topics found. Process some articles first with 'mindscout process'[/yellow]")
        return

    table = Table(title="Top Topics", show_header=True, header_style="bold cyan")
    table.add_column("Topic", style="bold")
    table.add_column("Count", justify="right")

    for topic, count in stats["top_topics"]:
        table.add_row(topic, str(count))

    console.print(table)
    console.print(f"\n[dim]Total unique topics: {len(stats['top_topics'])}[/dim]")


@main.command()
@click.argument("topic")
@click.option("--limit", "-n", default=10, help="Number of articles to show")
def find_by_topic(topic, limit):
    """Find articles by topic."""
    from mindscout.processors.content import ContentProcessor

    processor = ContentProcessor(lazy_init=True)
    articles = processor.get_articles_by_topic(topic, limit=limit)

    if not articles:
        console.print(f"[yellow]No articles found with topic matching '{topic}'[/yellow]")
        console.print("[dim]Make sure articles are processed first with 'mindscout process'[/dim]")
        return

    table = Table(
        title=f"Articles matching '{topic}' ({len(articles)} found)",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("ID", style="dim", width=6)
    table.add_column("Title", style="bold", min_width=40)
    table.add_column("Topics", width=30)

    for article in articles:
        import json
        topics_list = json.loads(article.topics) if article.topics else []
        topics_str = ", ".join(topics_list[:3])
        if len(topics_list) > 3:
            topics_str += "..."

        table.add_row(str(article.id), article.title[:80], topics_str)

    console.print(table)


@main.command()
def processing_stats():
    """Show processing statistics."""
    from mindscout.processors.content import ContentProcessor

    processor = ContentProcessor(lazy_init=True)
    stats = processor.get_processing_stats()

    table = Table(title="Processing Statistics", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Total Articles", str(stats["total_articles"]))
    table.add_row("Processed", f"[green]{stats['processed']}[/green]")
    table.add_row("Unprocessed", f"[yellow]{stats['unprocessed']}[/yellow]")
    table.add_row(
        "Processing Rate", f"{stats['processing_rate']:.1f}%"
    )

    console.print(table)


if __name__ == "__main__":
    main()
