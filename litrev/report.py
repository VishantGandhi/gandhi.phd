"""Literature review report generator.

Generates structured Markdown reports from search results,
organized by detected themes and annotated with perspective scores.
"""
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from collections import Counter
import re

from litrev.models import Paper, SearchResults
from litrev.perspectives import get_perspective


# Pre-defined research themes for automatic categorization
RESEARCH_THEMES = {
    "colonization_resistance": {
        "label": "Colonization Resistance & Pathogen Exclusion",
        "terms": [
            "colonization resistance", "pathogen exclusion", "competitive exclusion",
            "barrier function", "infection prevention", "pathogen displacement",
            "commensal protection", "niche exclusion",
        ],
    },
    "community_assembly": {
        "label": "Community Assembly & Ecological Dynamics",
        "terms": [
            "community assembly", "ecological dynamics", "succession",
            "community stability", "resilience", "community structure",
            "species interactions", "co-occurrence", "keystone species",
        ],
    },
    "synthetic_communities": {
        "label": "Synthetic & Defined Microbial Communities",
        "terms": [
            "synthetic community", "syncom", "defined community",
            "minimal community", "model community", "gnotobiotic",
            "reconstituted", "in vitro community", "co-culture",
        ],
    },
    "multi_omics_methods": {
        "label": "Multi-Omics Methods & Integration",
        "terms": [
            "multi-omics", "metatranscriptomics", "metaproteomics",
            "ribosome profiling", "ribo-seq", "translatomics",
            "metabolomics", "integrative analysis", "systems biology",
        ],
    },
    "urinary_tract": {
        "label": "Urinary Tract & Urobiome",
        "terms": [
            "urinary", "bladder", "urobiome", "uti", "uropathogen",
            "urine", "urinary tract infection", "catheter",
            "lower urinary tract", "recurrent uti",
        ],
    },
    "vaginal_microbiome": {
        "label": "Vaginal Microbiome & Reproductive Health",
        "terms": [
            "vaginal", "cervicovaginal", "bacterial vaginosis",
            "community state type", "lactobacillus dominant",
            "vaginal dysbiosis", "reproductive",
        ],
    },
    "metabolic_modeling": {
        "label": "Metabolic Modeling & Computational Biology",
        "terms": [
            "metabolic model", "genome-scale model", "flux balance",
            "constraint-based", "me-model", "metabolic network",
            "stoichiometric", "coralme", "cobra",
        ],
    },
    "absolute_quantification": {
        "label": "Absolute Quantification & Spike-in Methods",
        "terms": [
            "absolute abundance", "spike-in", "synthetic dna", "syndna",
            "quantitative microbiome", "absolute quantification",
            "copy number", "total load", "cell count",
        ],
    },
    "host_microbe_interaction": {
        "label": "Host-Microbe Interactions",
        "terms": [
            "host-microbe", "host interaction", "immune response",
            "epithelial", "mucosal", "inflammation", "innate immunity",
            "host defense", "pathogenesis",
        ],
    },
    "anaerobic_microbiology": {
        "label": "Anaerobic Microbiology & Culturing",
        "terms": [
            "anaerobic", "anaerobe", "obligate anaerobe",
            "anaerobic chamber", "culturomics", "fermentation",
            "oxygen-sensitive",
        ],
    },
    "metagenomics_methods": {
        "label": "Metagenomic Methods & Bioinformatics",
        "terms": [
            "metagenome-assembled genome", "mag", "binning",
            "genome-resolved", "assembly", "coverage breadth",
            "reference database", "taxonomic classification",
            "functional annotation", "read mapping",
        ],
    },
    "therapeutics": {
        "label": "Microbiome Therapeutics & Interventions",
        "terms": [
            "therapeutic", "probiotic", "prebiotic", "biotherapeutic",
            "fecal transplant", "fmt", "intervention", "treatment",
            "precision medicine", "microbiome engineering",
        ],
    },
}


