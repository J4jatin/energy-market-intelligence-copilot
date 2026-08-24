"""
Energy market news scraper.
Pulls articles from RSS feeds and summarizes them per competitor.
"""

import logging
from datetime import datetime, timedelta

import feedparser
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Energy sector RSS feeds
RSS_FEEDS = {
    "Reuters Energy": "https://feeds.reuters.com/reuters/businessNews",
    "Bloomberg NEF": "https://about.bnef.com/feed/",
    "Energy Monitor": "https://www.energymonitor.ai/feed/",
    "Recharge News": "https://www.rechargenews.com/rss",
    "PV Magazine": "https://www.pv-magazine.com/feed/",
}

# Keywords to track per competitor
COMPETITOR_KEYWORDS = {
    "E.ON": ["e.on", "eon", "e.on se"],
    "RWE": ["rwe", "rwe ag", "rwe renewables"],
    "Vattenfall": ["vattenfall"],
    "Uniper": ["uniper"],
    "EDF": ["edf", "electricite de france"],
    "Octopus Energy": ["octopus energy"],
    "General": ["energy market", "energiewende", "european energy", "german energy",
                "renewable energy", "offshore wind", "solar power", "electricity prices"],
}


def fetch_rss_articles(
    max_age_days: int = 7,
    max_per_feed: int = 10,
) -> list[dict]:
    """
    Fetch recent articles from all RSS feeds.

    Returns:
        List of article dicts: {title, link, summary, published, source}
    """
    articles = []
    cutoff = datetime.now() - timedelta(days=max_age_days)

    for source_name, feed_url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
            count = 0
            for entry in feed.entries:
                if count >= max_per_feed:
                    break

                # Parse published date
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])
                    if published < cutoff:
                        continue

                articles.append({
                    "title": entry.get("title", "No title"),
                    "link": entry.get("link", ""),
                    "summary": _clean_html(entry.get("summary", "")),
                    "published": published.strftime("%Y-%m-%d") if published else "Unknown",
                    "source": source_name,
                })
                count += 1

            logger.info(f"Fetched {count} articles from {source_name}")

        except Exception as e:
            logger.warning(f"Failed to fetch {source_name}: {e}")

    logger.info(f"Total articles fetched: {len(articles)}")
    return articles


def categorize_articles(articles: list[dict]) -> dict[str, list[dict]]:
    """
    Categorize articles by competitor/topic using keyword matching.

    Returns:
        Dict mapping category name → list of articles
    """
    categorized = {key: [] for key in COMPETITOR_KEYWORDS}

    for article in articles:
        text = (article["title"] + " " + article["summary"]).lower()
        matched = False

        for category, keywords in COMPETITOR_KEYWORDS.items():
            if category == "General":
                continue
            if any(kw in text for kw in keywords):
                categorized[category].append(article)
                matched = True
                break

        if not matched:
            # Check if it's general energy news
            if any(kw in text for kw in COMPETITOR_KEYWORDS["General"]):
                categorized["General"].append(article)

    # Remove empty categories
    return {k: v for k, v in categorized.items() if v}


def get_market_snapshot() -> dict:
    """
    Build a complete market snapshot for newsletter generation.

    Returns:
        Dict with categorized articles + metadata
    """
    articles = fetch_rss_articles()
    categorized = categorize_articles(articles)

    return {
        "generated_at": datetime.now().strftime("%B %d, %Y"),
        "total_articles": len(articles),
        "categories": categorized,
        "top_stories": articles[:5],  # Top 5 across all sources
    }


def _clean_html(text: str) -> str:
    """Strip HTML tags from text."""
    try:
        return BeautifulSoup(text, "html.parser").get_text(separator=" ").strip()
    except Exception:
        return text
