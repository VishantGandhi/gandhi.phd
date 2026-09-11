"""Configuration and API settings for LitRev."""

# --- API Configuration ---
PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PUBMED_SEARCH_URL = f"{PUBMED_BASE_URL}/esearch.fcgi"
PUBMED_FETCH_URL = f"{PUBMED_BASE_URL}/efetch.fcgi"

OPENALEX_BASE_URL = "https://api.openalex.org"
OPENALEX_WORKS_URL = f"{OPENALEX_BASE_URL}/works"
# Polite pool: include email for higher rate limits
OPENALEX_EMAIL = "vgandhi@ucsd.edu"

SEMANTIC_SCHOLAR_BASE_URL = "https://api.semanticscholar.org/graph/v1"
SEMANTIC_SCHOLAR_SEARCH_URL = f"{SEMANTIC_SCHOLAR_BASE_URL}/paper/search"

# --- Rate Limiting ---
# PubMed: 3 requests/second without API key, 10 with key
PUBMED_RATE_LIMIT = 0.34  # seconds between requests (3/sec)
OPENALEX_RATE_LIMIT = 0.1  # very generous limits with polite pool
SEMANTIC_SCHOLAR_RATE_LIMIT = 1.0  # 1 request/second without key

# --- Default Search Parameters ---
DEFAULT_MAX_RESULTS = 50
DEFAULT_YEARS = 5
DEFAULT_SORT = "relevance"

# --- Zengler Lab Known Authors ---
# Used to identify and highlight lab publications in results
ZENGLER_LAB_AUTHORS = [
    "Zengler K",
    "Zengler, Karsten",
    "Karsten Zengler",
    "Moyne O",
    "Moyne, Oriane",
    "Zaramela LS",
    "Zaramela, Livia",
    "Weng Y",
    "Weng, Yuhan",
    "Al-Bassam M",
    "Al-Bassam, Mahmoud",
    "Tibocha-Bonilla JD",
    "Tibocha-Bonilla, Juan D",
    "Lieng C",
    "Lieng, Christopher",
    "Norton GJ",
    "Thiruppathy D",
    "Kumar M",
    "Haddad E",
    "Gandhi V",
    "Gandhi, Vishant",
]
