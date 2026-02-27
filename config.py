"""
Sector News Tracker — Configuration
Multi-source news fetching: GNews API + NewsData.io + Google News RSS + Indian publication RSS feeds.
"""

import os

# ── API Configuration ──────────────────────────────────────────────────────────
GNEWS_API_KEY = os.environ.get("GNEWS_API_KEY", "")
GNEWS_BASE_URL = "https://gnews.io/api/v4/search"
GNEWS_MAX_RESULTS = 10

NEWSDATA_API_KEY = os.environ.get("NEWSDATA_API_KEY", "")
NEWSDATA_BASE_URL = "https://newsdata.io/api/1/latest"
NEWSDATA_MAX_RESULTS = 10

# Number of articles to keep per sector per region in the JSON store
MAX_ARTICLES_PER_SECTOR = 50

# ── Region Definitions ─────────────────────────────────────────────────────────
REGIONS = {
    "Global": {
        "country": None,           # GNews: no filter
        "newsdata_country": None,  # NewsData: no filter
        "google_params": "hl=en-US&gl=US&ceid=US:en",
        "label": "Global",
        "icon": "🌍",
    },
    "India": {
        "country": "in",           # GNews: country=in
        "newsdata_country": "in",  # NewsData: country=in
        "google_params": "hl=en-IN&gl=IN&ceid=IN:en",
        "label": "India",
        "icon": "🇮🇳",
    },
}

# ── Google News RSS Topics ─────────────────────────────────────────────────────
# Google News has built-in topic categories via RSS
# Format: https://news.google.com/rss/headlines/section/topic/TOPIC?params
GOOGLE_NEWS_TOPICS = {
    "TECHNOLOGY": "TECHNOLOGY",
    "BUSINESS": "BUSINESS",
    "HEALTH": "HEALTH",
    "SCIENCE": "SCIENCE",
}

# ── Sector Definitions ─────────────────────────────────────────────────────────
SECTORS = {
    "Technology": {
        # GNews queries
        "queries": [
            "technology business",
            "artificial intelligence industry",
            "semiconductor market",
        ],
        "queries_india": [
            "India technology startup",
            "Indian IT sector Infosys TCS",
        ],
        # NewsData.io queries (shorter, more focused)
        "newsdata_queries": ["technology business", "AI artificial intelligence"],
        "newsdata_queries_india": ["India IT sector", "India startup technology"],
        # Google News search queries for RSS
        "google_queries": ["technology industry", "AI semiconductor"],
        "google_queries_india": ["India technology sector", "Indian IT industry"],
        # Google News topic category
        "google_topic": "TECHNOLOGY",
        # RSS feeds — Global
        "rss_feeds": [
            "https://feeds.feedburner.com/TechCrunch/",
        ],
        # RSS feeds — India
        "rss_feeds_india": [
            "https://www.livemint.com/rss/technology",
            "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms",
        ],
    },
    "Banking & Finance": {
        "queries": [
            "banking sector news",
            "financial services industry",
            "fintech industry",
        ],
        "queries_india": [
            "RBI monetary policy",
            "Indian banking sector",
            "NSE BSE stock market India",
        ],
        "newsdata_queries": ["banking finance", "stock market"],
        "newsdata_queries_india": ["RBI India banking", "Indian stock market"],
        "google_queries": ["banking finance sector", "stock market trading"],
        "google_queries_india": ["India banking RBI", "NSE BSE Indian market"],
        "google_topic": "BUSINESS",
        "rss_feeds": [],
        "rss_feeds_india": [
            "https://www.livemint.com/rss/money",
            "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
            "https://www.business-standard.com/rss/finance.rss",
            "https://www.business-standard.com/rss/markets.rss",
            "http://www.moneycontrol.com/rss/latestnews.xml",
        ],
    },
    "Healthcare": {
        "queries": [
            "healthcare industry news",
            "pharmaceutical business",
            "biotech company",
        ],
        "queries_india": [
            "India healthcare sector",
            "Indian pharmaceutical industry",
        ],
        "newsdata_queries": ["healthcare industry", "pharmaceutical biotech"],
        "newsdata_queries_india": ["India healthcare", "Indian pharma"],
        "google_queries": ["healthcare industry", "pharmaceutical business"],
        "google_queries_india": ["India healthcare sector", "Indian pharma industry"],
        "google_topic": "HEALTH",
        "rss_feeds": [],
        "rss_feeds_india": [
            "https://economictimes.indiatimes.com/industry/healthcare/biotech/rssfeeds/13358014.cms",
        ],
    },
    "Energy": {
        "queries": [
            "energy sector business",
            "oil gas industry",
            "renewable energy market",
        ],
        "queries_india": [
            "India energy sector",
            "India renewable solar energy",
        ],
        "newsdata_queries": ["energy sector oil gas", "renewable energy"],
        "newsdata_queries_india": ["India energy sector", "India solar renewable"],
        "google_queries": ["energy sector oil gas", "renewable energy solar"],
        "google_queries_india": ["India energy oil gas", "India solar power renewable"],
        "google_topic": None,
        "rss_feeds": [],
        "rss_feeds_india": [
            "https://economictimes.indiatimes.com/industry/energy/rssfeeds/13358181.cms",
        ],
    },
    "Consumer Goods": {
        "queries": [
            "consumer goods industry",
            "FMCG market news",
            "e-commerce industry",
        ],
        "queries_india": [
            "India FMCG market",
            "India e-commerce Flipkart Reliance",
        ],
        "newsdata_queries": ["consumer goods FMCG", "retail e-commerce"],
        "newsdata_queries_india": ["India FMCG consumer", "India retail ecommerce"],
        "google_queries": ["consumer goods FMCG retail", "e-commerce industry"],
        "google_queries_india": ["India FMCG consumer goods", "India retail ecommerce"],
        "google_topic": None,
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
        ],
        "queries_india": [
            "India manufacturing Make in India",
            "Indian infrastructure development",
        ],
        "newsdata_queries": ["industrial manufacturing", "supply chain logistics"],
        "newsdata_queries_india": ["India manufacturing", "India infrastructure"],
        "google_queries": ["industrial manufacturing sector", "supply chain logistics"],
        "google_queries_india": ["India manufacturing sector", "India infrastructure development"],
        "google_topic": None,
        "rss_feeds": [],
        "rss_feeds_india": [
            "https://www.business-standard.com/rss/industry.rss",
        ],
    },
    "Real Estate": {
        "queries": [
            "real estate market news",
            "housing market trends",
        ],
        "queries_india": [
            "India real estate property market",
            "Indian housing sector RERA",
        ],
        "newsdata_queries": ["real estate market", "housing property"],
        "newsdata_queries_india": ["India real estate", "India housing RERA"],
        "google_queries": ["real estate market housing", "property market trends"],
        "google_queries_india": ["India real estate property", "India housing market"],
        "google_topic": None,
        "rss_feeds": [],
        "rss_feeds_india": [],
    },
    "Telecommunications": {
        "queries": [
            "telecom industry news",
            "5G network deployment",
        ],
        "queries_india": [
            "Jio Airtel India telecom",
            "India 5G rollout",
        ],
        "newsdata_queries": ["telecom 5G industry", "telecommunications"],
        "newsdata_queries_india": ["India telecom Jio Airtel", "India 5G"],
        "google_queries": ["telecom industry 5G", "telecommunications business"],
        "google_queries_india": ["India telecom Jio Airtel", "India 5G network"],
        "google_topic": None,
        "rss_feeds": [],
        "rss_feeds_india": [],
    },
}

# Data directory (relative to project root)
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
