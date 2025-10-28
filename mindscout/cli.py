"""Command-line interface for Mind Scout using argparse."""

import argparse
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from mindscout.database import init_db, get_session, Article
from mindscout.fetchers.arxiv import fetch_arxiv
from mindscout.config import DEFAULT_CATEGORIES

console = Console()


def cmd_fetch(args):
    """Fetch new articles from arXiv."""
    categories = args.categories if args.categories else DEFAULT_CATEGORIES

    console.print(f"[bold blue]Fetching articles from categories:[/bold blue] {', '.join(categories)}")

    try:
        new_count = fetch_arxiv(list(categories))
        if new_count > 0:
            console.print(f"[bold green]✓[/bold green] Added {new_count} new articles")
        else:
            console.print("[yellow]No new articles found[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


def cmd_search(args):
    """Search and fetch articles from arXiv with advanced filters."""
    from mindscout.fetchers.arxiv_advanced import ArxivAdvancedFetcher
    from datetime import datetime, timedelta

    fetcher = ArxivAdvancedFetcher()

    # Parse date arguments
    from_date = None
    to_date = None

    if args.last_days:
        to_date = datetime.now()
        from_date = to_date - timedelta(days=args.last_days)
    elif args.from_date:
        from_date = datetime.strptime(args.from_date, "%Y-%m-%d")
    elif args.to_date:
        to_date = datetime.strptime(args.to_date, "%Y-%m-%d")

    # Build description
    desc_parts = []
    if args.keywords:
        desc_parts.append(f"keywords: '{args.keywords}'")
    if args.categories:
        desc_parts.append(f"categories: {', '.join(args.categories)}")
    if args.author:
        desc_parts.append(f"author: '{args.author}'")
    if args.title:
        desc_parts.append(f"title: '{args.title}'")
    if from_date:
        desc_parts.append(f"from: {from_date.strftime('%Y-%m-%d')}")
    if to_date:
        desc_parts.append(f"to: {to_date.strftime('%Y-%m-%d')}")

    console.print(f"[bold blue]Searching arXiv with:[/bold blue] {', '.join(desc_parts)}")
    console.print(f"[dim]Max results: {args.max_results}, Sort by: {args.sort_by}[/dim]")

    try:
        new_count = fetcher.fetch_and_store(
            keywords=args.keywords,
            categories=args.categories,
            author=args.author,
            title=args.title,
            from_date=from_date,
            to_date=to_date,
            max_results=args.max_results,
            sort_by=args.sort_by,
            sort_order=args.sort_order,
        )

        if new_count > 0:
            console.print(f"[bold green]✓[/bold green] Added {new_count} new articles")
        else:
            console.print("[yellow]No new articles found (all already in database)[/yellow]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")


def cmd_fetch_semantic_scholar(args):
    """Fetch papers from Semantic Scholar with citation data."""
    from mindscout.fetchers.semanticscholar import SemanticScholarFetcher

    fetcher = SemanticScholarFetcher()

    # Build description
    desc_parts = [f"query: '{args.query}'"]
    if args.year:
        desc_parts.append(f"year: {args.year}")
    if args.min_citations:
        desc_parts.append(f"min citations: {args.min_citations}")

    console.print(f"[bold blue]Searching Semantic Scholar:[/bold blue] {', '.join(desc_parts)}")
    console.print(f"[dim]Max results: {args.max_results}, Sort: {args.sort}[/dim]")

    try:
        new_count = fetcher.fetch_and_store(
            query=args.query,
            limit=args.max_results,
            sort=args.sort,
            year=args.year,
            min_citations=args.min_citations,
        )

        if new_count > 0:
            console.print(f"[bold green]✓[/bold green] Added {new_count} new articles with citation data")
        else:
            console.print("[yellow]No new articles found (all already in database)[/yellow]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")


def cmd_list(args):
    """List articles in the database."""
    session = get_session()

    try:
        query = session.query(Article)

        if args.unread:
            query = query.filter_by(is_read=False)

        if args.source:
            query = query.filter_by(source=args.source)

        query = query.order_by(Article.fetched_date.desc())
        articles = query.limit(args.limit).all()

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


def cmd_show(args):
    """Show details of a specific article."""
    session = get_session()

    try:
        article = session.query(Article).filter_by(id=args.article_id).first()

        if not article:
            console.print(f"[bold red]Article {args.article_id} not found[/bold red]")
            return

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

        # Show citation data if available (Phase 3)
        if article.citation_count is not None:
            content.append(f"\n[bold cyan]Citations:[/bold cyan] {article.citation_count}")
            if article.influential_citations is not None:
                content.append(f"[bold cyan]Influential Citations:[/bold cyan] {article.influential_citations}")

        # Show implementation links if available (Phase 3)
        if article.github_url:
            content.append(f"[bold cyan]GitHub:[/bold cyan] {article.github_url}")
        if article.paper_url_pwc:
            content.append(f"[bold cyan]Papers with Code:[/bold cyan] {article.paper_url_pwc}")

        # Show Hugging Face data if available (Phase 3)
        if article.hf_upvotes is not None:
            content.append(f"[bold cyan]HF Upvotes:[/bold cyan] {article.hf_upvotes}")

        # TODO: Remove or uncomment depending on whether abstract summarization is needed in the future
        # Show summary if processed
        # if article.processed and article.summary:
        #     content.append("\n[bold cyan]Summary:[/bold cyan]")
        #     content.append(article.summary)

        # Show topics if processed
        if article.processed and article.topics:
            import json
            try:
                topics = json.loads(article.topics)
                content.append(f"\n[bold cyan]Topics:[/bold cyan] {', '.join(topics)}")
            except json.JSONDecodeError:
                pass

        content.append("\n[bold cyan]Abstract:[/bold cyan]")
        content.append(article.abstract or "No abstract available")

        panel = Panel("\n".join(content), title=f"Article {article.id}", border_style="blue")
        console.print(panel)

    finally:
        session.close()


def cmd_read(args):
    """Mark an article as read."""
    session = get_session()

    try:
        article = session.query(Article).filter_by(id=args.article_id).first()

        if not article:
            console.print(f"[bold red]Article {args.article_id} not found[/bold red]")
            return

        article.is_read = True
        session.commit()
        console.print(f"[bold green]✓[/bold green] Marked article {args.article_id} as read")

    finally:
        session.close()


def cmd_unread(args):
    """Mark an article as unread."""
    session = get_session()

    try:
        article = session.query(Article).filter_by(id=args.article_id).first()

        if not article:
            console.print(f"[bold red]Article {args.article_id} not found[/bold red]")
            return

        article.is_read = False
        session.commit()
        console.print(f"[bold green]✓[/bold green] Marked article {args.article_id} as unread")

    finally:
        session.close()


def cmd_stats(args):
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


def cmd_process(args):
    """Process articles with LLM (summarization and topic extraction)."""
    from mindscout.processors.content import ContentProcessor

    try:
        processor = ContentProcessor()

        if args.limit:
            console.print(f"[bold blue]Processing up to {args.limit} articles...[/bold blue]")
        else:
            console.print("[bold blue]Processing all unprocessed articles...[/bold blue]")

        if args.force:
            console.print("[yellow]Force mode: reprocessing already processed articles[/yellow]")

        processed, failed = processor.process_batch(limit=args.limit, force=args.force)

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


def cmd_topics(args):
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


def cmd_find_by_topic(args):
    """Find articles by topic."""
    from mindscout.processors.content import ContentProcessor

    processor = ContentProcessor(lazy_init=True)
    articles = processor.get_articles_by_topic(args.topic, limit=args.limit)

    if not articles:
        console.print(f"[yellow]No articles found with topic matching '{args.topic}'[/yellow]")
        console.print("[dim]Make sure articles are processed first with 'mindscout process'[/dim]")
        return

    table = Table(
        title=f"Articles matching '{args.topic}' ({len(articles)} found)",
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


def cmd_processing_stats(args):
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
    table.add_row("Processing Rate", f"{stats['processing_rate']:.1f}%")

    console.print(table)


def cmd_clear(args):
    """Clear all articles from the database."""
    session = get_session()

    try:
        # Get count before deletion
        count = session.query(Article).count()

        if count == 0:
            console.print("[yellow]Database is already empty[/yellow]")
            return

        # Confirm deletion unless --force flag is used
        if not args.force:
            console.print(f"[bold yellow]Warning:[/bold yellow] This will delete {count} articles from the database.")
            response = input("Are you sure? Type 'yes' to confirm: ")
            if response.lower() != 'yes':
                console.print("[yellow]Operation cancelled[/yellow]")
                return

        # Delete all articles
        session.query(Article).delete()
        session.commit()

        console.print(f"[bold green]✓[/bold green] Deleted {count} articles from the database")

    except Exception as e:
        session.rollback()
        console.print(f"[bold red]Error:[/bold red] {e}")
    finally:
        session.close()


def main():
    """Main entry point for Mind Scout CLI."""
    # Initialize database
    init_db()

    # Create main parser
    parser = argparse.ArgumentParser(
        prog='mindscout',
        description='Mind Scout - Your AI research assistant'
    )
    parser.add_argument('--version', action='version', version='mindscout 0.2.0')

    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # fetch command
    parser_fetch = subparsers.add_parser('fetch', help='Fetch new articles from arXiv RSS')
    parser_fetch.add_argument('-c', '--categories', nargs='*', help='arXiv categories to fetch')
    parser_fetch.set_defaults(func=cmd_fetch)

    # search command (advanced arXiv API)
    parser_search = subparsers.add_parser('search', help='Search arXiv with advanced filters')
    parser_search.add_argument('-k', '--keywords', help='Keywords to search for')
    parser_search.add_argument('-c', '--categories', nargs='*', help='arXiv categories to filter by')
    parser_search.add_argument('-a', '--author', help='Author name to search for')
    parser_search.add_argument('-t', '--title', help='Title keywords to search for')
    parser_search.add_argument('--last-days', type=int, help='Fetch papers from last N days')
    parser_search.add_argument('--from-date', help='Start date (YYYY-MM-DD)')
    parser_search.add_argument('--to-date', help='End date (YYYY-MM-DD)')
    parser_search.add_argument('-n', '--max-results', type=int, default=100, help='Maximum results (default: 100)')
    parser_search.add_argument('--sort-by', choices=['submittedDate', 'lastUpdatedDate', 'relevance'],
                               default='submittedDate', help='Sort field')
    parser_search.add_argument('--sort-order', choices=['ascending', 'descending'],
                               default='descending', help='Sort order')
    parser_search.set_defaults(func=cmd_search)

    # fetch-semantic-scholar command
    parser_ss = subparsers.add_parser('fetch-semantic-scholar',
                                       help='Fetch papers from Semantic Scholar with citations')
    parser_ss.add_argument('query', help='Search query')
    parser_ss.add_argument('-n', '--max-results', type=int, default=50, help='Maximum results (default: 50)')
    parser_ss.add_argument('--sort', choices=['citationCount:desc', 'citationCount:asc',
                                               'publicationDate:desc', 'publicationDate:asc'],
                           default='citationCount:desc', help='Sort order (default: most cited)')
    parser_ss.add_argument('--year', help='Filter by year (e.g., "2024" or "2020-2024")')
    parser_ss.add_argument('--min-citations', type=int, help='Minimum citation count')
    parser_ss.set_defaults(func=cmd_fetch_semantic_scholar)

    # list command
    parser_list = subparsers.add_parser('list', help='List articles in the database')
    parser_list.add_argument('-u', '--unread', action='store_true', help='Show only unread articles')
    parser_list.add_argument('-n', '--limit', type=int, default=10, help='Number of articles to show')
    parser_list.add_argument('-s', '--source', help='Filter by source')
    parser_list.set_defaults(func=cmd_list)

    # show command
    parser_show = subparsers.add_parser('show', help='Show details of a specific article')
    parser_show.add_argument('article_id', type=int, help='Article ID')
    parser_show.set_defaults(func=cmd_show)

    # read command
    parser_read = subparsers.add_parser('read', help='Mark an article as read')
    parser_read.add_argument('article_id', type=int, help='Article ID')
    parser_read.set_defaults(func=cmd_read)

    # unread command
    parser_unread = subparsers.add_parser('unread', help='Mark an article as unread')
    parser_unread.add_argument('article_id', type=int, help='Article ID')
    parser_unread.set_defaults(func=cmd_unread)

    # stats command
    parser_stats = subparsers.add_parser('stats', help='Show statistics')
    parser_stats.set_defaults(func=cmd_stats)

    # process command
    parser_process = subparsers.add_parser('process', help='Process articles with LLM')
    parser_process.add_argument('-n', '--limit', type=int, help='Maximum number of articles to process')
    parser_process.add_argument('-f', '--force', action='store_true', help='Reprocess already processed articles')
    parser_process.set_defaults(func=cmd_process)

    # topics command
    parser_topics = subparsers.add_parser('topics', help='Show discovered topics')
    parser_topics.set_defaults(func=cmd_topics)

    # find-by-topic command
    parser_find = subparsers.add_parser('find-by-topic', help='Find articles by topic')
    parser_find.add_argument('topic', help='Topic to search for')
    parser_find.add_argument('-n', '--limit', type=int, default=10, help='Number of results')
    parser_find.set_defaults(func=cmd_find_by_topic)

    # processing-stats command
    parser_pstats = subparsers.add_parser('processing-stats', help='Show processing statistics')
    parser_pstats.set_defaults(func=cmd_processing_stats)

    # clear command
    parser_clear = subparsers.add_parser('clear', help='Clear all articles from database')
    parser_clear.add_argument('-f', '--force', action='store_true', help='Skip confirmation prompt')
    parser_clear.set_defaults(func=cmd_clear)

    # Parse arguments
    args = parser.parse_args()

    # Execute command
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
