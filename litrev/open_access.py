"""
Open Access PDF and Full Text resolver using Unpaywall and PMC APIs.
"""
import urllib.request
import json
import re
from typing import Optional, Dict

_OA_CACHE: Dict[str, Dict[str, Optional[str]]] = {}

def resolve_open_access(doi: str, pmid: str = "") -> Dict[str, Optional[str]]:
    """
    Given a DOI or PMID, attempts to find the direct Open Access PDF URL.
    Returns a dict with:
      - is_oa: bool
      - pdf_url: str or None
      - landing_url: str or None
      - oa_status: str (e.g. 'gold', 'hybrid', 'green', 'closed')
    """
    clean_doi = doi.strip() if doi else ""
    if clean_doi in _OA_CACHE:
        return _OA_CACHE[clean_doi]

    result = {
        "is_oa": False,
        "pdf_url": None,
        "landing_url": None,
        "oa_status": "closed"
    }

    if clean_doi:
        try:
            url = f"https://api.unpaywall.org/v2/{urllib.parse.quote(clean_doi)}?email=vishant@gandhi.phd"
            req = urllib.request.Request(url, headers={"User-Agent": "LitRev/1.0"})
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode())
                
                is_oa = data.get("is_oa", False)
                best_loc = data.get("best_oa_location") or {}
                pdf_url = best_loc.get("url_for_pdf")
                landing_url = best_loc.get("url")
                oa_status = data.get("oa_status", "closed")

                result = {
                    "is_oa": is_oa,
                    "pdf_url": pdf_url,
                    "landing_url": landing_url,
                    "oa_status": oa_status
                }
        except Exception:
            pass

    # PMC fallback if pdf_url wasn't found but we have a PMID
    if not result["pdf_url"] and pmid:
        try:
            # Check if PMC article exists
            pmc_url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids={pmid}&format=json"
            req = urllib.request.Request(pmc_url, headers={"User-Agent": "LitRev/1.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                pmc_data = json.loads(resp.read().decode())
                records = pmc_data.get("records", [])
                if records and "pmcid" in records[0]:
                    pmcid = records[0]["pmcid"]
                    result["is_oa"] = True
                    result["pdf_url"] = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/"
                    result["landing_url"] = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"
                    result["oa_status"] = "pmc"
        except Exception:
            pass

    if clean_doi:
        _OA_CACHE[clean_doi] = result
    return result
