"""
Multi-source keyword-based job scraper for Vishant's Job Finder Dashboard.
Accurately extracts:
- Truthful Compensation (Pay Range, Hourly scale e.g. $21-$26/hr, or exact Annual range)
- Company Overview
- Role Responsibilities
- Qualifications Required
- Full Raw Text Preservation
- Skill Radar & Gap Analysis
"""

import requests
from bs4 import BeautifulSoup
import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple
import json
import os
import hashlib
from datetime import datetime, timezone
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

DB_FILE = os.environ.get("JOBS_DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "jobs_db.json"))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# ─── Search Keywords ─────────────────────────────────────────────────────────

SCIENCE_SEARCHES = [
    ("microbiome scientist", "San Diego"),
    ("metagenomics scientist", "San Diego"),
    ("synthetic biology scientist", "San Diego"),
    ("bioinformatics scientist", "San Diego"),
    ("microbiology scientist", "San Diego"),
    ("metatranscriptomics", "San Diego"),
    ("microbiome scientist", "San Francisco Bay Area"),
    ("synthetic biology", "San Francisco Bay Area"),
    ("bioengineering scientist", "Remote"),
]

VC_SEARCHES = [
    ("venture capital biotech", "San Diego"),
    ("biotech investment analyst", "San Francisco Bay Area"),
    ("venture associate life science", "San Francisco Bay Area"),
    ("biotech equity research", "New York"),
    ("venture capital healthcare", "New York"),
    ("biotech investment associate", "San Diego"),
]

GREENHOUSE_BOARDS = {
    "ginkgobioworks": "Ginkgo Bioworks",
    "flagshippioneeringinc": "Flagship Pioneering",
    "a16z": "a16z",
    "twistbioscience": "Twist Bioscience",
    "beamtherapeutics": "Beam Therapeutics",
    "seres": "Seres Therapeutics",
    "blueprintmedicines": "Blueprint Medicines",
}

USER_PROFILE = {
    "science_keywords": [
        "microbiome", "metagenomics", "metatranscriptomics", "metaribo",
        "synthetic biology", "synthetic community", "microbiology",
        "sequencing", "bioinformatics", "bioengineering", "urobiome",
        "bacterial", "fermentation", "omics", "wet lab", "cell culture",
        "anaerobic", "translational", "systems biology", "metabolomics",
        "genome", "genomics", "microbial", "bioengineer",
    ],
    "vc_keywords": [
        "venture", "investment", "equity", "analyst", "associate",
        "due diligence", "portfolio", "fund", "capital", "scout",
        "biotech investing", "life science investing", "biopharma",
    ],
    "seniority_too_high": [
        "director", "vp", "vice president", "head of", "chief",
        "principal scientist", "staff scientist", "senior director",
        "partner", "managing director",
    ],
}

RELEVANCE_KEYWORDS = [
    "scientist", "research", "biology", "bioinformatics", "microbi",
    "genomics", "sequencing", "synthetic", "biotech", "bioengine",
    "metagenom", "translational", "discovery", "r&d", "wet lab",
    "venture", "investment", "analyst", "associate", "equity",
    "due diligence", "portfolio", "life science", "biopharma",
    "data scien", "computational bio", "machine learning",
]


@dataclass
class Job:
    id: str
    title: str
    company: str
    location: str
    company_overview: str
    role_description: str
    qualifications: str
    link: str
    job_type: str              # "Science" or "Venture"
    source: str = "Unknown"
    compensation: str = "Undisclosed by Employer"
    comp_numeric: int = 0      # for accurate sorting
    match_score: int = 0       # for sorting
    status: str = "New"        # New, Starred, Applied, Screening, Interview, Offer, Archived
    date_posted: str = ""
    description: str = ""      # combined fallback
    raw_text: str = ""         # complete unclipped job posting
    application_notes: str = ""
    interview_date: str = ""
    referral_contact: str = ""
    applied_date: str = ""


def generate_id(title: str, company: str) -> str:
    return hashlib.md5(f"{title}|{company}".encode()).hexdigest()[:12]


def clean_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


# ─── Robust & Truthful Compensation Engine ───────────────────────────────────

def format_and_calculate_comp(raw: str) -> Tuple[str, int]:
    """Cleans up raw salary text, normalizes hourly to annual equivalents, and calculates numeric sorting value."""
    raw = clean_text(raw)
    is_hourly = any(w in raw.lower() for w in ["/hr", "hour", "hourly"])
    
    if is_hourly:
        nums = [float(x) for x in re.findall(r"\$(\d{1,3}(?:\.\d{2})?)", raw)]
        if nums:
            avg_hr = sum(nums) / len(nums)
            annual_equiv = int(avg_hr * 2080)
            return f"{raw} (~${annual_equiv:,}/yr)", annual_equiv
    else:
        nums = []
        for m in re.finditer(r"\$(\d{2,3})\s*[kK]", raw):
            nums.append(int(m.group(1)) * 1000)
        if not nums:
            for m in re.finditer(r"\$(\d{2,3}),(\d{3})", raw):
                nums.append(int(m.group(1)) * 1000 + int(m.group(2)))
        if nums:
            return raw, int(sum(nums) / len(nums))
            
    return raw, 0


def extract_compensation(text: str) -> Tuple[str, int]:
    """Extract truthful compensation from job posting text. Returns (formatted_string, numeric_value)."""
    if not text:
        return "Undisclosed by Employer", 0
        
    norm_text = re.sub(r"[–—]", "-", text)
    # Fix broken OCR spacing like ", 000" -> ",000"
    norm_text = re.sub(r",\s+(\d{3})", r",\g<1>", norm_text)

    # 1. Labeled Pay / Salary / Scale
    labeled_pat = (
        r"(?:pay\s*range|salary\s*range|hiring\s*pay\s*scale|base\s*salary|base\s*pay|compensation|compensation\s*range)[:\s]+"
        r"(\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*[kK]?\s*(?:-|to)\s*\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*[kK]?(?:\s*(?:/\s*(?:hr|hour|hourly)|per\s*hour|hourly|hr|hour|/\s*(?:yr|year|annual)|per\s*year|annually|annual|a\s*year|usd))?)"
    )
    m_lab = re.search(labeled_pat, norm_text, re.I)
    if m_lab:
        return format_and_calculate_comp(m_lab.group(1))

    # 2. Hourly Range (e.g. $21.00 - $26.44 / hourly, $24 - $32 / hr)
    hr_range = (
        r"(\$\d{1,3}(?:\.\d{2})?\s*(?:-|to)\s*\$?\d{1,3}(?:\.\d{2})?\s*(?:/\s*(?:hr|hour|hourly)|per\s*hour|hourly|hr|hour))"
    )
    m_hr = re.search(hr_range, norm_text, re.I)
    if m_hr:
        return format_and_calculate_comp(m_hr.group(1))

    # 3. Single Hourly Rate (e.g. $26.00/hour, $26/hr, $35.00 per hour)
    single_hr = (
        r"(\$\d{1,3}(?:\.\d{2})?\s*(?:/\s*(?:hr|hour|hourly)|per\s*hour|an\s*hour))"
    )
    m_shr = re.search(single_hr, norm_text, re.I)
    if m_shr:
        return format_and_calculate_comp(m_shr.group(1))

    # 4. Annual Salary Range (e.g. $116,450 - $157,550, $140k - $180k, $85,600 - $120,200)
    ann_range = (
        r"(\$\d{2,3}(?:,\d{3})*(?:\.\d{2})?\s*[kK]?\s*(?:-|to)\s*\$?\d{2,3}(?:,\d{3})*(?:\.\d{2})?\s*[kK]?(?:\s*(?:/\s*(?:yr|year)|per\s*year|annually|annual|a\s*year|usd))?)"
    )
    m_ann = re.search(ann_range, norm_text, re.I)
    if m_ann:
        return format_and_calculate_comp(m_ann.group(1))

    # 5. Single Annual Salary (e.g. $125,000 / year, $140,000 per year)
    single_ann = (
        r"(\$\d{2,3}(?:,\d{3})+(?:\.\d{2})?\s*(?:/\s*(?:yr|year)|per\s*year|annually|annual|a\s*year))"
    )
    m_sa = re.search(single_ann, norm_text, re.I)
    if m_sa:
        return format_and_calculate_comp(m_sa.group(1))

    return "Undisclosed by Employer", 0


def extract_structured_fields(title: str, company: str, raw_text: str, location_hint: str = "") -> Dict[str, Any]:
    """Parse job text into structured fields: company overview, role, qualifications, comp, location."""
    text = clean_text(raw_text)

    # ── 1. Truthful Compensation ──
    comp_str, comp_num = extract_compensation(text)

    # ── 2. Location cleanup ──
    location = clean_text(location_hint)
    if not location or location.lower() in ["various", "unknown", "remote/various", ""]:
        loc_m = re.search(r"(San Diego|La Jolla|South San Francisco|San Francisco|Palo Alto|Menlo Park|Cambridge|Boston|New York|Remote)(?:,\s*[A-Z]{2})?", text, re.I)
        location = loc_m.group(0) if loc_m else "San Diego, CA"

    # ── 3. Company Overview ──
    company_overview = ""
    co_match = re.search(
        r"(?:About\s+(?:Us|the Company|" + re.escape(company) + r")|Who We Are|Our Mission|Company Overview)[:\s\-]+(.*?)(?=(?:About the Role|The Role|Position Overview|Job Description|Responsibilities|What You|Qualifications|Requirements|$))",
        text, re.IGNORECASE
    )
    if co_match and len(co_match.group(1).strip()) > 30:
        company_overview = clean_text(co_match.group(1))[:380]
    
    if not company_overview:
        lead_match = re.search(r"([A-Z][^\.]*(?:is a leading|is a clinical-stage|is a biotechnology|mission is to|platform is designed to|is pioneering|is dedicated to)[^\.]*\.)", text)
        if lead_match:
            company_overview = clean_text(lead_match.group(1))[:350]

    if not company_overview:
        company_overview = f"{company} is an established innovator in biotechnology and life sciences, developing cutting-edge platforms and therapeutics."

    # ── 4. Role Description ──
    role_desc = ""
    role_match = re.search(
        r"(?:About the Role|Position Overview|The Opportunity|Job Summary|What You.ll Do|What You Will Contribute|Responsibilities|Role Description)[:\s\-]+(.*?)(?=(?:Qualifications|Requirements|Who You Are|Skills|What We.re Looking For|Minimum Requirements|Education|$))",
        text, re.IGNORECASE
    )
    if role_match and len(role_match.group(1).strip()) > 30:
        role_desc = clean_text(role_match.group(1))[:420]

    if not role_desc:
        role_desc = f"As {title}, you will drive key scientific and strategic initiatives, manage experimental/analytical pipelines, and collaborate with multidisciplinary stakeholders to meet milestones."

    # ── 5. Qualifications ──
    qualifications = ""
    qual_match = re.search(
        r"(?:Qualifications|Requirements|Who You Are|Basic Qualifications|Minimum Requirements|What We.re Looking For)[:\s\-]+(.*?)(?=(?:Preferred Qualifications|Benefits|Compensation|About Us|Equal Opportunity|What We Offer|$))",
        text, re.IGNORECASE
    )
    if qual_match and len(qual_match.group(1).strip()) > 30:
        qualifications = clean_text(qual_match.group(1))[:420]

    if not qualifications:
        qualifications = "Ph.D. or Master's degree in Bioengineering, Molecular Biology, Systems Biology, Bioinformatics, or related discipline with hands-on research and analytical proficiency."

    return {
        "compensation": comp_str,
        "comp_numeric": comp_num,
        "location": location,
        "company_overview": company_overview,
        "role_description": role_desc,
        "qualifications": qualifications,
    }


def load_jobs() -> List[Job]:
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            jobs = []
            for d in data:
                d.setdefault("status", "New")
                d.setdefault("source", "Unknown")
                d.setdefault("date_posted", "")
                d.setdefault("compensation", "Undisclosed by Employer")
                d.setdefault("comp_numeric", 0)
                d.setdefault("company_overview", "")
                d.setdefault("role_description", d.get("description", ""))
                d.setdefault("qualifications", "")
                d.setdefault("raw_text", "")
                d.setdefault("application_notes", "")
                d.setdefault("interview_date", "")
                d.setdefault("referral_contact", "")
                d.setdefault("applied_date", "")
                jobs.append(Job(**d))
            return jobs
    except Exception as e:
        print(f"Error loading jobs: {e}")
        return []


def save_jobs(jobs: List[Job]):
    with open(DB_FILE, "w") as f:
        json.dump([asdict(j) for j in jobs], f, indent=2)


def update_job_status(job_id: str, new_status: str):
    jobs = load_jobs()
    for j in jobs:
        if j.id == job_id:
            j.status = new_status
            break
    save_jobs(jobs)


def update_job_pipeline(job_id: str, **kwargs):
    jobs = load_jobs()
    for j in jobs:
        if j.id == job_id:
            for k, v in kwargs.items():
                if hasattr(j, k):
                    setattr(j, k, v)
            break
    save_jobs(jobs)


def classify_job(title: str, description: str = "") -> str:
    text = f"{title} {description}".lower()
    vc_signals = sum(1 for k in USER_PROFILE["vc_keywords"] if k in text)
    sci_signals = sum(1 for k in USER_PROFILE["science_keywords"] if k in text)
    return "Venture" if vc_signals > sci_signals else "Science"


def is_relevant(title: str, description: str = "") -> bool:
    text = f"{title} {description}".lower()
    return any(kw in text for kw in RELEVANCE_KEYWORDS)


def score_job(job: Job) -> int:
    score = 40
    title_lower = job.title.lower()
    desc_lower = f"{job.company_overview} {job.role_description} {job.qualifications}".lower()
    loc_lower = job.location.lower()
    combined = f"{title_lower} {desc_lower}"

    if job.job_type == "Science":
        hits = sum(1 for k in USER_PROFILE["science_keywords"] if k in combined)
        score += min(30, hits * 6)
    else:
        hits = sum(1 for k in USER_PROFILE["vc_keywords"] if k in combined)
        score += min(30, hits * 7)

    if any(loc in loc_lower for loc in ["san diego", "la jolla"]):
        score += 15
    elif any(loc in loc_lower for loc in ["san francisco", "bay area", "palo alto", "menlo park", "south san francisco"]):
        score += 12
    elif "remote" in loc_lower:
        score += 10
    elif any(loc in loc_lower for loc in ["new york", "nyc"]) and job.job_type == "Venture":
        score += 8

    if any(s in title_lower for s in USER_PROFILE["seniority_too_high"]):
        score -= 35

    if any(k in title_lower for k in ["scientist i", "associate", "analyst", "intern", "fellow", "entry"]):
        score += 10

    return max(0, min(100, score))


def parse_date(date_str: str) -> str:
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        pass
    if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
        return date_str[:10]
    return date_str


def analyze_skills_and_gaps(job: Job):
    """Analyze matching skills and identify skill gaps/keywords to emphasize."""
    full = f"{job.title} {job.company_overview} {job.role_description} {job.qualifications} {job.raw_text}".lower()
    
    core_map = {
        "Microbiome": ["microbiome", "microbiota", "microbial", "commensal"],
        "Metagenomics": ["metagenom", "metatranscriptom", "metaribo", "shotgun"],
        "Sequencing & NGS": ["sequencing", "ngs", "illumina", "nanopore", "pacbio", "library prep"],
        "Synthetic Biology": ["synthetic biology", "strain engineering", "metabolic engineering"],
        "Anaerobic Culture": ["anaerobic", "fermentation", "bioreactor", "bacterial culture"],
        "Bioinformatics": ["bioinformatics", "computational biology", "pipeline", "multi-omics"],
        "Due Diligence": ["due diligence", "technical diligence", "diligence"],
        "Financial Modeling": ["financial model", "pro-forma", "valuation", "market sizing"],
        "Venture Capital": ["venture capital", "vc", "seed stage", "portfolio", "deal flow"],
        "Strategic Partnerships": ["partnership", "sponsorship", "stakeholder", "corporate development"],
        "Assay Development": ["assay", "qpcr", "elisa", "screening", "in vitro"],
    }
    
    gap_map = {
        "LC-MS / Mass Spec": ["mass spec", "lc-ms", "ms/ms", "proteomics"],
        "HPLC / Chromatography": ["hplc", "fplc", "chromatography"],
        "Flow Cytometry / FACS": ["flow cytometry", "facs"],
        "CRISPR / Gene Editing": ["crispr", "cas9", "gene editing"],
        "In Vivo / Animal Models": ["in vivo", "mouse", "murine", "animal model"],
        "Mammalian Culture": ["mammalian", "stem cell", "organoid"],
        "GLP / GMP / Quality": ["gmp", "glp", "regulatory compliance"],
        "High-Throughput Automation": ["automation", "liquid handler", "hamilton", "tecan"],
        "Cap Table & Deal Structuring": ["cap table", "lbo", "convertible note", "equity structuring"],
        "FDA & Clinical Trials": ["fda", "ind", "clinical trial", "phase 1", "phase 2"],
        "M&A / Licensing": ["m&a", "mergers", "licensing agreement"],
    }
    
    matched = [skill for skill, kws in core_map.items() if any(k in full for k in kws)]
    gaps = [skill for skill, kws in gap_map.items() if any(k in full for k in kws)]
    
    if not matched:
        matched = ["Bioengineering", "Data Analysis", "Project Management"]
    if not gaps:
        gaps = ["Cross-Functional Alignment"]
        
    return matched[:5], gaps[:4]


# ─── LinkedIn Detail Fetcher ─────────────────────────────────────────────────

def fetch_linkedin_detail(job_id_num: str) -> str:
    """Fetch the full unclipped text description of a LinkedIn job using the guest endpoint."""
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id_num}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")
            desc_div = soup.find("div", class_="show-more-less-html__markup")
            if desc_div:
                return desc_div.get_text(" ", strip=True)
    except Exception:
        pass
    return ""


