"""Semantic Scholar search backend.

Uses the Semantic Scholar Academic Graph API to search for papers.
Provides good citation data and related paper recommendations.

API docs: https://api.semanticscholar.org/api-docs/
"""
import requests
import time
from typing import List, Optional
from datetime import datetime

from litrev.models import Paper
from litrev.config import (
    SEMANTIC_SCHOLAR_SEARCH_URL,
    SEMANTIC_SCHOLAR_RATE_LIMIT,
)


def search_semantic_scholar(
    query: str,
    max_results: int = 50,
    years: int = 5,
) -> List[Paper]:
    """Search Semantic Scholar and return parsed Paper objects.

    Args:
        query: Search query string
        max_results: Maximum number of results to return
        years: Limit to papers published in the last N years

    Returns:
        List of Paper objects with metadata from Semantic Scholar
    """
    min_year = datetime.now().year - years
    year_range = f"{min_year}-{datetime.now().year}"

    limit = min(max_results, 100)

    params = {
        "query": query,
        "limit": limit,
        "year": year_range,
        "fields": "title,authors,abstract,year,venue,externalIds,citationCount,url,publicationTypes",
    }

    try:
        response = requests.get(
            SEMANTIC_SCHOLAR_SEARCH_URL,
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as e:
        raise RuntimeError(f"Semantic Scholar search failed: {e}")

    results = data.get("data", [])
    papers = []

    for item in results:
        paper = _parse_s2_paper(item)
        if paper:
            papers.append(paper)

    return papers


def _parse_s2_paper(item: dict) -> Optional[Paper]:
    """Parse a Semantic Scholar paper object into a Paper."""
    title = item.get("title", "")
    if not title:
        return None

    # Authors
    authors = []
    for author in item.get("authors", []):
        name = author.get("name", "")
        if name:
            authors.append(name)

    # Abstract
    abstract = item.get("abstract", "") or ""

    # Year
    year = item.get("year", 0) or 0

    # Venue (journal)
    journal = item.get("venue", "") or ""

    # External IDs
    ext_ids = item.get("externalIds", {}) or {}
    doi = ext_ids.get("DOI", "") or ""
    pmid = str(ext_ids.get("PubMed", "")) if ext_ids.get("PubMed") else ""

    # Citation count
    citation_count = item.get("citationCount", 0) or 0

    # URL
    url = item.get("url", "") or ""

    # Publication types
    pub_types = item.get("publicationTypes", []) or []
    pub_type_str = ", ".join(pub_types)
    is_review = "Review" in pub_types
    is_clinical_only = "CaseReport" in pub_types or "ClinicalTrial" in pub_types
    
    return Paper(
        title=title,
        authors=authors,
        abstract=abstract,
        year=year,
        journal=journal,
        doi=doi,
        pmid=pmid,
        url=url,
        citation_count=citation_count,
        source="semantic_scholar",
        publication_type=pub_type_str,
        is_review=is_review,
        is_clinical_only=is_clinical_only,
        relevance_score=1.0,
    )
