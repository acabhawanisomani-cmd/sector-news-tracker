#!/usr/bin/env python3
"""
Sector News Tracker — Multi-Source News Fetcher

Sources (in priority order):
  1. Google News RSS  — unlimited, free, no API key needed
  2. NewsData.io API  — 200 credits/day free tier
  3. GNews API        — 100 requests/day free tier
  4. Direct RSS feeds — unlimited (LiveMint, Economic Times, Business Standard, MoneyControl, TechCrunch)

Fetches news for both Global and India regions, deduplicates, and writes to JSON.
Designed to run via GitHub Actions every hour.
"""

import hashlib
import json
import logging
import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus, urlencode

import requests

from config import (
    DATA_DIR,
    GNEWS_API_KEY,
    GNEWS_BASE_URL,
    GNEWS_MAX_RESULTS,
    MAX_ARTICLES_PER_SECTOR,
    NEWSDATA_API_KEY,
    NEWSDATA_BASE_URL,
    NEWSDATA_MAX_RESULTS,
    REGIONS,
    SECTORS,
)

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Helpers ────────────────────────────────────────────────────────────────────

def article_id(url: str) -> str:
    """Generate a deterministic short ID from a URL for deduplication."""
    return hashlib.md5(url.encode()).hexdigest()[:12]


def _make_filename(sector: str, region: str) -> str:
    """Build the JSON filename for a sector + region combo."""
    base = sector.lower().replace(" & ", "_").replace(" ", "_")
    if region.lower() == "india":
        return f"{base}_india.json"
    return f"{base}.json"


def load_existing(sector: str, region: str) -> list[dict]:
    """Load previously saved articles for a sector + region."""
    path = Path(DATA_DIR) / _make_filename(sector, region)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            logger.warning("Corrupt JSON for %s/%s — starting fresh.", sector, region)
    return []


def save_articles(sector: str, region: str, articles: list[dict]) -> None:
    """Persist articles to the sector + region JSON file."""
    path = Path(DATA_DIR) / _make_filename(sector, region)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    logger.info("Saved %d articles for [%s / %s]", len(articles), sector, region)


def _text(element, tag: str) -> str:
    """Safely extract text from an XML element."""
    child = element.find(tag)
    return child.text.strip() if child is not None and child.text else ""


def _clean(text: str) -> str:
    """Strip HTML tags and excessive whitespace from text."""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ══════════════════════════════════════════════════════════════════════════════
# SOURCE 1: GOOGLE NEWS RSS (Free, Unlimited, No API Key)
# ══════════════════════════════════════════════════════════════════════════════

def fetch_google_news_topic(topic: str, google_params: str) -> list[dict]:
    """Fetch articles from Google News topic RSS feed.

    e.g. https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-IN&gl=IN&ceid=IN:en
    """
    url = f"https://news.google.com/rss/headlines/section/topic/{topic}?{google_params}"
    return _parse_google_rss(url, f"GoogleNews/topic/{topic}")


