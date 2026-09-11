"""Multi-source literature search engine.

Searches PubMed, OpenAlex, and Semantic Scholar simultaneously,
deduplicates results, and applies perspective-based filtering.
"""
from typing import List, Optional
import time

from litrev.models import Paper, SearchResults
from litrev.search.pubmed import search_pubmed
from litrev.search.openalex import search_openalex
from litrev.search.semantic_scholar import search_semantic_scholar
from litrev.config import ZENGLER_LAB_AUTHORS


def aggregate_search(
    query: str,
    max_results: int = 50,
    years: int = 5,
    sources: List[str] = None,
) -> SearchResults:
    """Search across multiple literature databases and aggregate results.

    Args:
        query: Search query string
        max_results: Maximum results per source
        years: Limit to papers from the last N years
        sources: List of sources to query. Defaults to all.
                 Options: 'pubmed', 'openalex', 'semantic_scholar'

    Returns:
        SearchResults with deduplicated papers from all sources
    """
    if sources is None:
        sources = ["pubmed", "openalex", "semantic_scholar"]

    results = SearchResults(
        query=query,
        sources_queried=sources,
    )

    all_papers = []

    # Search each source
    for source in sources:
        try:
            if source == "pubmed":
                papers = search_pubmed(query, max_results=max_results, years=years)
                all_papers.extend(papers)
            elif source == "openalex":
                papers = search_openalex(query, max_results=max_results, years=years)
                all_papers.extend(papers)
            elif source == "semantic_scholar":
                papers = search_semantic_scholar(query, max_results=max_results, years=years)
                all_papers.extend(papers)
            # Small delay between API calls to be polite
            time.sleep(0.5)
        except Exception as e:
            results.errors.append(f"{source}: {str(e)}")

    results.total_found = len(all_papers)
    results.papers = all_papers

    # Deduplicate
    results.deduplicate()

    # Tag Zengler lab papers
    for paper in results.papers:
        _tag_zengler_lab(paper)

    return results


def _tag_zengler_lab(paper: Paper) -> None:
    """Tag a paper if it's from the Zengler lab."""
    for author in paper.authors:
        author_lower = author.lower()
        for lab_author in ZENGLER_LAB_AUTHORS:
            if lab_author.lower() in author_lower or author_lower in lab_author.lower():
                if "zengler_lab" not in paper.perspective_flags:
                    paper.perspective_flags.append("zengler_lab")
                return
