"""
Sector News Tracker — Configuration
Defines sector keywords, API settings, and RSS feed sources.
"""

import os

# ── API Configuration ──────────────────────────────────────────────────────────
GNEWS_API_KEY = os.environ.get("GNEWS_API_KEY", "")
GNEWS_BASE_URL = "https://gnews.io/api/v4/search"
GNEWS_MAX_RESULTS = 10  # free tier allows max 10 per request

# Number of articles to keep per sector in the JSON store
MAX_ARTICLES_PER_SECTOR = 50

# ── Sector Definitions ─────────────────────────────────────────────────────────
# Each sector maps to a list of search queries used to fetch relevant news.
# GNews searches are done per query; results are merged and deduplicated.
SECTORS = {
    "Technology": {
        "queries": [
            "technology business",
            "artificial intelligence industry",
            "semiconductor market",
            "cloud computing enterprise",
            "cybersecurity industry",
        ],
        "rss_feeds": [
            "https://feeds.feedburner.com/TechCrunch/",
            "https://www.wired.com/feed/category/business/latest/rss",
        ],
    },
    "Banking & Finance": {
        "queries": [
            "banking sector news",
            "financial services industry",
            "interest rate central bank",
            "fintech industry",
            "stock market trading",
        ],
        "rss_feeds": [
            "https://www.ft.com/?format=rss",
            "https://feeds.bloomberg.com/markets/news.rss",
        ],
    },
    "Healthcare": {
        "queries": [
            "healthcare industry news",
            "pharmaceutical business",
            "biotech company",
            "medical devices market",
            "health insurance industry",
        ],
        "rss_feeds": [
            "https://www.fiercehealthcare.com/rss/xml",
        ],
    },
    "Energy": {
        "queries": [
            "energy sector business",
            "oil gas industry",
            "renewable energy market",
            "solar wind power industry",
            "electric vehicle battery",
        ],
        "rss_feeds": [],
    },
    "Consumer Goods": {
        "queries": [
            "consumer goods industry",
            "retail sector business",
            "FMCG market news",
            "e-commerce industry",
            "consumer spending trends",
        ],
        "rss_feeds": [],
    },
    "Industrials": {
        "queries": [
            "industrial sector business",
            "manufacturing industry news",
            "supply chain logistics",
            "aerospace defense industry",
            "construction infrastructure market",
        ],
        "rss_feeds": [],
    },
    "Real Estate": {
        "queries": [
            "real estate market news",
            "commercial property industry",
            "housing market trends",
            "REIT real estate investment",
        ],
        "rss_feeds": [],
    },
    "Telecommunications": {
        "queries": [
            "telecom industry news",
            "5G network deployment",
            "broadband internet provider",
            "telecommunications business",
        ],
        "rss_feeds": [],
    },
}

# Data directory (relative to project root)
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
