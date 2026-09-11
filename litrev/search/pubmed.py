"""PubMed E-utilities search backend.

Uses NCBI's E-utilities API (esearch + efetch) to search PubMed
and retrieve paper metadata including abstracts.

API docs: https://www.ncbi.nlm.nih.gov/books/NBK25499/
"""
import requests
import xml.etree.ElementTree as ET
import time
from typing import List
from datetime import datetime

from litrev.models import Paper
from litrev.config import (
    PUBMED_SEARCH_URL,
    PUBMED_FETCH_URL,
    PUBMED_RATE_LIMIT,
)


def search_pubmed(
    query: str,
    max_results: int = 50,
    years: int = 5,
) -> List[Paper]:
    """Search PubMed and return parsed Paper objects.

    Args:
        query: PubMed search query (supports MeSH terms, boolean operators)
        max_results: Maximum number of results to return
        years: Limit to papers published in the last N years

    Returns:
        List of Paper objects with metadata from PubMed
    """
    # Step 1: Search for PMIDs
    min_year = datetime.now().year - years
    search_params = {
        "db": "pubmed",
        "term": query,
        "retmax": min(max_results, 200),  # PubMed cap
        "sort": "relevance",
        "retmode": "json",
        "mindate": str(min_year),
        "maxdate": str(datetime.now().year),
        "datetype": "pdat",
    }

    try:
        response = requests.get(PUBMED_SEARCH_URL, params=search_params, timeout=30)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as e:
        raise RuntimeError(f"PubMed search failed: {e}")

    pmids = data.get("esearchresult", {}).get("idlist", [])
    if not pmids:
        return []

    time.sleep(PUBMED_RATE_LIMIT)

    # Step 2: Fetch full records
    fetch_params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
    }

    try:
        response = requests.get(PUBMED_FETCH_URL, params=fetch_params, timeout=60)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"PubMed fetch failed: {e}")

    # Step 3: Parse XML
    try:
        root = ET.fromstring(response.text)
    except ET.ParseError as e:
        raise RuntimeError(f"PubMed XML parsing failed: {e}")

    papers = []
    for article in root.findall(".//PubmedArticle"):
        paper = _parse_pubmed_article(article)
        if paper:
            papers.append(paper)

    return papers


def _parse_pubmed_article(article: ET.Element) -> Paper:
    """Parse a PubmedArticle XML element into a Paper object."""
    medline = article.find(".//MedlineCitation")
    if medline is None:
        return None

    art = medline.find(".//Article")
    if art is None:
        return None

    # Title
    title_el = art.find(".//ArticleTitle")
    title = _get_text(title_el) if title_el is not None else ""

    # Abstract
    abstract_parts = []
    abstract_el = art.find(".//Abstract")
    if abstract_el is not None:
        for text_el in abstract_el.findall(".//AbstractText"):
            label = text_el.get("Label", "")
            text = _get_text(text_el)
            if label:
                abstract_parts.append(f"{label}: {text}")
            else:
                abstract_parts.append(text)
    abstract = " ".join(abstract_parts)

    # Authors
    authors = []
    author_list = art.find(".//AuthorList")
    if author_list is not None:
        for author_el in author_list.findall(".//Author"):
            last = author_el.findtext("LastName", "")
            first = author_el.findtext("ForeName", "")
            initials = author_el.findtext("Initials", "")
            if last:
                if first:
                    authors.append(f"{last} {initials}" if initials else f"{last} {first}")
                else:
                    authors.append(last)

    # Journal
    journal_el = art.find(".//Journal/Title")
    journal = journal_el.text if journal_el is not None and journal_el.text else ""
    # Fallback to ISOAbbreviation
    if not journal:
        iso_el = art.find(".//Journal/ISOAbbreviation")
        journal = iso_el.text if iso_el is not None and iso_el.text else ""

    # Year
    year = 0
    pub_date = art.find(".//Journal/JournalIssue/PubDate")
    if pub_date is not None:
        year_el = pub_date.find("Year")
        if year_el is not None and year_el.text:
            try:
                year = int(year_el.text)
            except ValueError:
                pass
        if year == 0:
            medline_date = pub_date.find("MedlineDate")
            if medline_date is not None and medline_date.text:
                parts = medline_date.text.split()
                if parts:
                    try:
                        year = int(parts[0])
                    except ValueError:
                        pass

    # PMID
    pmid_el = medline.find(".//PMID")
    pmid = pmid_el.text if pmid_el is not None and pmid_el.text else ""

    # DOI
    doi = ""
    for id_el in article.findall(".//ArticleIdList/ArticleId"):
        if id_el.get("IdType") == "doi":
            doi = id_el.text if id_el.text else ""
            break
    # Also check ELocationID
    if not doi:
        for eloc in art.findall(".//ELocationID"):
            if eloc.get("EIdType") == "doi":
                doi = eloc.text if eloc.text else ""
                break

    # Keywords
    keywords = []
    for kw_list in medline.findall(".//KeywordList/Keyword"):
        if kw_list.text:
            keywords.append(kw_list.text)
    # Also get MeSH terms
    for mesh in medline.findall(".//MeshHeadingList/MeshHeading/DescriptorName"):
        if mesh.text:
            keywords.append(mesh.text)

    # Publication Types
    pub_types = []
    for pt in art.findall(".//PublicationTypeList/PublicationType"):
        if pt.text:
            pub_types.append(pt.text)
    
    pub_type_str = ", ".join(pub_types)
    is_review = any("Review" in pt or "Meta-Analysis" in pt or "Systematic Review" in pt for pt in pub_types)
    
    # Simple check for clinical only (no sequences, etc)
    is_clinical_only = any(pt in ["Case Reports", "Clinical Trial", "Observational Study", "Comment", "Editorial"] for pt in pub_types)

    return Paper(
        title=title,
        authors=authors,
        abstract=abstract,
        year=year,
        journal=journal,
        doi=doi,
        pmid=pmid,
        url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
        keywords=keywords,
        source="pubmed",
        publication_type=pub_type_str,
        is_review=is_review,
        is_clinical_only=is_clinical_only,
        relevance_score=1.0,
    )


def _get_text(element: ET.Element) -> str:
    """Extract all text content from an XML element, including children."""
    return "".join(element.itertext()).strip()