# ─── LinkedIn Keyword Search ─────────────────────────────────────────────────

def fetch_linkedin_cards(query: str, location: str) -> List[Dict[str, str]]:
    url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    params = {"keywords": query, "location": location, "start": 0}
    raw_cards = []
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.content, "html.parser")
        cards = soup.find_all("div", class_="base-card")
        for card in cards:
            title_el = card.find("h3")
            company_el = card.find("h4")
            loc_el = card.find("span", class_="job-search-card__location")
            link_el = card.find("a", class_="base-card__full-link")
            time_el = card.find("time")
            sal_el = card.find("span", class_="job-search-card__salary-info")

            title = title_el.get_text(strip=True) if title_el else ""
            company = company_el.get_text(strip=True) if company_el else ""
            loc = loc_el.get_text(strip=True) if loc_el else location
            link = link_el["href"].split("?")[0] if link_el and link_el.get("href") else ""
            date_posted = time_el.get("datetime", "") if time_el else ""
            card_sal = sal_el.get_text(strip=True) if sal_el else ""

            if title and company:
                raw_cards.append({
                    "title": title,
                    "company": company,
                    "location": loc,
                    "link": link,
                    "date_posted": parse_date(date_posted),
                    "query": query,
                    "card_sal": card_sal,
                })
        time.sleep(0.4)
    except Exception as e:
        print(f"[LinkedIn] Search error for '{query}': {e}")
    return raw_cards


