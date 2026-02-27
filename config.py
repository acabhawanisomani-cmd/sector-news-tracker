"""
Sector News Tracker — Configuration
Defines sector keywords, API settings, RSS feed sources, and region settings.
"""

import os

# ── API Configuration ──────────────────────────────────────────────────────────
GNEWS_API_KEY = os.environ.get("GNEWS_API_KEY", "")
GNEWS_BASE_URL = "https://gnews.io/api/v4/search"
GNEWS_MAX_RESULTS = 10  # free tier allows max 10 per request

# Number of articles to keep per sector per region in the JSON store
MAX_ARTICLES_PER_SECTOR = 50

# ── Region Definitions ─────────────────────────────────────────────────────────
# GNews uses 'country' param for region filtering.
# "global" = no country filter (worldwide news)
# "india"  = country=in (India-specific news)
REGIONS = {
    "Global": {
        "country": None,  # No country filter → worldwide
        "label": "Global",
        "icon": "🌍",
    },
    "India": {
        "country": "in",  # GNews country code for India
        "label": "India",
        "icon": "🇮🇳",
    },
}

# ── Sector Definitions ─────────────────────────────────────────────────────────
# Each sector maps to:
#   - "queries": search queries for GNews (used for both regions)
#   - "queries_india": additional India-specific queries (appended for India region)
#   - "rss_feeds": global RSS feeds
#   - "rss_feeds_india": India-specific RSS feeds
SECTORS = {
    "Technology": {
        "queries": [
            "technology business",
            "artificial intelligence industry",
            "semiconductor market",
            "cloud computing enterprise",
            "cybersecurity industry",
        ],
        "queries_india": [
            "India technology startup",
            "Indian IT sector",
            "India digital economy",
        ],
        "rss_feeds": [
            "https://feeds.feedburner.com/TechCrunch/",
            "https://www.wired.com/feed/category/business/latest/rss",
        ],
        "rss_feeds_india": [
            "https://www.livemint.com/rss/technology",
            "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms",
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
        "queries_india": [
            "RBI monetary policy",
            "Indian banking sector",
            "NSE BSE stock market India",
            "India fintech UPI",
        ],
        "rss_feeds": [
            "https://www.ft.com/?format=rss",
            "https://feeds.bloomberg.com/markets/news.rss",
        ],
        "rss_feeds_india": [
            "https://www.livemint.com/rss/money",
            "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
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
        "queries_india": [
            "India healthcare sector",
            "Indian pharmaceutical industry",
            "Ayushman Bharat health",
        ],
        "rss_feeds": [
            "https://www.fiercehealthcare.com/rss/xml",
        ],
        "rss_feeds_india": [
            "https://economictimes.indiatimes.com/industry/healthcare/biotech/rssfeeds/13358014.cms",
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
        "queries_india": [
            "India energy sector",
            "Indian oil gas ONGC",
            "India solar renewable energy",
            "India electric vehicle market",
        ],
        "rss_feeds": [],
        "rss_feeds_india": [
            "https://economictimes.indiatimes.com/industry/energy/rssfeeds/13358181.cms",
        ],
    },
    "Consumer Goods": {
        "queries": [
            "consumer goods industry",
            "retail sector business",
            "FMCG market news",
            "e-commerce industry",
            "consumer spending trends",
        ],
        "queries_india": [
            "India FMCG market",
            "Indian retail consumer",
            "India e-commerce Flipkart Reliance",
        ],
        "rss_feeds": [],
        "rss_feeds_india": [
            "https://economictimes.indiatimes.com/industry/cons-products/rssfeeds/13358166.cms",
        ],
    },
    "Industrials": {
        "queries": [
            "industrial sector business",
            "manufacturing industry news",
            "supply chain logistics",
            "aerospace defense industry",
            "construction infrastructure market",
        ],
        "queries_india": [
            "India manufacturing Make in India",
            "Indian infrastructure development",
            "India defense industry",
        ],
        "rss_feeds": [],
        "rss_feeds_india": [],
    },
    "Real Estate": {
        "queries": [
            "real estate market news",
            "commercial property industry",
            "housing market trends",
            "REIT real estate investment",
        ],
        "queries_india": [
            "India real estate property market",
            "Indian housing sector RERA",
            "India commercial real estate",
        ],
        "rss_feeds": [],
        "rss_feeds_india": [],
    },
    "Telecommunications": {
        "queries": [
            "telecom industry news",
            "5G network deployment",
            "broadband internet provider",
            "telecommunications business",
        ],
        "queries_india": [
            "Jio Airtel India telecom",
            "India 5G rollout",
            "TRAI telecom regulation India",
        ],
        "rss_feeds": [],
        "rss_feeds_india": [],
    },
}

# Data directory (relative to project root)
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
