"""
Configuration module for the Deep Research Agent.
Loads environment variables and provides central settings.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ──────────────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# ── Model Settings ────────────────────────────────────────
MODEL_NAME = "gemini-2.0-flash"
MAX_OUTPUT_TOKENS = 8192
TEMPERATURE = 0.3  # Lower for factual research

# ── Search Settings ───────────────────────────────────────
MAX_WEB_RESULTS = 10           # Per sub-query
MAX_ACADEMIC_RESULTS = 5       # Per sub-query
MAX_WIKIPEDIA_RESULTS = 3
MAX_CONTENT_LENGTH = 4000      # Characters per source
SEARCH_TIMEOUT = 15            # Seconds

# ── Agent Settings ────────────────────────────────────────
MAX_RESEARCH_ITERATIONS = 3    # Max depth of iterative research
MAX_SUB_QUERIES = 5            # Max sub-queries per decomposition
CREDIBILITY_THRESHOLD = 0.5    # Min credibility score (0-1)

# ── Credibility Domain Scores ─────────────────────────────
# Pre-scored domains for fast credibility lookup
DOMAIN_SCORES = {
    # Tier 1 — Authoritative (0.9-1.0)
    "nature.com": 0.95, "science.org": 0.95, "arxiv.org": 0.93,
    "pubmed.ncbi.nlm.nih.gov": 0.95, "scholar.google.com": 0.90,
    "ieee.org": 0.93, "acm.org": 0.92, "semanticscholar.org": 0.90,
    "who.int": 0.95, "cdc.gov": 0.93, "nih.gov": 0.94,
    "wikipedia.org": 0.82, "en.wikipedia.org": 0.82,
    "britannica.com": 0.88,

    # Tier 2 — Reputable News (0.75-0.89)
    "reuters.com": 0.88, "apnews.com": 0.88, "bbc.com": 0.85,
    "bbc.co.uk": 0.85, "nytimes.com": 0.84, "washingtonpost.com": 0.83,
    "theguardian.com": 0.82, "economist.com": 0.85,
    "wsj.com": 0.84, "ft.com": 0.84, "bloomberg.com": 0.83,
    "techcrunch.com": 0.78, "arstechnica.com": 0.80,
    "wired.com": 0.78, "theverge.com": 0.75,
    "mit.edu": 0.90, "stanford.edu": 0.90, "harvard.edu": 0.90,

    # Tier 3 — General (0.5-0.74)
    "medium.com": 0.55, "substack.com": 0.60,
    "reddit.com": 0.50, "quora.com": 0.45,
}

# ── Server Settings ───────────────────────────────────────
HOST = "0.0.0.0"
PORT = 8000