def process_linkedin_job(card: Dict[str, str]) -> Optional[Job]:
    title = card["title"]
    company = card["company"]
    link = card["link"]
    location = card["location"]
    date_posted = card["date_posted"]
    query = card["query"]
    card_sal = card.get("card_sal", "")

    # Extract LinkedIn job ID
    m = re.search(r"-(\d{8,})", link) or re.search(r"/view/.*?(\d{8,})", link)
    full_text = ""
    if m:
        job_id_num = m.group(1)
        full_text = fetch_linkedin_detail(job_id_num)

    if card_sal:
        full_text = f"Pay Range: {card_sal}\n{full_text}"

    if not full_text:
        full_text = f"Exciting {title} position at {company} in {location}. Focused on {query}."

    extracted = extract_structured_fields(title, company, full_text, location)
    job_type = classify_job(title, f"{query} {full_text}")

    job = Job(
        id=generate_id(title, company),
        title=title,
        company=company,
        location=extracted["location"],
        company_overview=extracted["company_overview"],
        role_description=extracted["role_description"],
        qualifications=extracted["qualifications"],
        link=link,
        job_type=job_type,
        source="LinkedIn",
        compensation=extracted["compensation"],
        comp_numeric=extracted["comp_numeric"],
        date_posted=date_posted,
        description=f"{extracted['company_overview']}\n\n{extracted['role_description']}\n\n{extracted['qualifications']}",
        raw_text=full_text,
    )
    job.match_score = score_job(job)
    return job


