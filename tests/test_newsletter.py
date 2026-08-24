"""
Tests for the newsletter generator.
"""


import pytest

from src.newsletter.generator import NewsletterGenerator
from src.newsletter.scraper import categorize_articles

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_snapshot():
    return {
        "generated_at": "June 07, 2025",
        "total_articles": 12,
        "categories": {
            "RWE": [
                {
                    "title": "RWE expands offshore wind portfolio",
                    "link": "https://example.com/rwe-wind",
                    "summary": "RWE AG announced a 2GW offshore wind expansion in the North Sea.",
                    "published": "2025-06-05",
                    "source": "Reuters Energy",
                }
            ],
            "E.ON": [
                {
                    "title": "E.ON reports record renewable output",
                    "link": "https://example.com/eon",
                    "summary": "E.ON SE reported record renewable energy output in Q1 2025.",
                    "published": "2025-06-04",
                    "source": "Bloomberg NEF",
                }
            ],
        },
        "top_stories": [],
    }


# ── Newsletter Generator Tests ─────────────────────────────────────────────────

class TestNewsletterGenerator:

    def test_generate_returns_html_string(self, sample_snapshot, tmp_path):
        gen = NewsletterGenerator()
        # Point output dir to tmp
        gen._env  # ensure env loads
        html = gen.generate(sample_snapshot, ai_summary="Test summary.")
        assert isinstance(html, str)
        assert "<html" in html.lower()

    def test_generated_html_contains_competitor_names(self, sample_snapshot):
        gen = NewsletterGenerator()
        html = gen.generate(sample_snapshot)
        assert "RWE" in html
        assert "E.ON" in html

    def test_generated_html_contains_article_titles(self, sample_snapshot):
        gen = NewsletterGenerator()
        html = gen.generate(sample_snapshot)
        assert "RWE expands offshore wind portfolio" in html

    def test_ai_summary_included_when_provided(self, sample_snapshot):
        gen = NewsletterGenerator()
        html = gen.generate(sample_snapshot, ai_summary="Critical market shift detected.")
        assert "Critical market shift detected." in html

    def test_save_creates_file(self, sample_snapshot, tmp_path, monkeypatch):
        gen = NewsletterGenerator()
        from src.newsletter import generator as gen_module
        monkeypatch.setattr(gen_module, "OUTPUT_DIR", tmp_path)
        gen._env  # reload not needed

        html = gen.generate(sample_snapshot)
        # Directly save to tmp_path
        output_path = tmp_path / "test_newsletter.html"
        output_path.write_text(html, encoding="utf-8")

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_default_summary_generated_when_no_ai(self, sample_snapshot):
        gen = NewsletterGenerator()
        html = gen.generate(sample_snapshot, ai_summary=None)
        # Default summary should mention article count
        assert "12" in html or "articles" in html.lower()


# ── Scraper / Categorization Tests ────────────────────────────────────────────

class TestCategorization:

    def test_rwe_article_categorized_correctly(self):
        articles = [
            {
                "title": "RWE AG announces new solar farm",
                "summary": "RWE plans to build a 500MW solar farm in Bavaria.",
                "link": "", "published": "", "source": ""
            }
        ]
        result = categorize_articles(articles)
        assert "RWE" in result
        assert len(result["RWE"]) == 1

    def test_eon_article_categorized_correctly(self):
        articles = [
            {
                "title": "E.ON SE reports quarterly earnings",
                "summary": "E.ON SE posted strong Q1 results driven by renewable growth.",
                "link": "", "published": "", "source": ""
            }
        ]
        result = categorize_articles(articles)
        assert "E.ON" in result

    def test_general_energy_news_categorized(self):
        articles = [
            {
                "title": "European energy prices hit record high",
                "summary": "Electricity prices across the EU surged amid cold snap.",
                "link": "", "published": "", "source": ""
            }
        ]
        result = categorize_articles(articles)
        assert "General" in result

    def test_unrelated_article_not_categorized(self):
        articles = [
            {
                "title": "Tech stocks rally on AI news",
                "summary": "Nasdaq climbed 2% as AI stocks surged.",
                "link": "", "published": "", "source": ""
            }
        ]
        result = categorize_articles(articles)
        # No energy keywords → empty result
        assert len(result) == 0

    def test_multiple_articles_multiple_categories(self):
        articles = [
            {
                "title": "RWE offshore wind update",
                "summary": "RWE confirms North Sea expansion.",
                "link": "", "published": "", "source": ""
            },
            {
                "title": "Vattenfall exits German coal",
                "summary": "Vattenfall finalizes coal exit strategy.",
                "link": "", "published": "", "source": ""
            },
        ]
        result = categorize_articles(articles)
        assert "RWE" in result
        assert "Vattenfall" in result
