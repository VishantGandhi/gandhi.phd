"""Export search results to citation manager formats.

Supports BibTeX and RIS (for Zotero, Mendeley, EndNote).
"""
from typing import List
import re
from litrev.models import Paper


def get_bibtex_string(papers: List[Paper]) -> str:
    """Return BibTeX formatted string for a list of papers."""
    entries = []
    used_keys = set()
    for paper in papers:
        key = _unique_key(paper.citation_key, used_keys)
        used_keys.add(key)
        entries.append(_paper_to_bibtex(paper, key))
    return "\n\n".join(entries)


def get_ris_string(papers: List[Paper]) -> str:
    """Return RIS formatted string for a list of papers."""
    entries = [_paper_to_ris(p) for p in papers]
    return "\n".join(entries)


def export_bibtex(papers: List[Paper], output_path: str) -> str:
    """Export papers to BibTeX format.

    Args:
        papers: List of Paper objects to export
        output_path: Path to write the .bib file

    Returns:
        Path to the written file
    """
    content = get_bibtex_string(papers)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content + "\n")

    return output_path


def export_ris(papers: List[Paper], output_path: str) -> str:
    """Export papers to RIS format (compatible with Zotero, Mendeley, EndNote).

    Args:
        papers: List of Paper objects to export
        output_path: Path to write the .ris file

    Returns:
        Path to the written file
    """
    entries = []

    for paper in papers:
        entry = _paper_to_ris(paper)
        entries.append(entry)

    content = "\n".join(entries)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path


def _paper_to_bibtex(paper: Paper, key: str) -> str:
    """Convert a Paper to a BibTeX entry string."""
    title = _escape_bibtex(paper.title)
    journal = _escape_bibtex(paper.journal)
    abstract = _escape_bibtex(paper.abstract)

    authors_bib = " and ".join(paper.authors) if paper.authors else "Unknown"

    lines = [
        f"@article{{{key},",
        f"  title = {{{title}}},",
        f"  author = {{{authors_bib}}},",
        f"  year = {{{paper.year}}},",
    ]

    if journal:
        lines.append(f"  journal = {{{journal}}},")
    if paper.doi:
        lines.append(f"  doi = {{{paper.doi}}},")
    if paper.pmid:
        lines.append(f"  pmid = {{{paper.pmid}}},")
    if paper.url or paper.link:
        lines.append(f"  url = {{{paper.link}}},")
    if abstract:
        if len(abstract) > 1000:
            abstract = abstract[:1000] + "..."
        lines.append(f"  abstract = {{{abstract}}},")
    if paper.keywords:
        kw_str = ", ".join(paper.keywords[:10])
        lines.append(f"  keywords = {{{kw_str}}},")

    lines.append("}")
    return "\n".join(lines)


def _paper_to_ris(paper: Paper) -> str:
    """Convert a Paper to an RIS entry string."""
    lines = [
        "TY  - JOUR",
        f"TI  - {paper.title}",
    ]

    for author in paper.authors:
        lines.append(f"AU  - {author}")

    if paper.year:
        lines.append(f"PY  - {paper.year}")
    if paper.journal:
        lines.append(f"JO  - {paper.journal}")
    if paper.doi:
        lines.append(f"DO  - {paper.doi}")
    if paper.pmid:
        lines.append(f"AN  - {paper.pmid}")
    if paper.url or paper.link:
        lines.append(f"UR  - {paper.link}")
    if paper.abstract:
        lines.append(f"AB  - {paper.abstract}")
    for kw in paper.keywords[:10]:
        lines.append(f"KW  - {kw}")

    lines.append("ER  - ")
    lines.append("")

    return "\n".join(lines)


def _escape_bibtex(text: str) -> str:
    """Escape special characters for BibTeX."""
    if not text:
        return ""
    replacements = {
        "&": "\\&",
        "%": "\\%",
        "#": "\\#",
    }
    for char, escaped in replacements.items():
        text = text.replace(char, escaped)
    return text


def _unique_key(base_key: str, used_keys: set) -> str:
    """Generate a unique citation key by appending letters if needed."""
    if base_key not in used_keys:
        return base_key
    for suffix in "abcdefghijklmnopqrstuvwxyz":
        candidate = f"{base_key}{suffix}"
        if candidate not in used_keys:
            return candidate
    return f"{base_key}_dup"