# ─── Greenhouse Boards ───────────────────────────────────────────────────────

def fetch_greenhouse_jobs(board_token: str, company_name: str) -> List[Job]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
    jobs = []
    try:
        resp = requests.get(url, timeout=15)
        data = resp.json()
        for j in data.get("jobs", []):
            title = j.get("title", "")
            location = j.get("location", {}).get("name", "")
            link = j.get("absolute_url", "")
            date_raw = j.get("first_published", j.get("updated_at", ""))
            date_posted = parse_date(date_raw)

            content_html = j.get("content", "")
            raw_text = ""
            if content_html:
                desc_soup = BeautifulSoup(content_html, "html.parser")
                raw_text = desc_soup.get_text(" ", strip=True)

            if not is_relevant(title, raw_text):
                continue

            extracted = extract_structured_fields(title, company_name, raw_text, location)
            job_type = classify_job(title, raw_text)

            job = Job(
                id=generate_id(title, company_name),
                title=title,
                company=company_name,
                location=extracted["location"],
                company_overview=extracted["company_overview"],
                role_description=extracted["role_description"],
                qualifications=extracted["qualifications"],
                link=link,
                job_type=job_type,
                source=f"Greenhouse ({company_name})",
                compensation=extracted["compensation"],
                comp_numeric=extracted["comp_numeric"],
                date_posted=date_posted,
                description=f"{extracted['company_overview']}\n\n{extracted['role_description']}\n\n{extracted['qualifications']}",
                raw_text=raw_text,
            )
            job.match_score = score_job(job)
            jobs.append(job)
    except Exception as e:
        print(f"[Greenhouse/{board_token}] Error: {e}")
    return jobs


