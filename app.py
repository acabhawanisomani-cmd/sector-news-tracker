"""
Sector News Tracker — Streamlit Dashboard
A clean, sector-based news dashboard for research analysts.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from config import DATA_DIR, SECTORS

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sector News Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main container */
    .block-container { padding-top: 1rem; }

    /* Card styles */
    .news-card {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1rem;
        transition: box-shadow 0.2s;
    }
    .news-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    [data-testid="stAppViewContainer"][data-theme="dark"] .news-card,
    .stApp[data-theme="dark"] .news-card {
        background: #1e1e1e;
        border-color: #333;
    }

    .news-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.4rem;
        line-height: 1.4;
    }
    .news-title a { color: #1a73e8; text-decoration: none; }
    .news-title a:hover { text-decoration: underline; }

    .news-meta {
        font-size: 0.82rem;
        color: #666;
        margin-bottom: 0.5rem;
    }
    .news-summary {
        font-size: 0.92rem;
        color: #444;
        line-height: 1.55;
    }
    [data-testid="stAppViewContainer"][data-theme="dark"] .news-summary,
    .stApp[data-theme="dark"] .news-summary {
        color: #ccc;
    }
    [data-testid="stAppViewContainer"][data-theme="dark"] .news-meta,
    .stApp[data-theme="dark"] .news-meta {
        color: #999;
    }

    .source-badge {
        background: #e8f0fe;
        color: #1a73e8;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 500;
    }

    .sector-header {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        margin-bottom: 0.2rem;
    }

    .last-updated {
        font-size: 0.82rem;
        color: #888;
        padding: 0.3rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ── Data Loading ───────────────────────────────────────────────────────────────

def sector_filename(sector: str) -> str:
    return f"{sector.lower().replace(' & ', '_').replace(' ', '_')}.json"


@st.cache_data(ttl=300)  # cache for 5 minutes
def load_sector_news(sector: str) -> list[dict]:
    """Load articles for a given sector from the JSON data store."""
    path = Path(DATA_DIR) / sector_filename(sector)
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


@st.cache_data(ttl=300)
def load_meta() -> dict:
    """Load the metadata file with last fetch info."""
    path = Path(DATA_DIR) / "_meta.json"
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def format_timestamp(ts: str) -> str:
    """Format an ISO timestamp to a human-readable string."""
    if not ts:
        return "Unknown"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = now - dt

        if delta.total_seconds() < 3600:
            mins = int(delta.total_seconds() / 60)
            return f"{mins}m ago"
        elif delta.total_seconds() < 86400:
            hours = int(delta.total_seconds() / 3600)
            return f"{hours}h ago"
        elif delta.days < 7:
            return f"{delta.days}d ago"
        else:
            return dt.strftime("%b %d, %Y")
    except ValueError:
        return ts[:16] if len(ts) > 16 else ts


# ── Sector Icons ───────────────────────────────────────────────────────────────
SECTOR_ICONS = {
    "Technology": "💻",
    "Banking & Finance": "🏦",
    "Healthcare": "🏥",
    "Energy": "⚡",
    "Consumer Goods": "🛒",
    "Industrials": "🏗️",
    "Real Estate": "🏠",
    "Telecommunications": "📡",
}


# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 📊 Sector News Tracker")
    st.markdown("---")

    sector_list = list(SECTORS.keys())
    selected_sector = st.selectbox(
        "Select Sector",
        sector_list,
        index=0,
        help="Choose a business sector to view the latest news.",
    )

    st.markdown("---")

    # Keyword filter
    keyword_filter = st.text_input(
        "🔍 Filter by keyword",
        placeholder="e.g. earnings, merger, AI",
        help="Filter articles by keyword in title or summary.",
    )

    # Source filter
    articles_for_filter = load_sector_news(selected_sector)
    sources = sorted({a.get("source", "Unknown") for a in articles_for_filter})
    selected_sources = st.multiselect(
        "📰 Filter by source",
        sources,
        default=[],
        help="Show articles from selected sources only.",
    )

    st.markdown("---")

    # Meta info
    meta = load_meta()
    if meta.get("last_fetch"):
        st.markdown(
            f'<div class="last-updated">Last updated: '
            f'{format_timestamp(meta["last_fetch"])}</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div style="font-size:0.75rem;color:#999;margin-top:1rem;">'
        "Data refreshes every hour via GitHub Actions."
        "</div>",
        unsafe_allow_html=True,
    )


# ── Main Content ───────────────────────────────────────────────────────────────

icon = SECTOR_ICONS.get(selected_sector, "📰")
st.markdown(
    f'<div class="sector-header">'
    f"<h1>{icon} {selected_sector}</h1>"
    f"</div>",
    unsafe_allow_html=True,
)

articles = load_sector_news(selected_sector)

# Apply filters
if keyword_filter:
    kw = keyword_filter.lower()
    articles = [
        a for a in articles
        if kw in a.get("title", "").lower() or kw in a.get("summary", "").lower()
    ]

if selected_sources:
    articles = [a for a in articles if a.get("source") in selected_sources]


if not articles:
    st.info(
        "No articles found for this sector yet. "
        "News will appear after the first automated fetch runs. "
        "You can also run `python fetch_news.py` manually."
    )
else:
    # Stats bar
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Articles", len(articles))
    recent_count = sum(
        1 for a in articles
        if "h ago" in format_timestamp(a.get("published_at", ""))
        or "m ago" in format_timestamp(a.get("published_at", ""))
    )
    col2.metric("Recent (< 24h)", recent_count)
    col3.metric("Sources", len({a.get("source") for a in articles}))

    st.markdown("---")

    # Article cards
    for article in articles:
        title = article.get("title", "No title")
        url = article.get("url", "#")
        source = article.get("source", "Unknown")
        summary = article.get("summary", "")
        published = format_timestamp(article.get("published_at", ""))

        card_html = f"""
        <div class="news-card">
            <div class="news-title">
                <a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a>
            </div>
            <div class="news-meta">
                <span class="source-badge">{source}</span>
                &nbsp;&middot;&nbsp; {published}
            </div>
            <div class="news-summary">{summary}</div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
