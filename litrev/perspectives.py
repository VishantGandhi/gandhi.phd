"""Perspective-based filtering system for literature reviews.

Perspectives encode methodological, conceptual, or thematic lenses
through which to evaluate scientific literature. Each perspective
defines terms that boost, penalize, or exclude papers based on
their methodology and approach.

Pre-built perspectives are tailored for the Zengler Lab's research
focus areas at UCSD.
"""
from typing import Dict, List, Optional, Tuple
import re


class Perspective:
    """A research perspective that filters and scores papers."""

    def __init__(
        self,
        name: str,
        description: str,
        boost_terms: List[str],
        penalize_terms: List[str] = None,
        exclude_if_only: List[str] = None,
        require_any: List[str] = None,
        weight: float = 1.0,
    ):
        self.name = name
        self.description = description
        self.boost_terms = [t.lower() for t in boost_terms]
        self.penalize_terms = [t.lower() for t in (penalize_terms or [])]
        self.exclude_if_only = [t.lower() for t in (exclude_if_only or [])]
        self.require_any = [t.lower() for t in (require_any or [])]
        self.weight = weight

    def score_text(self, text: str) -> Tuple[float, List[str]]:
        """Score a text block against this perspective.

        Returns:
            Tuple of (score, list of matched flags)
        """
        text_lower = text.lower()
        score = 0.0
        flags = []

        # Boost scoring
        for term in self.boost_terms:
            count = len(re.findall(re.escape(term), text_lower))
            if count > 0:
                score += count * 2.0
                flags.append(f"boost:{term}")

        # Penalize scoring
        for term in self.penalize_terms:
            count = len(re.findall(re.escape(term), text_lower))
            if count > 0:
                score -= count * 1.5
                flags.append(f"penalize:{term}")

        # Exclusion check: if ONLY excluded terms appear and NO boost terms
        if self.exclude_if_only:
            has_excluded = any(
                re.search(re.escape(t), text_lower) for t in self.exclude_if_only
            )
            has_boost = any(
                re.search(re.escape(t), text_lower) for t in self.boost_terms
            )
            if has_excluded and not has_boost:
                score = -100.0  # Strong exclusion signal
                flags.append("EXCLUDED:only_has_penalized_methods")

        # Require-any check
        if self.require_any:
            has_required = any(
                re.search(re.escape(t), text_lower) for t in self.require_any
            )
            if not has_required:
                score *= 0.3  # Heavy discount
                flags.append("missing_required_terms")

        return score * self.weight, flags

    def should_exclude(self, text: str) -> bool:
        """Check if a paper should be completely excluded."""
        score, _ = self.score_text(text)
        return score <= -100.0


# ============================================================
# Pre-built Perspectives for the Zengler Lab
# ============================================================