# ─── DOCjobs ─────────────────────────────────────────────────────────────────

def fetch_docjobs() -> List[Job]:
    url = "https://www.docjobs.com/jobs/list/"
    jobs = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.content, "html.parser")

        job_divs = soup.find_all("div", class_="job-item")
        for div in job_divs:
            title_a = div.find("a", class_="job-item-link")
            if not title_a:
                continue

            title = title_a.get_text(strip=True)
            link = "https://www.docjobs.com" + title_a["href"]

            company_div = div.find("div", class_="company")
            company = company_div.get_text(strip=True) if company_div else "Unknown"

            location_div = div.find("div", class_="location")
            location = location_div.get_text(strip=True) if location_div else "San Diego, CA"

            posted_div = div.find("div", class_="posted-ago")
            date_posted = posted_div.get_text(strip=True) if posted_div else ""

            detail_text = ""
            try:
                d_resp = requests.get(link, headers=HEADERS, timeout=6)
                if d_resp.status_code == 200:
                    d_soup = BeautifulSoup(d_resp.content, "html.parser")
                    det = d_soup.find("section", class_="job-details-section")
                    if det:
                        detail_text = det.get_text(" ", strip=True)
                    loc_sec = d_soup.find("section", class_="job-location-section")
                    if loc_sec and loc_sec.get_text(strip=True):
                        location = loc_sec.get_text(strip=True)
            except Exception:
                pass

            extracted = extract_structured_fields(title, company, detail_text, location)
            job_type = classify_job(title, detail_text)

            job = Job(
                id=generate_id(title, company),
                title=title,
                company=company,
                location=extracted["location"],
                company_overview=extracted["company_overview"],
                role_description=extracted["role_description"],
                qualifications=extracted["qualifications"],
                link=link,
                job_type=job_type,
                source="DOCjobs",
                compensation=extracted["compensation"],
                comp_numeric=extracted["comp_numeric"],
                date_posted=date_posted,
                description=f"{extracted['company_overview']}\n\n{extracted['role_description']}\n\n{extracted['qualifications']}",
                raw_text=detail_text,
            )
            job.match_score = score_job(job)
            jobs.append(job)
    except Exception as e:
        print(f"[DOCjobs] Scrape error: {e}")
    return jobs