def fetch_google_news_search(query: str, google_params: str) -> list[dict]:
    """Fetch articles from Google News search RSS feed.

    e.g. https://news.google.com/rss/search?q=technology+business&hl=en-IN&gl=IN&ceid=IN:en
    """
    encoded_query = quote_plus(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&{google_params}"
    return _parse_google_rss(url, f"GoogleNews/search/{query}")


def _parse_google_rss(url: str, source_label: str) -> list[dict]:
    """Parse a Google News RSS feed and return normalized articles."""
    try:
        resp = requests.get(
            url,
            timeout=15,
            headers={"User-Agent": "SectorNewsTracker/2.0"},
        )
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")

        articles = []
        for item in items[:10]:
            title = _text(item, "title")
            link = _text(item, "link")
            pub_date = _text(item, "pubDate")

            # Google News titles often end with " - Source Name"
            source = "Google News"
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                title = parts[0].strip()
                source = parts[1].strip()

            # Extract description if available
            desc = _text(item, "description")
            desc = _clean(desc)[:300] if desc else ""

            if not link:
                continue

            articles.append({
                "id": article_id(link),
                "title": _clean(title),
                "source": source,
                "summary": desc,
                "url": link.strip(),
                "image": "",
                "published_at": pub_date or "",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })

        logger.info("Google News RSS [%s]: fetched %d articles", source_label, len(articles))
        return articles

    except requests.exceptions.RequestException as exc:
        logger.warning("Google News RSS failed for %s: %s", source_label, exc)
    except ET.ParseError as exc:
        logger.warning("Google News RSS parse error for %s: %s", source_label, exc)

    return []


# ══════════════════════════════════════════════════════════════════════════════
# SOURCE 2: NEWSDATA.IO API (200 credits/day free tier)
# ══════════════════════════════════════════════════════════════════════════════

def fetch_newsdata(query: str, country: str | None = None) -> list[dict]:
    """Fetch articles from NewsData.io API."""
    if not NEWSDATA_API_KEY:
        return []

    params = {
        "apikey": NEWSDATA_API_KEY,
        "q": query,
        "language": "en",
        "size": NEWSDATA_MAX_RESULTS,
    }
    if country:
        params["country"] = country

    try:
        resp = requests.get(NEWSDATA_BASE_URL, params=params, timeout=15)

        if resp.status_code == 429:
            logger.warning("NewsData.io rate limit hit for '%s'.", query)
            return []
        if resp.status_code == 403:
            logger.error("NewsData.io API key invalid or quota exhausted.")
            return []

        resp.raise_for_status()
        data = resp.json()

        articles = []
        for item in data.get("results", []):
            link = item.get("link", "")
            if not link:
                continue
            articles.append({
                "id": article_id(link),
                "title": (item.get("title") or "").strip(),
                "source": item.get("source_name", item.get("source_id", "Unknown")),
                "summary": (item.get("description") or "").strip()[:300],
                "url": link,
                "image": item.get("image_url", "") or "",
                "published_at": item.get("pubDate", "") or "",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })

        logger.info("NewsData.io [%s]: fetched %d articles", query, len(articles))
        return articles

    except requests.exceptions.RequestException as exc:
        logger.error("NewsData.io request failed for '%s': %s", query, exc)
    except (KeyError, ValueError) as exc:
        logger.error("Error parsing NewsData.io response for '%s': %s", query, exc)

    return []


# ══════════════════════════════════════════════════════════════════════════════
# SOURCE 3: GNEWS API (100 requests/day free tier)
# ══════════════════════════════════════════════════════════════════════════════

def fetch_gnews(query: str, country: str | None = None,
                max_results: int = GNEWS_MAX_RESULTS) -> list[dict]:
    """Fetch articles from GNews API."""
    if not GNEWS_API_KEY:
        return []

    params = {
        "q": query,
        "lang": "en",
        "max": max_results,
        "apikey": GNEWS_API_KEY,
        "sortby": "publishedAt",
    }
    if country:
        params["country"] = country

    url = f"{GNEWS_BASE_URL}?{urlencode(params)}"
    try:
        resp = requests.get(url, timeout=15)

        if resp.status_code == 429:
            logger.warning("GNews rate limit hit for '%s'. Backing off.", query)
            return []
        if resp.status_code == 403:
            logger.error("GNews API key invalid or quota exhausted.")
            return []

        resp.raise_for_status()
        data = resp.json()

        articles = []
        for item in data.get("articles", []):
            articles.append({
                "id": article_id(item["url"]),
                "title": item.get("title", "").strip(),
                "source": item.get("source", {}).get("name", "Unknown"),
                "summary": item.get("description", "").strip(),
                "url": item["url"],
                "image": item.get("image", ""),
                "published_at": item.get("publishedAt", ""),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })

        logger.info("GNews [%s]: fetched %d articles", query, len(articles))
        return articles

    except requests.exceptions.RequestException as exc:
        logger.error("GNews request failed for '%s': %s", query, exc)
    except (KeyError, ValueError) as exc:
        logger.error("Error parsing GNews response for '%s': %s", query, exc)

    return []


# ══════════════════════════════════════════════════════════════════════════════
# SOURCE 4: DIRECT RSS FEEDS (Unlimited)
# ══════════════════════════════════════════════════════════════════════════════

def fetch_rss(feed_url: str) -> list[dict]:
    """Parse a direct RSS feed and return normalized article dicts."""
    try:
        resp = requests.get(
            feed_url,
            timeout=15,
            headers={"User-Agent": "SectorNewsTracker/2.0"},
        )
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        items = root.findall(".//item") or root.findall(
            ".//{http://www.w3.org/2005/Atom}entry"
        )

        articles = []
        for item in items[:10]:
            title = _text(item, "title")
            link = _text(item, "link")
            desc = _text(item, "description")
            pub_date = _text(item, "pubDate")

            if not title:
                title = _text(item, "{http://www.w3.org/2005/Atom}title")
            if not link:
                link_el = item.find("{http://www.w3.org/2005/Atom}link")
                link = link_el.get("href", "") if link_el is not None else ""
            if not desc:
                desc = _text(item, "{http://www.w3.org/2005/Atom}summary")
            if not pub_date:
                pub_date = _text(item, "{http://www.w3.org/2005/Atom}updated")

            if not link:
                continue

            # Extract clean domain name as source
            domain = feed_url.split("/")[2]
            # Prettify common Indian sources
            source_map = {
                "economictimes.indiatimes.com": "Economic Times",
                "www.livemint.com": "LiveMint",
                "www.business-standard.com": "Business Standard",
                "www.moneycontrol.com": "MoneyControl",
                "feeds.feedburner.com": "TechCrunch",
                "www.thehindubusinessline.com": "The Hindu BusinessLine",
                "www.financialexpress.com": "Financial Express",
            }
            source = source_map.get(domain, domain)

            articles.append({
                "id": article_id(link),
                "title": _clean(title),
                "source": source,
                "summary": _clean(desc)[:300],
                "url": link.strip(),
                "image": "",
                "published_at": pub_date or "",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })

        logger.info("RSS [%s]: fetched %d articles", feed_url.split("/")[2], len(articles))
        return articles

    except requests.exceptions.RequestException as exc:
        logger.warning("RSS fetch failed for %s: %s", feed_url, exc)
    except ET.ParseError as exc:
        logger.warning("RSS parse error for %s: %s", feed_url, exc)

    return []


# ══════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def _add_unique(all_articles: list[dict], new_articles: list[dict],
                seen_ids: set) -> None:
    """Add articles to the list if not already seen (in-place)."""
    for art in new_articles:
        if art["id"] not in seen_ids:
            seen_ids.add(art["id"])
            all_articles.append(art)


