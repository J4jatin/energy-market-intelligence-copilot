"""
Orchestrator for the Market Intelligence automation pipeline.

Steps:
  1. Scrape RSS feeds → categorize articles
  2. Generate AI executive summary
  3. Render HTML newsletter
  4. Save to disk
  5. Upload to SharePoint
  6. Reload RAG index if new docs added
"""

import logging
from datetime import datetime
from pathlib import Path

from src.newsletter.scraper import get_market_snapshot
from src.newsletter.generator import NewsletterGenerator, generate_ai_summary
from src.newsletter.sharepoint_uploader import SharePointUploader

logger = logging.getLogger(__name__)


class MarketIntelligencePipeline:
    """
    Full automation pipeline: scrape → summarize → generate → publish.

    Example:
        pipeline = MarketIntelligencePipeline()
        result = pipeline.run()
        print(result)
    """

    def __init__(self):
        self.generator = NewsletterGenerator()
        self.uploader = SharePointUploader()

    def run(self, upload_to_sharepoint: bool = True) -> dict:
        """
        Execute the full pipeline.

        Returns:
            Summary dict with status, output_path, sharepoint_url
        """
        start_time = datetime.now()
        logger.info("=" * 50)
        logger.info("🚀 Starting Market Intelligence Pipeline")
        logger.info(f"   Timestamp: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 50)

        result = {
            "status": "started",
            "timestamp": start_time.isoformat(),
            "output_path": None,
            "sharepoint_url": None,
            "articles_processed": 0,
            "errors": [],
        }

        # Step 1: Scrape
        try:
            logger.info("📡 Step 1/4: Scraping energy market news...")
            snapshot = get_market_snapshot()
            result["articles_processed"] = snapshot.get("total_articles", 0)
            logger.info(f"   ✅ Scraped {result['articles_processed']} articles "
                       f"across {len(snapshot.get('categories', {}))} categories")
        except Exception as e:
            error = f"Scraping failed: {e}"
            logger.error(error)
            result["errors"].append(error)
            result["status"] = "failed"
            return result

        # Step 2: AI Summary
        try:
            logger.info("🤖 Step 2/4: Generating AI executive summary...")
            ai_summary = generate_ai_summary(snapshot)
            logger.info("   ✅ AI summary generated")
        except Exception as e:
            logger.warning(f"   ⚠️  AI summary skipped: {e}")
            ai_summary = ""

        # Step 3: Generate HTML
        try:
            logger.info("📰 Step 3/4: Rendering HTML newsletter...")
            filename = f"newsletter_{datetime.now().strftime('%Y_W%V')}.html"
            output_path = self.generator.generate_and_save(snapshot, ai_summary, filename)
            result["output_path"] = str(output_path)
            logger.info(f"   ✅ Saved to: {output_path}")
        except Exception as e:
            error = f"Newsletter generation failed: {e}"
            logger.error(error)
            result["errors"].append(error)
            result["status"] = "failed"
            return result

        # Step 4: Upload to SharePoint
        if upload_to_sharepoint:
            try:
                logger.info("🏢 Step 4/4: Uploading to SharePoint...")
                sharepoint_url = self.uploader.upload(output_path)
                result["sharepoint_url"] = sharepoint_url
                if sharepoint_url:
                    logger.info(f"   ✅ Published: {sharepoint_url}")
                else:
                    logger.info("   ⚠️  SharePoint upload skipped (no credentials)")
            except Exception as e:
                error = f"SharePoint upload failed: {e}"
                logger.warning(error)
                result["errors"].append(error)
        else:
            logger.info("📤 Step 4/4: SharePoint upload skipped (disabled)")

        # Done
        duration = (datetime.now() - start_time).total_seconds()
        result["status"] = "completed"
        result["duration_seconds"] = round(duration, 2)

        logger.info("=" * 50)
        logger.info(f"✅ Pipeline completed in {duration:.1f}s")
        logger.info("=" * 50)

        return result


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    pipeline = MarketIntelligencePipeline()
    result = pipeline.run()
    print("\n📊 Pipeline Result:")
    for k, v in result.items():
        print(f"  {k}: {v}")