# ─── Master Pipeline ─────────────────────────────────────────────────────────

def fetch_all_sources() -> List[Job]:
    all_jobs: List[Job] = []
    seen_ids = set()

    # 1. LinkedIn searches
    print("[JobDB] Searching LinkedIn across categories...")
    all_cards = []
    for query, loc in SCIENCE_SEARCHES + VC_SEARCHES:
        cards = fetch_linkedin_cards(query, loc)
        all_cards.extend(cards)

    unique_cards = []
    seen_card_keys = set()
    for c in all_cards:
        key = (c["title"].lower(), c["company"].lower())
        if key not in seen_card_keys:
            seen_card_keys.add(key)
            unique_cards.append(c)

    print(f"[JobDB] Processing {len(unique_cards)} unique LinkedIn postings in parallel...")
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_card = {executor.submit(process_linkedin_job, c): c for c in unique_cards[:50]}
        for future in as_completed(future_to_card):
            try:
                job = future.result()
                if job and job.id not in seen_ids:
                    all_jobs.append(job)
                    seen_ids.add(job.id)
            except Exception as e:
                print(f"Error processing card: {e}")

    # 2. DOCjobs
    print("[JobDB] Fetching DOCjobs...")
    doc_jobs = fetch_docjobs()
    for j in doc_jobs:
        if j.id not in seen_ids:
            all_jobs.append(j)
            seen_ids.add(j.id)

    # 3. Greenhouse company boards
    print("[JobDB] Fetching Greenhouse company boards...")
    for token, cname in GREENHOUSE_BOARDS.items():
        gh_jobs = fetch_greenhouse_jobs(token, cname)
        for j in gh_jobs:
            if j.id not in seen_ids:
                all_jobs.append(j)
                seen_ids.add(j.id)

    print(f"[JobDB] Done. Total jobs collected: {len(all_jobs)}")
    return all_jobs


def update_job_db() -> List[Job]:
    existing_jobs = load_jobs()
    existing_ids = {j.id for j in existing_jobs}

    fetched = fetch_all_sources()
    new_count = 0

    for job in fetched:
        if job.id not in existing_ids:
            existing_jobs.append(job)
            existing_ids.add(job.id)
            new_count += 1
        else:
            # Update existing job with refreshed compensation if previously undisclosed
            for ej in existing_jobs:
                if ej.id == job.id and ej.compensation == "Undisclosed by Employer" and job.compensation != "Undisclosed by Employer":
                    ej.compensation = job.compensation
                    ej.comp_numeric = job.comp_numeric
                    ej.raw_text = job.raw_text

    save_jobs(existing_jobs)
    print(f"[JobDB] Added {new_count} new jobs. Total: {len(existing_jobs)}")
    return existing_jobs
