"""Data models for the literature review tool."""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import re


@dataclass
class Paper:
    """Represents a scientific paper with metadata."""
    title: str
    authors: List[str]
    abstract: str = ""
    year: int = 0
    journal: str = ""
    doi: str = ""
    pmid: str = ""
    url: str = ""
    citation_count: int = 0
    keywords: List[str] = field(default_factory=list)
    source: str = ""  # which API found it (pubmed, openalex, semantic_scholar)
    publication_type: str = ""  # e.g. "research-article", "review", "case-report"
    is_review: bool = False  # True for review articles, meta-analyses, editorials
    is_clinical_only: bool = False  # True for weak clinical papers without sequencing data
    relevance_score: float = 0.0
    perspective_score: float = 0.0
    combined_score: float = 0.0
    matched_themes: List[str] = field(default_factory=list)
    perspective_flags: List[str] = field(default_factory=list)

    @property
    def display_authors(self) -> str:
        """Format authors for display (first author et al. if >3)."""
        if not self.authors:
            return "Unknown"
        if len(self.authors) <= 3:
            return ", ".join(self.authors)
        return f"{self.authors[0]} et al."

    @property
    def citation_key(self) -> str:
        """Generate a citation key for BibTeX."""
        if self.authors:
            first_author = self.authors[0].split()[-1] if self.authors[0] else "Unknown"
            first_author = re.sub(r'[^a-zA-Z]', '', first_author)
        else:
            first_author = "Unknown"
        return f"{first_author}{self.year}"

    @property
    def link(self) -> str:
        """Return the best available URL for this paper."""
        if self.doi:
            return f"https://doi.org/{self.doi}"
        if self.pmid:
            return f"https://pubmed.ncbi.nlm.nih.gov/{self.pmid}/"
        return self.url or ""
        
    @property
    def ucsd_link(self) -> str:
        """Return a UCSD EZproxy link for full-text access."""
        base_link = self.link
        if not base_link:
            return ""
        # UCSD EZproxy URL structure
        return f"https://ucsd.idm.oclc.org/login?url={base_link}"

    @property
    def searchable_text(self) -> str:
        """Combine title, abstract, and keywords for text searching."""
        parts = [self.title, self.abstract]
        parts.extend(self.keywords)
        return " ".join(parts).lower()

    def __hash__(self):
        return hash(self.doi or self.pmid or self.title)

    def __eq__(self, other):
        if not isinstance(other, Paper):
            return False
        if self.doi and other.doi:
            return self.doi.lower().strip() == other.doi.lower().strip()
        if self.pmid and other.pmid:
            return self.pmid == other.pmid
        return self.title.lower().strip() == other.title.lower().strip()


@dataclass
class SearchResults:
    """Container for search results with metadata."""
    query: str
    papers: List[Paper] = field(default_factory=list)
    perspectives_applied: List[str] = field(default_factory=list)
    total_found: int = 0
    total_after_filtering: int = 0
    search_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    sources_queried: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def deduplicate(self) -> 'SearchResults':
        """Remove duplicate papers (by DOI, then PMID, then title) and merge metadata."""
        seen = {}
        unique = []
        for paper in self.papers:
            key = paper.doi.lower().strip() if paper.doi else (
                paper.pmid if paper.pmid else paper.title.lower().strip()
            )
            if key not in seen:
                seen[key] = paper
                unique.append(paper)
            else:
                # Merge boolean flags if any source detected them
                existing = seen[key]
                existing.is_review = existing.is_review or paper.is_review
                existing.is_clinical_only = existing.is_clinical_only or paper.is_clinical_only
                # Take highest citation count
                existing.citation_count = max(existing.citation_count, paper.citation_count)
                
        self.papers = unique
        self.total_after_filtering = len(unique)
        return self