PERSPECTIVES: Dict[str, Perspective] = {

    "shotgun_metagenomics": Perspective(
        name="Shotgun Metagenomics",
        description=(
            "Prioritizes whole-genome shotgun sequencing and genome-resolved "
            "metagenomics. Penalizes studies relying solely on 16S rRNA amplicon "
            "sequencing. As the Zengler lab philosophy states: '16S is for the weak.'"
        ),
        boost_terms=[
            "shotgun metagenomics", "whole genome sequencing", "wgs",
            "metagenome-assembled genome", "mag", "genome-resolved metagenomics",
            "metagenomic sequencing", "deep sequencing", "whole metagenome",
            "metagenomic assembly", "coverage breadth", "functional metagenomics",
            "shotgun sequencing", "genome-resolved", "read mapping",
            "reference genome", "contig", "binning", "metagenomic profiling",
        ],
        penalize_terms=[
            "16s rrna gene sequencing", "16s amplicon", "amplicon sequencing",
            "v3-v4 region", "v4 region", "16s rdna", "its sequencing",
            "marker gene survey", "16s survey", "amplicon-based",
            "otu picking", "otu clustering",
        ],
        exclude_if_only=[
            "16s rrna", "16s amplicon", "amplicon sequencing", "v3-v4",
        ],
    ),

    "multi_omics": Perspective(
        name="Multi-Omics Integration",
        description=(
            "Prioritizes studies combining multiple omics layers: metagenomics + "
            "metatranscriptomics + metaproteomics/translatomics + metabolomics. "
            "Values integrated, systems-level analysis over single-omics snapshots. "
            "Especially values metaRibo-seq / metatranslatomics work."
        ),
        boost_terms=[
            "multi-omics", "multiomics", "metatranscriptomics", "metaproteomics",
            "metabolomics", "ribosome profiling", "ribo-seq", "translatomics",
            "metatranslatomics", "metaribo-seq", "integrative omics",
            "systems biology", "transcriptomics", "proteomics",
            "translational efficiency", "functional genomics",
            "multi-omic", "paired omics", "integrated analysis",
        ],
        penalize_terms=[
            "single marker gene", "amplicon only",
        ],
    ),

    "synthetic_communities": Perspective(
        name="Synthetic Microbial Communities (SynComs)",
        description=(
            "Prioritizes studies using defined, synthetic microbial communities "
            "for mechanistic investigation. Values reductionist approaches with "
            "known community composition. Includes in vitro community modeling, "
            "gnotobiotic systems, and bottom-up community assembly."
        ),
        boost_terms=[
            "synthetic community", "synthetic consortium", "syncom",
            "defined community", "defined consortium", "minimal community",
            "gnotobiotic", "mock community", "reconstituted community",
            "bottom-up", "in vitro community", "co-culture",
            "community assembly", "ecological engineering",
            "defined microbial", "model community", "constructed community",
            "fabricated ecosystem", "ecofab",
        ],
        penalize_terms=[
            "observational study", "cross-sectional survey",
        ],
    ),

    "clinical_translational": Perspective(
        name="Clinical & Translational Applications",
        description=(
            "Prioritizes studies with direct clinical relevance, therapeutic "
            "applications, or translational potential. Values high-quality "
            "clinical cohorts, interventional studies, and therapeutic "
            "microbiome engineering."
        ),
        boost_terms=[
            "clinical trial", "clinical cohort", "therapeutic", "probiotic",
            "treatment", "intervention", "patient", "disease", "diagnosis",
            "biomarker", "precision medicine", "translational",
            "fecal microbiota transplant", "fmt", "live biotherapeutic",
            "colonization resistance", "pathogen exclusion",
            "antibiotic", "antimicrobial", "drug target",
            "clinical outcome", "patient cohort", "randomized",
        ],
        penalize_terms=[
            "in silico only", "computational only", "simulation only",
        ],
    ),

    "mechanistic": Perspective(
        name="Mechanistic & Functional",
        description=(
            "Prioritizes studies that uncover causal mechanisms rather than "
            "correlational associations. Values functional assays, genetic "
            "knockouts, metabolic modeling, and experimental validation."
        ),
        boost_terms=[
            "mechanism", "mechanistic", "causal", "functional",
            "metabolic model", "genome-scale model", "flux balance",
            "knockout", "mutant", "competition assay", "cross-feeding",
            "auxotrophy", "metabolic exchange", "niche partitioning",
            "constraint-based", "ecological niche", "metabolic niche",
            "me-model", "growth phenotype",
        ],
        penalize_terms=[
            "correlational", "association study", "descriptive only",
            "observational", "biomarker discovery",
        ],
    ),

    "urobiome": Perspective(
        name="Urobiome & Urinary Tract Microbiology",
        description=(
            "Focused on the urinary microbiome, urinary tract infections, "
            "bladder ecology, and the gut-bladder axis. Includes catheter-associated "
            "UTI, recurrent UTI, lower urinary tract symptoms, and vaginal "
            "microbiome interactions with the urinary tract."
        ),
        boost_terms=[
            "urobiome", "urinary microbiome", "urinary tract",
            "bladder microbiome", "urinary tract infection", "uti",
            "recurrent uti", "ruti", "uropathogen", "cauti",
            "catheter-associated", "luts", "lower urinary tract",
            "urine", "bladder", "uroepithelial", "uropathogenic",
            "escherichia coli uti", "enterococcus faecalis",
            "asymptomatic bacteriuria", "gut-bladder axis",
            "vaginal microbiome", "lactobacillus crispatus",
            "interstitial cystitis", "bladder pain syndrome",
        ],
        penalize_terms=[],
    ),

    "anaerobic_microbiology": Perspective(
        name="Anaerobic Microbiology & Culturing",
        description=(
            "Prioritizes studies involving strict anaerobic cultivation, "
            "anaerobic chamber work, and characterization of obligate anaerobes. "
            "Values culturomics and high-throughput isolation approaches."
        ),
        boost_terms=[
            "anaerobic", "anaerobe", "obligate anaerobe", "anaerobic chamber",
            "anaerobic culture", "culturomics", "high-throughput cultivation",
            "hungate technique", "anaerobic digestion", "fermentation",
            "strict anaerobe", "oxygen-sensitive", "anaerobic workstation",
            "vinyl chamber", "coy chamber", "anaerobic jar",
        ],
        penalize_terms=[],
    ),

    "vaginal_microbiome": Perspective(
        name="Vaginal Microbiome",
        description=(
            "Focused on the vaginal microbiome, community state types, "
            "Lactobacillus-dominated communities, bacterial vaginosis, "
            "and interactions with the urogenital tract."
        ),
        boost_terms=[
            "vaginal microbiome", "vaginal microbiota", "cervicovaginal",
            "bacterial vaginosis", "community state type", "cst",
            "lactobacillus crispatus", "lactobacillus iners",
            "lactobacillus gasseri", "lactobacillus jensenii",
            "gardnerella", "vaginal lavage", "vaginal health",
            "vaginal dysbiosis", "aerobic vaginitis",
            "urogenital", "estrogen therapy",
        ],
        penalize_terms=[],
    ),

    "metabolic_modeling": Perspective(
        name="Metabolic Modeling & Systems Biology",
        description=(
            "Prioritizes studies using constraint-based metabolic modeling, "
            "genome-scale metabolic reconstructions (GEMs), ME-models, "
            "flux balance analysis, and community metabolic modeling."
        ),
        boost_terms=[
            "genome-scale model", "metabolic model", "flux balance analysis",
            "fba", "gem", "metabolic reconstruction", "me-model",
            "constraint-based", "proteome allocation",
            "metabolic flux", "stoichiometric model", "community model",
            "cobrame", "coralme", "solveme", "mind framework",
            "metabolic network", "pfba", "metabolic engineering",
        ],
        penalize_terms=[],
    ),
}


