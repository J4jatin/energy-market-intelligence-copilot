"""
HTML Newsletter Generator for Energy Market Intelligence.

Renders the Jinja2 template with scraped market data + AI summary.
Supports saving to file and uploading to SharePoint.
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "newsletters"


class NewsletterGenerator:
    """
    Generates polished HTML competitive intelligence newsletters.

    Example:
        gen = NewsletterGenerator()
        html = gen.generate(snapshot)
        gen.save(html, "newsletter_2025_W24.html")
    """

    def __init__(self):
        self._env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=True,
        )
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        snapshot: Dict,
        ai_summary: Optional[str] = None,
    ) -> str:
        """
        Render newsletter HTML from a market snapshot.

        Args:
            snapshot: Output from scraper.get_market_snapshot()
            ai_summary: Optional AI-generated executive summary

        Returns:
            Rendered HTML string
        """
        now = datetime.now()
        template = self._env.get_template("newsletter.html")

        context = {
            "generated_at": snapshot.get("generated_at", now.strftime("%B %d, %Y")),
            "total_articles": snapshot.get("total_articles", 0),
            "categories": snapshot.get("categories", {}),
            "top_stories": snapshot.get("top_stories", []),
            "week_number": now.strftime("%V"),
            "year": now.year,
            "ai_summary": ai_summary or self._default_summary(snapshot),
        }

        html = template.render(**context)
        logger.info("Newsletter HTML rendered successfully")
        return html

    def save(self, html: str, filename: Optional[str] = None) -> Path:
        """Save newsletter HTML to disk."""
        if not filename:
            filename = f"newsletter_{datetime.now().strftime('%Y_W%V')}.html"

        output_path = OUTPUT_DIR / filename
        output_path.write_text(html, encoding="utf-8")
        logger.info(f"Newsletter saved: {output_path}")
        return output_path

    def generate_and_save(
        self,
        snapshot: Dict,
        ai_summary: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> Path:
        """Generate and save in one call."""
        html = self.generate(snapshot, ai_summary)
        return self.save(html, filename)

    def _default_summary(self, snapshot: Dict) -> str:
        """Fallback summary when no AI summary is provided."""
        categories = list(snapshot.get("categories", {}).keys())
        total = snapshot.get("total_articles", 0)
        cat_str = ", ".join(categories[:4]) if categories else "various competitors"
        return (
            f"This week's automated market intelligence digest analyzed {total} articles "
            f"across the European energy sector. Key activity detected from: {cat_str}. "
            f"Review the sections below for detailed competitor insights."
        )


def generate_ai_summary(snapshot: Dict) -> str:
    """
    Use OpenAI to generate an executive summary of the market snapshot.
    Falls back to default summary if API key not set.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("No OPENAI_API_KEY — using default summary")
        return ""

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        # Build a compact text representation
        stories = []
        for cat, articles in list(snapshot.get("categories", {}).items())[:5]:
            for article in articles[:2]:
                stories.append(f"[{cat}] {article['title']}: {article['summary'][:150]}")

        prompt = (
            "You are a senior energy market analyst. Based on these recent headlines, "
            "write a concise 3-sentence executive summary of the most important market "
            "developments this week:\n\n" + "\n".join(stories)
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.warning(f"AI summary generation failed: {e}")
        return ""
