"""Command-line interface for Mind Scout using argparse."""

import argparse
import sys
from datetime import datetime
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
    """Search and fetch articles from multiple sources."""
    source = args.source.lower()

    if source == 'arxiv':
        _search_arxiv(args)
    elif source == 'semanticscholar':
        _search_semanticscholar(args)
    else:
        console.print(f"[bold red]Error:[/bold red] Unknown source '{source}'")
        console.print("[yellow]Supported sources: arxiv, semanticscholar[/yellow]")


def _search_arxiv(args):
    """Search arXiv with advanced filters."""
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

    console.print(f"[bold blue]Searching arXiv:[/bold blue] {', '.join(desc_parts) if desc_parts else 'all fields'}")
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


def _search_semanticscholar(args):
    """Search Semantic Scholar with citation data."""
    from mindscout.fetchers.semanticscholar import SemanticScholarFetcher

    # Require query for Semantic Scholar
    if not args.query:
        console.print("[bold red]Error:[/bold red] Query is required for Semantic Scholar search")
        console.print("[yellow]Example:[/yellow] mindscout search --source semanticscholar --query \"transformers\" -n 20")
        return

    fetcher = SemanticScholarFetcher()

    # Build description
    desc_parts = [f"query: '{args.query}'"]
    if args.year:
        desc_parts.append(f"year: {args.year}")
    if args.min_citations:
        desc_parts.append(f"min citations: {args.min_citations}")

    console.print(f"[bold blue]Searching Semantic Scholar:[/bold blue] {', '.join(desc_parts)}")
    console.print(f"[dim]Max results: {args.max_results}, Sort: {args.ss_sort}[/dim]")

    try:
        new_count = fetcher.fetch_and_store(
            query=args.query,
            limit=args.max_results,
            sort=args.ss_sort,
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


def cmd_fetch_semantic_scholar(args):
    """Fetch papers from Semantic Scholar with citation data. DEPRECATED."""
    console.print("[yellow]⚠ Warning: This command is deprecated. Use 'search --source semanticscholar' instead.[/yellow]\n")

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


def cmd_profile(args):
    """Manage user profile."""
    from mindscout.profile import ProfileManager

    manager = ProfileManager()

    try:
        if args.profile_command == 'show':
            # Show profile summary
            summary = manager.get_profile_summary()

            panel_content = []
            panel_content.append(f"[bold cyan]Skill Level:[/bold cyan] {summary['skill_level']}")
            panel_content.append(f"[bold cyan]Daily Reading Goal:[/bold cyan] {summary['daily_reading_goal']} papers")

            interests = summary['interests']
            if interests:
                panel_content.append(f"\n[bold cyan]Interests:[/bold cyan]")
                for interest in interests:
                    panel_content.append(f"  • {interest}")
            else:
                panel_content.append(f"\n[bold cyan]Interests:[/bold cyan] [dim]None set[/dim]")

            sources = summary['preferred_sources']
            panel_content.append(f"\n[bold cyan]Preferred Sources:[/bold cyan] {', '.join(sources)}")

            panel_content.append(f"\n[dim]Last updated: {summary['updated_date'].strftime('%Y-%m-%d %H:%M')}[/dim]")

            from rich.panel import Panel
            console.print(Panel("\n".join(panel_content), title="Your Profile", border_style="cyan"))

        elif args.profile_command == 'set-interests':
            interests = [i.strip() for i in args.interests.split(",")]
            manager.set_interests(interests)
            console.print(f"[bold green]✓[/bold green] Set interests to: {', '.join(interests)}")

        elif args.profile_command == 'add-interests':
            interests = [i.strip() for i in args.interests.split(",")]
            manager.add_interests(interests)
            all_interests = manager.get_interests()
            console.print(f"[bold green]✓[/bold green] Added interests. Current interests: {', '.join(all_interests)}")

        elif args.profile_command == 'set-skill':
            manager.set_skill_level(args.level)
            console.print(f"[bold green]✓[/bold green] Set skill level to: {args.level}")

        elif args.profile_command == 'set-sources':
            sources = [s.strip() for s in args.sources.split(",")]
            manager.set_preferred_sources(sources)
            console.print(f"[bold green]✓[/bold green] Set preferred sources to: {', '.join(sources)}")

        elif args.profile_command == 'set-goal':
            manager.set_daily_goal(args.goal)
            console.print(f"[bold green]✓[/bold green] Set daily reading goal to: {args.goal} papers")

    finally:
        manager.close()


def cmd_rate(args):
    """Rate an article."""
    session = get_session()

    try:
        article = session.query(Article).filter_by(id=args.article_id).first()

        if not article:
            console.print(f"[bold red]Article {args.article_id} not found[/bold red]")
            return

        if args.rating < 1 or args.rating > 5:
            console.print("[bold red]Rating must be between 1 and 5[/bold red]")
            return

        article.rating = args.rating
        article.rated_date = datetime.utcnow()
        session.commit()

        stars = "★" * args.rating + "☆" * (5 - args.rating)
        console.print(f"[bold green]✓[/bold green] Rated article {args.article_id}: {stars} ({args.rating}/5)")
        console.print(f"[dim]{article.title[:80]}[/dim]")

    except Exception as e:
        session.rollback()
        console.print(f"[bold red]Error:[/bold red] {e}")
    finally:
        session.close()


def cmd_recommend(args):
    """Get personalized recommendations."""
    from mindscout.recommender import RecommendationEngine

    engine = RecommendationEngine()

    try:
        recommendations = engine.get_recommendations(
            limit=args.limit,
            days_back=args.days,
            unread_only=not args.include_read,
        )

        if not recommendations:
            console.print("[yellow]No recommendations found. Try:[/yellow]")
            console.print("  1. Set your interests: mindscout profile set-interests \"topic1, topic2\"")
            console.print("  2. Fetch more articles: mindscout search ...")
            console.print("  3. Process articles: mindscout process")
            return

        table = Table(
            title=f"Recommended for You ({len(recommendations)} articles)",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("ID", style="dim", width=6)
        table.add_column("Score", width=6, justify="right")
        table.add_column("Title", style="bold", min_width=40)
        table.add_column("Reason", width=30)

        for rec in recommendations:
            article = rec["article"]
            score_str = f"{rec['score']:.0%}"
            reason = rec["reasons"][0] if rec["reasons"] else "Good match"

            # Color code score
            if rec["score"] >= 0.7:
                score_str = f"[bold green]{score_str}[/bold green]"
            elif rec["score"] >= 0.4:
                score_str = f"[yellow]{score_str}[/yellow]"
            else:
                score_str = f"[dim]{score_str}[/dim]"

            table.add_row(
                str(article.id),
                score_str,
                article.title[:60],
                reason[:30],
            )

        console.print(table)

        if args.explain and recommendations:
            console.print("\n[bold cyan]Showing details for top recommendation:[/bold cyan]")
            top_rec = recommendations[0]
            explanation = engine.explain_recommendation(top_rec["article"])

            from rich.panel import Panel
            panel_content = []
            panel_content.append(f"[bold]Overall Score:[/bold] {explanation['overall_score']:.0%}")
            panel_content.append(f"\n[bold]Why recommended:[/bold]")
            for reason in explanation["reasons"]:
                panel_content.append(f"  • {reason}")

            panel_content.append(f"\n[bold]Score Breakdown:[/bold]")
            panel_content.append(f"  Topic Match: {explanation['details']['topic_match']:.0%}")
            panel_content.append(f"  Citations: {explanation['details']['citation_score']:.0%}")
            panel_content.append(f"  Recency: {explanation['details']['recency']:.0%}")
            panel_content.append(f"  Source: {explanation['details']['source_preference']:.0%}")
            panel_content.append(f"  Has Code: {'Yes' if explanation['details']['has_code'] else 'No'}")

            console.print(Panel("\n".join(panel_content), title=f"Article {top_rec['article'].id}", border_style="cyan"))

    finally:
        engine.close()


def cmd_insights(args):
    """Show reading insights and analytics."""
    session = get_session()

    try:
        from mindscout.profile import ProfileManager
        manager = ProfileManager()

        # Get profile
        profile = manager.get_or_create_profile()

        # Calculate stats
        total_articles = session.query(Article).count()
        read_count = session.query(Article).filter_by(is_read=True).count()
        rated_count = session.query(Article).filter(Article.rating.isnot(None)).count()

        # Get rating breakdown
        from sqlalchemy import func
        rating_dist = session.query(
            Article.rating,
            func.count(Article.id)
        ).filter(
            Article.rating.isnot(None)
        ).group_by(Article.rating).all()

        # Get source breakdown for read articles
        source_dist = session.query(
            Article.source,
            func.count(Article.id)
        ).filter(
            Article.is_read == True
        ).group_by(Article.source).all()

        # Display insights
        table = Table(title="Your Reading Insights", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right")

        table.add_row("Total Articles in Library", str(total_articles))
        table.add_row("Articles Read", f"[green]{read_count}[/green]")
        table.add_row("Articles Rated", str(rated_count))

        if total_articles > 0:
            read_pct = (read_count / total_articles) * 100
            table.add_row("Read Percentage", f"{read_pct:.1f}%")

        table.add_row("", "")
        table.add_row("Daily Reading Goal", str(profile.daily_reading_goal))

        console.print(table)

        if rating_dist:
            console.print("\n[bold cyan]Rating Distribution:[/bold cyan]")
            for rating, count in sorted(rating_dist):
                stars = "★" * int(rating)
                console.print(f"  {stars}: {count} articles")

        if source_dist:
            console.print("\n[bold cyan]Read Articles by Source:[/bold cyan]")
            for source, count in source_dist:
                console.print(f"  {source}: {count} articles")

    finally:
        session.close()
        manager.close()


def cmd_index(args):
    """Index articles in vector database for semantic search."""
    from mindscout.vectorstore import VectorStore

    vector_store = VectorStore()

    try:
        console.print("[bold blue]Indexing articles in vector database...[/bold blue]")

        if args.force:
            console.print("[yellow]Force mode: Re-indexing all articles[/yellow]")

        indexed = vector_store.index_articles(limit=args.limit, force=args.force)

        console.print(f"[bold green]✓[/bold green] Indexed {indexed} articles")

        # Show stats
        stats = vector_store.get_collection_stats()
        console.print(f"\n[dim]Total indexed: {stats['total_indexed']} articles[/dim]")
        console.print(f"[dim]Embedding dimension: {stats['model']}[/dim]")

    finally:
        vector_store.close()


def cmd_similar(args):
    """Find articles similar to a given article."""
    from mindscout.vectorstore import VectorStore

    vector_store = VectorStore()
    session = get_session()

    try:
        # Get the reference article
        article = session.query(Article).filter_by(id=args.article_id).first()

        if not article:
            console.print(f"[bold red]Article {args.article_id} not found[/bold red]")
            return

        console.print(f"[bold cyan]Finding articles similar to:[/bold cyan]")
        console.print(f"[dim]{article.title}[/dim]\n")

        # Find similar articles
        similar = vector_store.find_similar(
            args.article_id,
            n_results=args.limit,
            min_similarity=args.min_similarity
        )

        if not similar:
            console.print("[yellow]No similar articles found. Try:[/yellow]")
            console.print("  1. Lowering --min-similarity threshold")
            console.print("  2. Indexing more articles: mindscout index")
            return

        table = Table(
            title=f"Similar Articles ({len(similar)} found)",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("ID", style="dim", width=6)
        table.add_column("Similarity", width=10, justify="right")
        table.add_column("Title", style="bold", min_width=40)
        table.add_column("Source", width=12)

        for sim in similar:
            sim_article = sim["article"]
            similarity_str = f"{sim['similarity']:.0%}"

            # Color code similarity
            if sim["similarity"] >= 0.7:
                similarity_str = f"[bold green]{similarity_str}[/bold green]"
            elif sim["similarity"] >= 0.5:
                similarity_str = f"[yellow]{similarity_str}[/yellow]"
            else:
                similarity_str = f"[dim]{similarity_str}[/dim]"

            table.add_row(
                str(sim_article.id),
                similarity_str,
                sim_article.title[:60],
                sim_article.source
            )

        console.print(table)

    finally:
        vector_store.close()
        session.close()


def cmd_semantic_search(args):
    """Perform semantic search for articles."""
    from mindscout.vectorstore import VectorStore

    vector_store = VectorStore()

    try:
        console.print(f"[bold blue]Semantic search:[/bold blue] \"{args.query}\"\n")

        results = vector_store.semantic_search(args.query, n_results=args.limit)

        if not results:
            console.print("[yellow]No results found. Make sure articles are indexed:[/yellow]")
            console.print("  mindscout index")
            return

        table = Table(
            title=f"Search Results ({len(results)} found)",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("ID", style="dim", width=6)
        table.add_column("Relevance", width=10, justify="right")
        table.add_column("Title", style="bold", min_width=40)
        table.add_column("Source", width=12)

        for result in results:
            article = result["article"]
            relevance_str = f"{result['relevance']:.0%}"

            # Color code relevance
            if result["relevance"] >= 0.7:
                relevance_str = f"[bold green]{relevance_str}[/bold green]"
            elif result["relevance"] >= 0.5:
                relevance_str = f"[yellow]{relevance_str}[/yellow]"
            else:
                relevance_str = f"[dim]{relevance_str}[/dim]"

            table.add_row(
                str(article.id),
                relevance_str,
                article.title[:60],
                article.source
            )

        console.print(table)

    finally:
        vector_store.close()


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
    parser_search = subparsers.add_parser('search', help='Search multiple sources with advanced filters')
    parser_search.add_argument('--source', choices=['arxiv', 'semanticscholar'], default='arxiv',
                               help='Source to search (default: arxiv)')
    parser_search.add_argument('-n', '--max-results', type=int, default=100, help='Maximum results (default: 100)')

    # Common arguments
    parser_search.add_argument('-q', '--query', help='Search query (required for Semantic Scholar)')

    # arXiv-specific arguments
    parser_search.add_argument('-k', '--keywords', help='[arXiv] Keywords to search for')
    parser_search.add_argument('-c', '--categories', nargs='*', help='[arXiv] arXiv categories to filter by')
    parser_search.add_argument('-a', '--author', help='[arXiv] Author name to search for')
    parser_search.add_argument('-t', '--title', help='[arXiv] Title keywords to search for')
    parser_search.add_argument('--last-days', type=int, help='[arXiv] Fetch papers from last N days')
    parser_search.add_argument('--from-date', help='[arXiv] Start date (YYYY-MM-DD)')
    parser_search.add_argument('--to-date', help='[arXiv] End date (YYYY-MM-DD)')
    parser_search.add_argument('--sort-by', choices=['submittedDate', 'lastUpdatedDate', 'relevance'],
                               default='submittedDate', help='[arXiv] Sort field')
    parser_search.add_argument('--sort-order', choices=['ascending', 'descending'],
                               default='descending', help='[arXiv] Sort order')

    # Semantic Scholar-specific arguments
    parser_search.add_argument('--ss-sort', choices=['citationCount:desc', 'citationCount:asc',
                                                      'publicationDate:desc', 'publicationDate:asc'],
                               default='citationCount:desc', help='[Semantic Scholar] Sort order')
    parser_search.add_argument('--year', help='[Semantic Scholar] Filter by year (e.g., "2024" or "2020-2024")')
    parser_search.add_argument('--min-citations', type=int, help='[Semantic Scholar] Minimum citation count')

    parser_search.set_defaults(func=cmd_search)

    # fetch-semantic-scholar command (DEPRECATED - use 'search --source semanticscholar' instead)
    parser_ss = subparsers.add_parser('fetch-semantic-scholar',
                                       help='[DEPRECATED] Use "search --source semanticscholar" instead')
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

    # profile command (Phase 4)
    parser_profile = subparsers.add_parser('profile', help='Manage your user profile')
    profile_subparsers = parser_profile.add_subparsers(dest='profile_command', required=True)

    # profile show
    profile_show = profile_subparsers.add_parser('show', help='Show your profile')

    # profile set-interests
    profile_set_int = profile_subparsers.add_parser('set-interests', help='Set your interests (replaces existing)')
    profile_set_int.add_argument('interests', help='Comma-separated list of topics (e.g., "transformers, RL, NLP")')

    # profile add-interests
    profile_add_int = profile_subparsers.add_parser('add-interests', help='Add interests (keeps existing)')
    profile_add_int.add_argument('interests', help='Comma-separated list of topics to add')

    # profile set-skill
    profile_set_skill = profile_subparsers.add_parser('set-skill', help='Set your skill level')
    profile_set_skill.add_argument('level', choices=['beginner', 'intermediate', 'advanced'], help='Skill level')

    # profile set-sources
    profile_set_src = profile_subparsers.add_parser('set-sources', help='Set preferred sources')
    profile_set_src.add_argument('sources', help='Comma-separated list (e.g., "arxiv,semanticscholar")')

    # profile set-goal
    profile_set_goal = profile_subparsers.add_parser('set-goal', help='Set daily reading goal')
    profile_set_goal.add_argument('goal', type=int, help='Number of papers to read per day')

    parser_profile.set_defaults(func=cmd_profile)

    # rate command (Phase 4)
    parser_rate = subparsers.add_parser('rate', help='Rate an article (1-5 stars)')
    parser_rate.add_argument('article_id', type=int, help='Article ID')
    parser_rate.add_argument('rating', type=int, help='Rating (1-5 stars)')
    parser_rate.set_defaults(func=cmd_rate)

    # recommend command (Phase 4)
    parser_rec = subparsers.add_parser('recommend', help='Get personalized recommendations')
    parser_rec.add_argument('-n', '--limit', type=int, default=10, help='Number of recommendations (default: 10)')
    parser_rec.add_argument('-d', '--days', type=int, default=30, help='Look back N days (default: 30)')
    parser_rec.add_argument('--include-read', action='store_true', help='Include already-read articles')
    parser_rec.add_argument('--explain', action='store_true', help='Show detailed explanation for top recommendation')
    parser_rec.set_defaults(func=cmd_recommend)

    # insights command (Phase 4)
    parser_insights = subparsers.add_parser('insights', help='Show reading insights and analytics')
    parser_insights.set_defaults(func=cmd_insights)

    # index command (Phase 5)
    parser_index = subparsers.add_parser('index', help='Index articles for semantic search')
    parser_index.add_argument('-n', '--limit', type=int, help='Maximum number of articles to index')
    parser_index.add_argument('-f', '--force', action='store_true', help='Re-index all articles')
    parser_index.set_defaults(func=cmd_index)

    # similar command (Phase 5)
    parser_similar = subparsers.add_parser('similar', help='Find similar articles')
    parser_similar.add_argument('article_id', type=int, help='Article ID to find similar papers for')
    parser_similar.add_argument('-n', '--limit', type=int, default=10, help='Number of results (default: 10)')
    parser_similar.add_argument('--min-similarity', type=float, default=0.3, help='Minimum similarity score (0-1)')
    parser_similar.set_defaults(func=cmd_similar)

    # semantic-search command (Phase 5)
    parser_semantic = subparsers.add_parser('semantic-search', help='Semantic search for articles')
    parser_semantic.add_argument('query', help='Natural language search query')
    parser_semantic.add_argument('-n', '--limit', type=int, default=10, help='Number of results (default: 10)')
    parser_semantic.set_defaults(func=cmd_semantic_search)

    # Parse arguments
    args = parser.parse_args()

    # Execute command
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