def detect_themes(papers: List[Paper]) -> Dict[str, List[Paper]]:
    """Assign papers to themes based on keyword matching.

    Each paper can belong to multiple themes. Papers with no theme
    match are placed in an 'Other' category.

    Args:
        papers: List of Paper objects to categorize

    Returns:
        Dict mapping theme labels to lists of papers
    """
    themed: Dict[str, List[Paper]] = {}
    unthemed = []

    for paper in papers:
        text = paper.searchable_text
        matched = False

        for theme_id, theme_info in RESEARCH_THEMES.items():
            score = sum(
                1 for term in theme_info["terms"]
                if term in text
            )
            if score >= 2:  # Require at least 2 matching terms
                label = theme_info["label"]
                if label not in themed:
                    themed[label] = []
                themed[label].append(paper)
                if theme_id not in paper.matched_themes:
                    paper.matched_themes.append(theme_id)
                matched = True

        if not matched:
            unthemed.append(paper)

    if unthemed:
        themed["Other Relevant Papers"] = unthemed

    return themed


def generate_review_report(
    results: SearchResults,
    perspectives: List[str] = None,
    output_path: str = None,
) -> str:
    """Generate a structured literature review report in Markdown.

    Args:
        results: SearchResults containing papers to review
        perspectives: List of perspective names that were applied
        output_path: Optional path to write the report file

    Returns:
        The Markdown report as a string
    """
    # Separate reviews and clinical papers
    papers = results.papers
    perspectives = perspectives or []
    reviews = [p for p in papers if p.is_review and not "zengler_lab" in p.perspective_flags]
    clinical = [p for p in papers if p.is_clinical_only and not p.is_review and not "zengler_lab" in p.perspective_flags]
    
    # Primary research papers go into themes
    primary_papers = [p for p in papers if p not in reviews and p not in clinical]
    themes = detect_themes(primary_papers)

    # Build report
    sections = []

    # Header
    sections.append(_build_header(results, perspectives))

    # Summary statistics
    sections.append(_build_summary(results, papers, perspectives))

    # Zengler Lab papers (if any)
    zengler_papers = [p for p in papers if "zengler_lab" in p.perspective_flags]
    if zengler_papers:
        sections.append(_build_zengler_section(zengler_papers))

    # Themed sections (Primary Research)
    for theme_label, theme_papers in themes.items():
        theme_papers.sort(key=lambda p: p.combined_score, reverse=True)
        sections.append(_build_theme_section(theme_label, theme_papers))

    # Reviews section
    if reviews:
        reviews.sort(key=lambda p: p.combined_score, reverse=True)
        sections.append(_build_theme_section("📚 Reviews & Meta-Analyses", reviews))

    # Clinical section
    if clinical:
        clinical.sort(key=lambda p: p.combined_score, reverse=True)
        sections.append(_build_theme_section("🏥 Clinical Observations & Case Reports", clinical))

    # Methodology notes
    if perspectives:
        sections.append(_build_methodology_notes(perspectives, results))

    # Footer
    sections.append(_build_footer())

    report = "\n\n".join(sections)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)

    return report


def _build_header(results: SearchResults, perspectives: List[str]) -> str:
    """Build the report header."""
    persp_str = ", ".join(perspectives) if perspectives else "None"
    return (
        f"# Literature Review: {results.query}\n\n"
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
        f"Perspectives: {persp_str} | "
        f"Papers: {len(results.papers)} | "
        f"Sources: {', '.join(results.sources_queried)}*"
    )


def _build_summary(results: SearchResults, papers: List[Paper], perspectives: List[str]) -> str:
    """Build the summary statistics section."""
    lines = ["## Summary\n"]

    lines.append(f"- **Total papers found across sources:** {results.total_found}")
    lines.append(f"- **After deduplication:** {results.total_after_filtering}")
    lines.append(f"- **After perspective filtering:** {len(papers)}")

    # Top journals
    journal_counts = Counter(p.journal for p in papers if p.journal)
    if journal_counts:
        top_journals = journal_counts.most_common(5)
        journals_str = ", ".join(f"{j} ({c})" for j, c in top_journals)
        lines.append(f"- **Top journals:** {journals_str}")

    # Year distribution
    year_counts = Counter(p.year for p in papers if p.year)
    if year_counts:
        years_sorted = sorted(year_counts.items(), reverse=True)
        years_str = ", ".join(f"{y}: {c}" for y, c in years_sorted[:5])
        lines.append(f"- **Year distribution:** {years_str}")

    # Most cited
    if papers:
        most_cited = max(papers, key=lambda p: p.citation_count)
        if most_cited.citation_count > 0:
            lines.append(
                f"- **Most cited:** {most_cited.display_authors} ({most_cited.year}) "
                f"- {most_cited.citation_count} citations"
            )

    # Perspective info
    for persp_name in perspectives:
        p = get_perspective(persp_name)
        if p:
            lines.append(f"\n> **Perspective: {p.name}** — {p.description}")

    # Errors
    if results.errors:
        lines.append("\n> ⚠️ **Search warnings:**")
        for err in results.errors:
            lines.append(f"> - {err}")

    return "\n".join(lines)