def fetch_sector(sector: str, sector_config: dict, region: str,
                 region_cfg: dict) -> list[dict]:
    """Fetch all news for a single sector + region from ALL sources."""
    all_articles = []
    seen_ids = set()
    country = region_cfg["country"]
    google_params = region_cfg["google_params"]
    is_india = region.lower() == "india"

    # ── Source 1: Google News RSS (FREE, UNLIMITED) ────────────────────────
    # 1a. Topic feed (if sector has a mapped topic)
    topic = sector_config.get("google_topic")
    if topic:
        articles = fetch_google_news_topic(topic, google_params)
        _add_unique(all_articles, articles, seen_ids)

    # 1b. Search queries
    goog_queries = (
        sector_config.get("google_queries_india", []) if is_india
        else sector_config.get("google_queries", [])
    )
    for query in goog_queries:
        articles = fetch_google_news_search(query, google_params)
        _add_unique(all_articles, articles, seen_ids)
        time.sleep(0.5)

    # ── Source 2: NewsData.io API (200 credits/day) ────────────────────────
    nd_queries = (
        sector_config.get("newsdata_queries_india", []) if is_india
        else sector_config.get("newsdata_queries", [])
    )
    nd_country = region_cfg.get("newsdata_country")
    for query in nd_queries:
        articles = fetch_newsdata(query, country=nd_country)
        _add_unique(all_articles, articles, seen_ids)
        time.sleep(1)

    # ── Source 3: GNews API (100 requests/day) ─────────────────────────────
    gn_queries = (
        sector_config.get("queries_india", []) if is_india
        else sector_config.get("queries", [])
    )
    for query in gn_queries:
        articles = fetch_gnews(query, country=country)
        _add_unique(all_articles, articles, seen_ids)
        time.sleep(1)

    # ── Source 4: Direct RSS Feeds (UNLIMITED) ─────────────────────────────
    feeds = (
        sector_config.get("rss_feeds_india", []) if is_india
        else sector_config.get("rss_feeds", [])
    )
    for feed_url in feeds:
        articles = fetch_rss(feed_url)
        _add_unique(all_articles, articles, seen_ids)

    logger.info(
        "TOTAL for [%s / %s]: %d unique articles from all sources",
        sector, region, len(all_articles),
    )
    return all_articles


def merge_and_trim(existing: list[dict], new: list[dict],
                   max_items: int) -> list[dict]:
    """Merge new articles into existing list, deduplicate, sort by date, trim."""
    seen_ids = set()
    merged = []

    for art in new + existing:
        if art["id"] not in seen_ids:
            seen_ids.add(art["id"])
            merged.append(art)

    def sort_key(a):
        ts = a.get("published_at", "")
        if ts:
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                pass
        return datetime.min.replace(tzinfo=timezone.utc)

    merged.sort(key=sort_key, reverse=True)
    return merged[:max_items]


def run_all():
    """Main entry point: fetch news for every sector x region and save."""
    logger.info("=" * 60)
    logger.info("Starting Sector News Tracker — Multi-Source Fetch")
    logger.info("=" * 60)

    sources_status = []
    sources_status.append(f"Google News RSS: ACTIVE (no key needed)")
    sources_status.append(f"NewsData.io: {'ACTIVE' if NEWSDATA_API_KEY else 'SKIPPED (no key)'}")
    sources_status.append(f"GNews API: {'ACTIVE' if GNEWS_API_KEY else 'SKIPPED (no key)'}")
    sources_status.append(f"Direct RSS feeds: ACTIVE (no key needed)")
    for s in sources_status:
        logger.info("  → %s", s)

    total_new = 0

    for sector, cfg in SECTORS.items():
        for region_name, region_cfg in REGIONS.items():
            logger.info("Processing: %s / %s", sector, region_name)
            existing = load_existing(sector, region_name)
            new_articles = fetch_sector(sector, cfg, region_name, region_cfg)
            merged = merge_and_trim(existing, new_articles, MAX_ARTICLES_PER_SECTOR)
            save_articles(sector, region_name, merged)
            total_new += len(new_articles)

    # Write metadata
    meta_path = Path(DATA_DIR) / "_meta.json"
    meta = {
        "last_fetch": datetime.now(timezone.utc).isoformat(),
        "sectors_updated": list(SECTORS.keys()),
        "regions_updated": list(REGIONS.keys()),
        "total_new_articles": total_new,
        "sources": {
            "google_news_rss": True,
            "newsdata_io": bool(NEWSDATA_API_KEY),
            "gnews": bool(GNEWS_API_KEY),
            "rss_feeds": True,
        },
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    logger.info("Fetch run complete. %d new articles total.", total_new)


if __name__ == "__main__":
    run_all()
