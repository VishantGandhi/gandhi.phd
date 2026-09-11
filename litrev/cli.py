"""Command-line interface for LitRev.

Provides commands for searching literature, generating reviews,
and exporting results to citation manager formats.
"""
import click
import json
import sys
from typing import List, Optional
from datetime import datetime

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import print as rprint
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from litrev import __version__
from litrev.search import aggregate_search
from litrev.perspectives import (
    PERSPECTIVES,
    get_perspective,
    list_perspectives,
    apply_perspectives,
    build_query_with_perspective,
)
from litrev.report import generate_review_report
from litrev.export import export_bibtex, export_ris
from litrev.models import SearchResults


console = Console() if HAS_RICH else None


def _print(msg: str, style: str = None):
    """Print with Rich formatting if available, plain otherwise."""
    if HAS_RICH and console:
        console.print(msg, style=style)
    else:
        # Strip Rich markup for plain output
        import re
        clean = re.sub(r'\[/?[^\]]*\]', '', msg)
        print(clean)


@click.group()
@click.version_option(version=__version__)
def cli():
    """LitRev — Context & Perspective-Specific Literature Review Tool.

    Search across PubMed, OpenAlex, and Semantic Scholar with
    methodology-aware filtering. Built for microbiome researchers
    who demand more than 16S.

    \b
    Quick start:
      litrev search "colonization resistance urobiome"
      litrev review "synthetic microbial community metagenomics" -p shotgun_metagenomics
      litrev perspectives
    """
    pass