def _build_zengler_section(papers: List[Paper]) -> str:
    """Build a section highlighting Zengler lab publications."""
    lines = ["## 🔬 Zengler Lab Publications\n"]
    lines.append("*Papers from the Zengler Lab relevant to this topic:*\n")

    for paper in papers:
        lines.append(_format_paper_entry(paper, show_perspective=False))

    return "\n".join(lines)


def _build_theme_section(label: str, papers: List[Paper]) -> str:
    """Build a themed section with paper listings."""
    lines = [f"## {label}\n"]
    lines.append(f"*{len(papers)} papers*\n")

    for i, paper in enumerate(papers[:15], 1):
        lines.append(_format_paper_entry(paper, number=i))

    if len(papers) > 15:
        lines.append(f"\n*... and {len(papers) - 15} more papers in this theme.*")

    return "\n".join(lines)


def _format_paper_entry(paper: Paper, number: int = None, show_perspective: bool = True) -> str:
    """Format a single paper as a markdown entry."""
    prefix = f"{number}. " if number else "- "

    # Title line with link
    # Title line with link
    if paper.link:
        title_line = f"{prefix}**{paper.display_authors} ({paper.year})** — [{paper.title}]({paper.link})"
        if paper.ucsd_link:
            title_line += f" [[UCSD Full Text]({paper.ucsd_link})]"
    else:
        title_line = f"{prefix}**{paper.display_authors} ({paper.year})** — {paper.title}"

    # Journal and citation info
    meta_parts = []
    if paper.journal:
        meta_parts.append(f"*{paper.journal}*")
    if paper.citation_count > 0:
        meta_parts.append(f"Citations: {paper.citation_count}")
    if paper.source:
        meta_parts.append(f"Source: {paper.source}")

    # Perspective score indicator
    if show_perspective and paper.perspective_score != 0:
        if paper.perspective_score > 5:
            meta_parts.append("Perspective: ⭐⭐⭐")
        elif paper.perspective_score > 2:
            meta_parts.append("Perspective: ⭐⭐")
        elif paper.perspective_score > 0:
            meta_parts.append("Perspective: ⭐")

    # Zengler lab flag
    if "zengler_lab" in paper.perspective_flags:
        meta_parts.append("🔬 Zengler Lab")

    meta_line = f"   {' | '.join(meta_parts)}" if meta_parts else ""

    # Abstract excerpt
    abstract_line = ""
    if paper.abstract:
        excerpt = paper.abstract[:300].strip()
        if len(paper.abstract) > 300:
            excerpt += "..."
        abstract_line = f"\n   > {excerpt}"

    entry = title_line
    if meta_line:
        entry += "\n" + meta_line
    if abstract_line:
        entry += abstract_line
    entry += "\n"

    return entry


def _build_methodology_notes(perspectives: List[str], results: SearchResults) -> str:
    """Build methodology notes section."""
    lines = ["## Methodology Notes\n"]

    for persp_name in perspectives:
        p = get_perspective(persp_name)
        if p:
            lines.append(f"### Perspective: {p.name}\n")
            lines.append(f"{p.description}\n")

            if p.boost_terms:
                boost_str = ", ".join(f"`{t}`" for t in p.boost_terms[:8])
                lines.append(f"- **Boosted terms:** {boost_str}")
            if p.penalize_terms:
                pen_str = ", ".join(f"`{t}`" for t in p.penalize_terms[:8])
                lines.append(f"- **Penalized terms:** {pen_str}")
            lines.append("")

    if results.errors:
        lines.append("### Search Notes\n")
        for err in results.errors:
            lines.append(f"- ⚠️ {err}")

    return "\n".join(lines)


def _build_footer() -> str:
    """Build the report footer."""
    return (
        "---\n\n"
        "*Generated by LitRev — Context & Perspective-Specific Literature Review Tool*\n"
        "*Built for the Zengler Lab @ UCSD*\n"
        "*Tip: Export results to Zotero with `litrev export --format ris`*"
    )