def get_perspective(name: str) -> Optional[Perspective]:
    """Get a perspective by name (case-insensitive)."""
    return PERSPECTIVES.get(name.lower())


def list_perspectives() -> Dict[str, str]:
    """Return a dict of {name: description} for all perspectives."""
    return {name: p.description for name, p in PERSPECTIVES.items()}


def apply_perspectives(
    papers: list,
    perspective_names: List[str],
) -> list:
    """Apply one or more perspectives to score and filter papers.

    Args:
        papers: List of Paper objects to score
        perspective_names: Names of perspectives to apply

    Returns:
        Filtered and scored list of Paper objects, sorted by combined score
    """
    perspectives = []
    for name in perspective_names:
        p = get_perspective(name)
        if p:
            perspectives.append(p)

    if not perspectives:
        return papers

    scored_papers = []
    for paper in papers:
        text = paper.searchable_text
        total_perspective_score = 0.0
        all_flags = []
        should_exclude = False

        for perspective in perspectives:
            score, flags = perspective.score_text(text)
            total_perspective_score += score
            all_flags.extend(flags)
            if perspective.should_exclude(text):
                should_exclude = True

        if should_exclude:
            continue

        paper.perspective_score = total_perspective_score
        paper.perspective_flags = all_flags

        # Combined score: base relevance + perspective + citation bonus
        citation_bonus = min(paper.citation_count * 0.1, 10.0)  # Cap at 10
        recency_bonus = max(0, (paper.year - 2020) * 0.5)  # Bonus for recent papers
        paper.combined_score = (
            paper.relevance_score
            + total_perspective_score
            + citation_bonus
            + recency_bonus
        )
        scored_papers.append(paper)

    # Sort by combined score descending
    scored_papers.sort(key=lambda p: p.combined_score, reverse=True)
    return scored_papers


def build_query_with_perspective(
    base_query: str,
    perspective_names: List[str],
) -> str:
    """Enhance a search query with perspective-specific terms.

    Adds key boost terms to the query to improve API search results.
    Only adds a few top terms to avoid over-constraining the search.

    Args:
        base_query: The user's original search query
        perspective_names: Perspectives to apply

    Returns:
        Enhanced query string
    """
    extra_terms = []
    for name in perspective_names:
        p = get_perspective(name)
        if p:
            # Add top 2-3 most distinctive terms from the perspective
            top_terms = p.boost_terms[:3]
            extra_terms.extend(top_terms)

    if not extra_terms:
        return base_query

    # Deduplicate
    seen = set()
    unique_terms = []
    for t in extra_terms:
        if t.lower() not in seen:
            seen.add(t.lower())
            unique_terms.append(t)

    # Only add a few terms to avoid over-constraining
    additions = " OR ".join(f'"{t}"' for t in unique_terms[:4])
    return f"({base_query}) AND ({additions})"
