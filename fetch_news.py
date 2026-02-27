#!/usr/bin/env python3
"""
Sector News Tracker — News Fetcher
Fetches news from GNews API and RSS feeds for both Global and India regions,
deduplicates, and writes to JSON.
Designed to run via GitHub Actions every hour.
"""

import hashlib
import json
import logging
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import requests

from config import (
    DATA_DIR,
    GNEWS_API_KEY,
    GNEWS_BASE_URL,
    GNEWS_MAX_RESULTS,
    MAX_ARTICLES_PER_SECTOR,
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
    """Build the JSON filename for a sector + region combo.

    Global files:  technology.json
    India files:   technology_india.json
    """
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


# ── GNews API Fetcher ──────────────────────────────────────────────────────────

def fetch_gnews(query: str, country: str | None = None,
                max_results: int = GNEWS_MAX_RESULTS) -> list[dict]:
    """Fetch articles from GNews API for a single query string.

    Args:
        query: Search query.
        country: GNews country code (e.g. 'in' for India). None = worldwide.
        max_results: Max articles to return.
    """
    if not GNEWS_API_KEY:
        logger.warning("GNEWS_API_KEY not set — skipping API fetch for '%s'.", query)
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
            logger.warning("GNews rate limit hit for query '%s'. Backing off.", query)
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
        return articles

    except requests.exceptions.Timeout:
        logger.error("Timeout fetching GNews for query '%s'.", query)
    except requests.exceptions.ConnectionError:
        logger.error("Connection error fetching GNews for query '%s'.", query)
    except requests.exceptions.RequestException as exc:
        logger.error("GNews request failed for '%s': %s", query, exc)
    except (KeyError, ValueError) as exc:
        logger.error("Error parsing GNews response for '%s': %s", query, exc)

    return []


# ── RSS Feed Fetcher ───────────────────────────────────────────────────────────

def fetch_rss(feed_url: str) -> list[dict]:
    """Parse an RSS feed and return normalized article dicts."""
    try:
        resp = requests.get(
            feed_url,
            timeout=15,
            headers={"User-Agent": "SectorNewsTracker/1.0"},
        )
        resp.raise_for_status()

        root = ET.fromstring(resp.content)

        # Handle both RSS 2.0 (<channel><item>) and Atom (<entry>) feeds
        items = root.findall(".//item") or root.findall(
            ".//{http://www.w3.org/2005/Atom}entry"
        )

        articles = []
        for item in items[:10]:  # cap at 10 per feed
            # RSS 2.0
            title = _text(item, "title")
            link = _text(item, "link")
            desc = _text(item, "description")
            pub_date = _text(item, "pubDate")

            # Atom fallback
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

            articles.append({
                "id": article_id(link),
                "title": _clean(title),
                "source": feed_url.split("/")[2],  # domain as source name
                "summary": _clean(desc)[:300],
                "url": link.strip(),
                "image": "",
                "published_at": pub_date or "",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })

        return articles

    except requests.exceptions.RequestException as exc:
        logger.warning("RSS fetch failed for %s: %s", feed_url, exc)
    except ET.ParseError as exc:
        logger.warning("RSS parse error for %s: %s", feed_url, exc)

    return []


def _text(element, tag: str) -> str:
    """Safely extract text from an XML element."""
    child = element.find(tag)
    return child.text.strip() if child is not None and child.text else ""


def _clean(text: str) -> str:
    """Strip HTML tags and excessive whitespace from text."""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ── Main Pipeline ──────────────────────────────────────────────────────────────

def fetch_sector(sector: str, sector_config: dict, region: str,
                 country: str | None) -> list[dict]:
    """Fetch all news for a single sector + region from all sources."""
    all_articles = []
    seen_ids = set()

    # 1. Determine which queries to use
    if region.lower() == "india":
        # For India: use India-specific queries only
        queries = sector_config.get("queries_india", [])
    else:
        # For Global: use the standard queries
        queries = sector_config["queries"]

    # 2. GNews API queries
    for query in queries:
        articles = fetch_gnews(query, country=country)
        for art in articles:
            if art["id"] not in seen_ids:
                seen_ids.add(art["id"])
                all_articles.append(art)
        # Small delay to avoid hammering the API
        time.sleep(1)

    # 3. RSS feeds (region-specific)
    if region.lower() == "india":
        feeds = sector_config.get("rss_feeds_india", [])
    else:
        feeds = sector_config.get("rss_feeds", [])

    for feed_url in feeds:
        articles = fetch_rss(feed_url)
        for art in articles:
            if art["id"] not in seen_ids:
                seen_ids.add(art["id"])
                all_articles.append(art)

    logger.info(
        "Fetched %d new unique articles for [%s / %s]",
        len(all_articles), sector, region,
    )
    return all_articles


def merge_and_trim(existing: list[dict], new: list[dict],
                   max_items: int) -> list[dict]:
    """Merge new articles into existing list, deduplicate, sort by date, trim."""
    seen_ids = set()
    merged = []

    # New articles first (they're fresher)
    for art in new + existing:
        if art["id"] not in seen_ids:
            seen_ids.add(art["id"])
            merged.append(art)

    # Sort by published date descending
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
    """Main entry point: fetch news for every sector × region and save."""
    logger.info("=" * 60)
    logger.info("Starting Sector News Tracker fetch run")
    logger.info("=" * 60)

    if not GNEWS_API_KEY:
        logger.warning(
            "GNEWS_API_KEY environment variable is not set. "
            "Only RSS feeds will be used."
        )

    total_new = 0

    for sector, cfg in SECTORS.items():
        for region_name, region_cfg in REGIONS.items():
            logger.info("Processing: %s / %s", sector, region_name)
            existing = load_existing(sector, region_name)
            new_articles = fetch_sector(
                sector, cfg, region_name, region_cfg["country"]
            )
            merged = merge_and_trim(
                existing, new_articles, MAX_ARTICLES_PER_SECTOR
            )
            save_articles(sector, region_name, merged)
            total_new += len(new_articles)

    # Write a metadata file with the last fetch timestamp
    meta_path = Path(DATA_DIR) / "_meta.json"
    meta = {
        "last_fetch": datetime.now(timezone.utc).isoformat(),
        "sectors_updated": list(SECTORS.keys()),
        "regions_updated": list(REGIONS.keys()),
        "total_new_articles": total_new,
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    logger.info("Fetch run complete. %d new articles total.", total_new)


if __name__ == "__main__":
    run_all()