@cli.command()
@click.argument("query")
@click.option(
    "-p", "--perspective",
    multiple=True,
    help="Perspective filter to apply (can specify multiple). Use 'litrev perspectives' to list.",
)
@click.option(
    "-y", "--years",
    default=5,
    help="Limit to papers from the last N years.",
    show_default=True,
)
@click.option(
    "-n", "--max-results",
    default=50,
    help="Maximum results per source.",
    show_default=True,
)
@click.option(
    "-s", "--sources",
    default="pubmed,openalex,semantic_scholar",
    help="Comma-separated list of sources to query.",
    show_default=True,
)
@click.option(
    "-o", "--output",
    default=None,
    help="Save results to JSON file.",
)
def search(query: str, perspective: tuple, years: int, max_results: int, sources: str, output: str):
    """Search for papers across multiple literature databases.

    \b
    Examples:
      litrev search "colonization resistance urobiome"
      litrev search "metaRibo-seq metatranslatomics" -p multi_omics -p shotgun_metagenomics
      litrev search "synthetic community urinary tract" -y 3 -n 100
    """
    source_list = [s.strip() for s in sources.split(",")]
    perspective_list = list(perspective)

    _print(f"\n🔍 Searching for: [bold]{query}[/bold]", style="cyan")
    if perspective_list:
        _print(f"📐 Perspectives: {', '.join(perspective_list)}", style="yellow")
    _print(f"📅 Years: last {years} | 🗄️  Sources: {', '.join(source_list)}\n")

    # Optionally enhance query with perspective terms
    search_query = query
    if perspective_list:
        search_query = build_query_with_perspective(query, perspective_list)
        _print(f"🔧 Enhanced query: {search_query}\n", style="dim")

    # Perform search
    if HAS_RICH and console:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Searching databases...", total=None)
            results = aggregate_search(
                search_query,
                max_results=max_results,
                years=years,
                sources=source_list,
            )
            progress.update(task, completed=True)
    else:
        print("Searching databases...")
        results = aggregate_search(
            search_query,
            max_results=max_results,
            years=years,
            sources=source_list,
        )

    # Apply perspective filtering
    if perspective_list:
        results.papers = apply_perspectives(results.papers, perspective_list)
        results.total_after_filtering = len(results.papers)

    # Display results
    _print(f"\n✅ Found {results.total_found} papers, {results.total_after_filtering} after deduplication")
    if perspective_list:
        _print(f"📐 {len(results.papers)} papers after perspective filtering")

    if results.errors:
        for err in results.errors:
            _print(f"⚠️  {err}", style="yellow")

    _print("")

    # Display table
    if HAS_RICH and console and results.papers:
        table = Table(title=f"Search Results: {query}", show_lines=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Authors", style="cyan", max_width=25)
        table.add_column("Year", style="green", width=6)
        table.add_column("Title", max_width=50)
        table.add_column("Journal", style="magenta", max_width=25)
        table.add_column("Cited", style="yellow", width=6)
        table.add_column("Score", style="bold", width=7)

        for i, paper in enumerate(results.papers[:25], 1):
            flags = ""
            if "zengler_lab" in paper.perspective_flags:
                flags = " 🔬"
            table.add_row(
                str(i),
                paper.display_authors + flags,
                str(paper.year),
                paper.title[:80] + ("..." if len(paper.title) > 80 else ""),
                paper.journal[:30] if paper.journal else "-",
                str(paper.citation_count),
                f"{paper.combined_score:.1f}",
            )

        console.print(table)
    else:
        for i, paper in enumerate(results.papers[:25], 1):
            lab_flag = " [ZENGLER LAB]" if "zengler_lab" in paper.perspective_flags else ""
            print(
                f"  {i:3d}. {paper.display_authors} ({paper.year}) "
                f"- {paper.title[:70]}... "
                f"[{paper.journal or 'N/A'}] "
                f"Cited: {paper.citation_count} "
                f"Score: {paper.combined_score:.1f}"
                f"{lab_flag}"
            )

    if len(results.papers) > 25:
        _print(f"\n  ... and {len(results.papers) - 25} more results.")

    # Save to JSON if requested
    if output:
        _save_results_json(results, output)
        _print(f"\n💾 Results saved to: {output}", style="green")


@cli.command()
@click.argument("query")
@click.option(
    "-p", "--perspective",
    multiple=True,
    help="Perspective filter to apply.",
)
@click.option(
    "-y", "--years",
    default=5,
    help="Limit to papers from the last N years.",
    show_default=True,
)
@click.option(
    "-n", "--max-results",
    default=50,
    help="Maximum results per source.",
    show_default=True,
)
@click.option(
    "-s", "--sources",
    default="pubmed,openalex,semantic_scholar",
    help="Comma-separated list of sources.",
    show_default=True,
)
@click.option(
    "-o", "--output",
    default=None,
    help="Path for the Markdown review report. Defaults to stdout.",
)
@click.option(
    "--bib",
    default=None,
    help="Also export BibTeX to this path.",
)
@click.option(
    "--ris",
    default=None,
    help="Also export RIS (Zotero) to this path.",
)
def review(query: str, perspective: tuple, years: int, max_results: int, sources: str, output: str, bib: str, ris: str):
    """Generate a structured literature review report.

    Searches multiple databases, applies perspective filtering, groups
    papers by themes, and generates a formatted Markdown report.

    \b
    Examples:
      litrev review "colonization resistance urobiome" -p shotgun_metagenomics -o review.md
      litrev review "metaRibo-seq translational efficiency" -p multi_omics --bib refs.bib
      litrev review "synthetic community urinary microbiome" -p synthetic_communities -p urobiome
    """
    source_list = [s.strip() for s in sources.split(",")]
    perspective_list = list(perspective)

    _print(f"\n📚 Generating literature review for: [bold]{query}[/bold]", style="cyan")

    # Search
    search_query = query
    if perspective_list:
        search_query = build_query_with_perspective(query, perspective_list)

    if HAS_RICH and console:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Searching databases...", total=None)
            results = aggregate_search(
                search_query,
                max_results=max_results,
                years=years,
                sources=source_list,
            )
            progress.update(task, description="Applying perspectives...")
            if perspective_list:
                results.papers = apply_perspectives(results.papers, perspective_list)
                results.total_after_filtering = len(results.papers)
            progress.update(task, description="Generating report...")
            report = generate_review_report(results, perspective_list, output)
            progress.update(task, completed=True)
    else:
        print("Searching databases...")
        results = aggregate_search(
            search_query,
            max_results=max_results,
            years=years,
            sources=source_list,
        )
        if perspective_list:
            results.papers = apply_perspectives(results.papers, perspective_list)
            results.total_after_filtering = len(results.papers)
        print("Generating report...")
        report = generate_review_report(results, perspective_list, output)

    # Print or save
    if output:
        _print(f"\n✅ Report saved to: [bold]{output}[/bold]", style="green")
        _print(f"   Papers included: {len(results.papers)}")
    else:
        print(report)

    # Export citations if requested
    if bib:
        export_bibtex(results.papers, bib)
        _print(f"📖 BibTeX exported to: {bib}", style="green")

    if ris:
        export_ris(results.papers, ris)
        _print(f"📖 RIS exported to: {ris}", style="green")

    if results.errors:
        _print("\n⚠️  Warnings:", style="yellow")
        for err in results.errors:
            _print(f"  - {err}", style="yellow")


@cli.command("perspectives")
def list_perspectives_cmd():
    """List all available research perspectives."""
    _print("\n📐 Available Research Perspectives\n", style="bold cyan")

    if HAS_RICH and console:
        for name, persp in PERSPECTIVES.items():
            panel = Panel(
                f"{persp.description}\n\n"
                f"[dim]Boost terms:[/dim] {', '.join(persp.boost_terms[:6])}...\n"
                f"[dim]Penalize terms:[/dim] {', '.join(persp.penalize_terms[:4]) if persp.penalize_terms else 'None'}",
                title=f"[bold]{name}[/bold] — {persp.name}",
                border_style="green",
            )
            console.print(panel)
    else:
        for name, persp in PERSPECTIVES.items():
            print(f"  {name}")
            print(f"    {persp.name}")
            print(f"    {persp.description}")
            print(f"    Boost: {', '.join(persp.boost_terms[:5])}...")
            print()


@cli.command()
@click.argument("input_json")
@click.option(
    "-f", "--format",
    "fmt",
    type=click.Choice(["bibtex", "ris", "both"]),
    default="both",
    help="Export format.",
    show_default=True,
)
@click.option(
    "-o", "--output",
    default=None,
    help="Output file path (extension auto-added if needed).",
)
def export(input_json: str, fmt: str, output: str):
    """Export search results to citation manager formats.

    Takes a JSON file from 'litrev search --output results.json'
    and exports to BibTeX and/or RIS format.

    \b
    Examples:
      litrev export results.json -f bibtex -o refs.bib
      litrev export results.json -f ris -o refs.ris
      litrev export results.json -f both -o my_refs
    """
    from litrev.models import Paper

    # Load papers from JSON
    try:
        with open(input_json, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        _print(f"❌ Error loading {input_json}: {e}", style="red")
        sys.exit(1)

    papers = []
    for p in data.get("papers", []):
        papers.append(Paper(
            title=p.get("title", ""),
            authors=p.get("authors", []),
            abstract=p.get("abstract", ""),
            year=p.get("year", 0),
            journal=p.get("journal", ""),
            doi=p.get("doi", ""),
            pmid=p.get("pmid", ""),
            url=p.get("url", ""),
            citation_count=p.get("citation_count", 0),
            keywords=p.get("keywords", []),
            source=p.get("source", ""),
        ))

    if not papers:
        _print("❌ No papers found in input file.", style="red")
        sys.exit(1)

    base = output or "litrev_export"

    if fmt in ("bibtex", "both"):
        bib_path = base if base.endswith(".bib") else f"{base}.bib"
        export_bibtex(papers, bib_path)
        _print(f"📖 BibTeX exported: {bib_path} ({len(papers)} papers)", style="green")

    if fmt in ("ris", "both"):
        ris_path = base if base.endswith(".ris") else f"{base}.ris"
        export_ris(papers, ris_path)
        _print(f"📖 RIS exported: {ris_path} ({len(papers)} papers)", style="green")


def _save_results_json(results: SearchResults, path: str):
    """Save search results to a JSON file."""
    data = {
        "query": results.query,
        "search_timestamp": results.search_timestamp,
        "sources_queried": results.sources_queried,
        "total_found": results.total_found,
        "total_after_filtering": results.total_after_filtering,
        "errors": results.errors,
        "papers": [
            {
                "title": p.title,
                "authors": p.authors,
                "abstract": p.abstract,
                "year": p.year,
                "journal": p.journal,
                "doi": p.doi,
                "pmid": p.pmid,
                "url": p.url,
                "citation_count": p.citation_count,
                "keywords": p.keywords,
                "source": p.source,
                "relevance_score": p.relevance_score,
                "perspective_score": p.perspective_score,
                "combined_score": p.combined_score,
                "matched_themes": p.matched_themes,
                "perspective_flags": p.perspective_flags,
            }
            for p in results.papers
        ],
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    cli()
