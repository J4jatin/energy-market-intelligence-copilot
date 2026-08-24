"""
Pull real, live energy-market articles via the existing RSS scraper and save
them as .txt documents the RAG pipeline can ingest.

This turns the knowledge base from illustrative sample docs into real,
up-to-date news — without touching the RAG engine itself.

Run:
    python scripts/fetch_real_articles.py

Then rebuild the index so it includes both the original sample docs and
these new real articles:
    python -m src.chatbot.data_ingestion --dir data
"""

import logging
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.newsletter.scraper import fetch_rss_articles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REAL_DOCS_DIR = Path(__file__).parent.parent / "data" / "real_docs"


def _slugify(text: str, max_len: int = 60) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    return slug[:max_len] or "article"


def main():
    REAL_DOCS_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Fetching live articles from RSS feeds...")
    articles = fetch_rss_articles(max_age_days=14, max_per_feed=15)

    if not articles:
        logger.warning(
            "No articles fetched. Some RSS feeds may be down or blocked. "
            "The sample_docs corpus is still there, so the app keeps working."
        )
        return

    saved = 0
    for i, art in enumerate(articles, 1):
        if not art.get("summary") or len(art["summary"]) < 80:
            continue  # skip near-empty entries, not useful for retrieval

        filename = f"{i:03d}_{_slugify(art['title'])}.txt"
        content = (
            f"Title: {art['title']}\n"
            f"Source: {art['source']}\n"
            f"Published: {art['published']}\n"
            f"Link: {art['link']}\n\n"
            f"{art['summary']}\n"
        )
        (REAL_DOCS_DIR / filename).write_text(content, encoding="utf-8")
        saved += 1

    logger.info(f"✅ Saved {saved} real articles to {REAL_DOCS_DIR}")
    logger.info(
        "Next: rebuild the index with both sample + real docs:\n"
        "    python -m src.chatbot.data_ingestion --dir data"
    )


if __name__ == "__main__":
    main()
