"""OpenAlex search backend.

Uses the OpenAlex API to search for scholarly works. OpenAlex is free,
open, and has comprehensive metadata including citation counts and
abstract reconstruction.

API docs: https://docs.openalex.org/
"""
import requests
import time
from typing import List, Optional
from datetime import datetime

from litrev.models import Paper
from litrev.config import (
    OPENALEX_WORKS_URL,
    OPENALEX_EMAIL,
    OPENALEX_RATE_LIMIT,
)


def search_openalex(
    query: str,
    max_results: int = 50,
    years: int = 5,
) -> List[Paper]:
    """Search OpenAlex and return parsed Paper objects.

    Args:
        query: Search query string
        max_results: Maximum number of results to return
        years: Limit to papers published in the last N years

    Returns:
        List of Paper objects with metadata from OpenAlex
    """
    min_year = datetime.now().year - years
    params = {
        "search": query,
        "filter": f"from_publication_date:{min_year}-01-01,type:article",
        "sort": "relevance_score:desc",
        "per_page": min(max_results, 200),
        "mailto": OPENALEX_EMAIL,
    }

    try:
        response = requests.get(OPENALEX_WORKS_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as e:
        raise RuntimeError(f"OpenAlex search failed: {e}")

    results = data.get("results", [])
    papers = []

    for work in results:
        paper = _parse_openalex_work(work)
        if paper:
            papers.append(paper)

    return papers


def _parse_openalex_work(work: dict) -> Optional[Paper]:
    """Parse an OpenAlex work object into a Paper."""
    title = work.get("title", "")
    if not title:
        return None

    # Authors
    authors = []
    for authorship in work.get("authorships", []):
        author = authorship.get("author", {})
        name = author.get("display_name", "")
        if name:
            authors.append(name)

    # Abstract - OpenAlex uses inverted index format
    abstract = _reconstruct_abstract(work.get("abstract_inverted_index"))

    # Year
    year = work.get("publication_year", 0) or 0

    # Journal
    journal = ""
    primary_loc = work.get("primary_location", {})
    if primary_loc:
        source = primary_loc.get("source", {})
        if source:
            journal = source.get("display_name", "")

    # DOI
    doi = work.get("doi", "") or ""
    if doi and doi.startswith("https://doi.org/"):
        doi = doi.replace("https://doi.org/", "")

    # Citation count
    citation_count = work.get("cited_by_count", 0) or 0

    # Keywords / Concepts
    keywords = []
    for concept in work.get("concepts", []):
        name = concept.get("display_name", "")
        score = concept.get("score", 0)
        if name and score and score > 0.3:
            keywords.append(name)
    for topic in work.get("topics", []):
        name = topic.get("display_name", "")
        if name:
            keywords.append(name)

    # URL
    url = work.get("id", "")

    # PMID
    pmid = ""
    ids = work.get("ids", {})
    if ids and "pmid" in ids:
        pmid_url = ids["pmid"]
        if pmid_url:
            pmid = pmid_url.replace("https://pubmed.ncbi.nlm.nih.gov/", "").strip("/")

    # Type
    pub_type = work.get("type", "")
    title_lower = title.lower()
    is_review = "review" in pub_type.lower() or "review" in title_lower or "meta-analysis" in title_lower
    is_clinical_only = False # Harder to tell just from OA type usually, leave false or check for case-report
    if "case" in pub_type.lower() or "report" in pub_type.lower() or "case report" in title_lower:
        is_clinical_only = True

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
        keywords=keywords,
        source="openalex",
        publication_type=pub_type,
        is_review=is_review,
        is_clinical_only=is_clinical_only,
        relevance_score=1.0,
    )


def _reconstruct_abstract(inverted_index: Optional[dict]) -> str:
    """Reconstruct abstract text from OpenAlex's inverted index format.

    OpenAlex stores abstracts as {word: [position1, position2, ...]} to save
    storage. We reconstruct the original text by placing words at their positions.
    """
    if not inverted_index:
        return ""

    positions = {}
    for word, indices in inverted_index.items():
        for idx in indices:
            positions[idx] = word

    if not positions:
        return ""

    max_pos = max(positions.keys())
    words = []
    for i in range(max_pos + 1):
        if i in positions:
            words.append(positions[i])

    return " ".join(words)
